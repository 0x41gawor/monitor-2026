import os

from dataclasses import dataclass

@dataclass(frozen=True)
class ColorPalette:
    ok: str
    warn: str
    bad: str


class Colorer:
    def __init__(
        self,
        *,
        strong_palette: ColorPalette,
        soft_palette: ColorPalette,
    ):
        self.palettes = {
            "strong": strong_palette,
            "soft": soft_palette,
        }

        self.targets = {
            "sleep_start": os.environ["TARGET_SLEEP_START"],
            "sleep_end": os.environ["TARGET_SLEEP_END"],
            "asleep": os.environ["TARGET_ASLEEP_TIME"],
            "in_bed": os.environ["TARGET_IN_BED_TIME"],
        }

        self._dispatch = {
            "start [ts]": self._color_sleep_time_start,
            "end [ts]": self._color_sleep_time_end,
            "asleep [h]": self._color_sleep_time_asleep,
            "in_bed [h]": self._color_sleep_time_in_bed,
        }

    # ============================================================
    # Helpers
    # ============================================================
    # Colors
    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        return (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16),
        )

    def _rgb_to_hex(self, r: int, g: int, b: int) -> str:
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _interpolate(self, c1: str, c2: str, t: float) -> str:
        r1, g1, b1 = self._hex_to_rgb(c1)
        r2, g2, b2 = self._hex_to_rgb(c2)

        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)

        return self._rgb_to_hex(r, g, b)
    # Hours -> Numerics
    def _hhmm_to_hours(self, value: str) -> float:
        h, m = value.split(":")
        return int(h) + int(m) / 60
    
    # Midnight handle
    def _sleep_start_offset(self, value: str, target: str) -> float:
        v = self._hhmm_to_hours(value)
        t = self._hhmm_to_hours(target)

        # wszystko < 12 traktujemy jako po północy
        if v < 12:
            v += 24

        return v - (t + 24)
    
    # Normal distribution
    def _normal_dist(self, value: float, mean: float, var: float) -> float:
        """
        Returns normalized deviation in range [0, 1]
        """
        sigma = var ** 0.5
        z = abs(value - mean) / sigma

        # 0..1σ → 0..0.5
        # 1..2σ → 0.5..1
        if z <= 1:
            return 0.5 * z
        elif z <= 2:
            return 0.5 + 0.5 * (z - 1)
        else:
            return 1.0
        
    # Color distributor
    def _color_dist(self, severity: float, palette: ColorPalette) -> str:
        if severity <= 0.5:
            return self._interpolate(palette.ok, palette.warn, severity / 0.5)
        else:
            return self._interpolate(palette.warn, palette.bad, (severity - 0.5) / 0.5)




    def _color_sleep_time_start(self, value: str) -> str:
        offset = self._sleep_start_offset(value, self.targets["sleep_start"])

        severity = self._normal_dist(
            value=offset,
            mean=0,
            var=1.0,   # ← np. tolerancja ±1h
        )

        return self._color_dist(severity, self.palettes["soft"])

    def _color_sleep_time_end(self, value: str) -> str:
        hours = self._hhmm_to_hours(value)
        target = self._hhmm_to_hours(self.targets["sleep_end"])

        severity = self._normal_dist(
            value=hours,
            mean=target,
            var=0.25,   # np. tolerancja ~15min
        )

        return self._color_dist(severity, self.palettes["soft"])

    def _color_sleep_time_asleep(self, value: str) -> str:
        hours = self._hhmm_to_hours(value)
        target = self._hhmm_to_hours(self.targets["asleep"])

        severity = self._normal_dist(
            value=hours,
            mean=target,
            var=0.5,   # np. tolerancja ~1h
        )

        return self._color_dist(severity, self.palettes["strong"])

    def _color_sleep_time_in_bed(self, value: str) -> str:
        hours = self._hhmm_to_hours(value)
        target = self._hhmm_to_hours(self.targets["in_bed"])

        severity = self._normal_dist(
            value=hours,
            mean=target,
            var=0.5,   # np. tolerancja ~1h
        )

        return self._color_dist(severity, self.palettes["soft"])


    # ============================================================
    # Public API
    # ============================================================
    def get_color(self, header: str, value) -> str | None:
        if value is None:
            return None

        fn = self._dispatch.get(header)
        if not fn:
            return None

        return fn(value)