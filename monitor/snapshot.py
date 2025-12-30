from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DaySnapshot:
    sleep_start: Optional[str] = field(default=None, metadata={"sheet": "start [ts]"})
    sleep_end: Optional[str] = field(default=None, metadata={"sheet": "end [ts]"})
    sleep_asleep: Optional[str] = field(default=None, metadata={"sheet": "asleep [h]"})
    sleep_in_bed: Optional[str] = field(default=None, metadata={"sheet": "in_bed [h]"})
    sleep_efficiency: Optional[float] = field(default=None, metadata={"sheet": "effic. [%]"})
    sleep_deep: Optional[str] = field(default=None, metadata={"sheet": "deep [h]"})
    sleep_light: Optional[str] = field(default=None, metadata={"sheet": "light [h]"})
    sleep_rem: Optional[str] = field(default=None, metadata={"sheet": "rem [h]"})
    sleep_wake: Optional[str] = field(default=None, metadata={"sheet": "wake [h]"})

    hrv: Optional[int] = field(default=None, metadata={"sheet": "hrv [ms]"})
    rhr: Optional[int] = field(default=None, metadata={"sheet": "rhr [bpm]"})
    steps: Optional[int] = field(default=None, metadata={"sheet": "steps [1]", "date_offset": -1})

    kcal: Optional[int] = field(default=None, metadata={"sheet": "cal. [kcal]", "date_offset": -1})
    protein: Optional[int] = field(default=None, metadata={"sheet": "prot. [g]", "date_offset": -1})
    fats: Optional[int] = field(default=None, metadata={"sheet": "fats [g]", "date_offset": -1})
    carbs: Optional[int] = field(default=None, metadata={"sheet": "carb. [g]", "date_offset": -1})