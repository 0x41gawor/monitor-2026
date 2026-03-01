from dataclasses import fields
from datetime import datetime, timedelta
from monitor.snapshot import DaySnapshot
from infra.fitbit.client import FitbitClient
from infra.sheets.client import SheetsClient
from infra.dietonez.client import DietonezClient
from monitor.util import iso_to_hhmm, minutes_to_hhmm
from monitor.colorer import Colorer


class Monitor:
    def __init__(
        self,
        fitbit: FitbitClient,
        sheets: SheetsClient,
        dietonez: DietonezClient,
        colorer: Colorer,
    ):
        self.fitbit = fitbit
        self.sheets = sheets
        self.dietonez = dietonez
        self.colorer = colorer

    def build_snapshot(self, date: str) -> DaySnapshot:
        d = datetime.fromisoformat(date)

        previous_date = (d - timedelta(days=1)).date().isoformat()

        sleep_raw = self.fitbit.sleep(date)
        
        main = next((s for s in sleep_raw["sleep"] if s.get("isMainSleep")), None)

        dietonez_raw = self.dietonez.menu_summary(previous_date)

        summary = sleep_raw.get("summary", {})
        stages = summary.get("stages") or {}

        return DaySnapshot(
            sleep_start=iso_to_hhmm(main["startTime"]) if main else None,
            sleep_end=iso_to_hhmm(main["endTime"]) if main else None,
            sleep_asleep=minutes_to_hhmm(summary.get("totalMinutesAsleep")) if summary.get("totalMinutesAsleep") else None,
            sleep_in_bed=minutes_to_hhmm(summary.get("totalTimeInBed")) if summary.get("totalTimeInBed") else None,
            sleep_efficiency=main["efficiency"] if main else None,
            sleep_deep=minutes_to_hhmm(stages.get("deep")) if stages.get("deep") else None,
            sleep_light=minutes_to_hhmm(stages.get("light")) if stages.get("light") else None,
            sleep_rem=minutes_to_hhmm(stages.get("rem")) if stages.get("rem") else None,
            sleep_wake=minutes_to_hhmm(stages.get("wake")) if stages.get("wake") else None,
            hrv=self.fitbit.hrv(date),
            rhr=self.fitbit.rhr(date),
            steps=self.fitbit.steps(previous_date),
            kcal=int(dietonez_raw["kcal"]),
            proteins=int(dietonez_raw["proteins"]),
            fats=int(dietonez_raw["fats"]),
            carbs=int(dietonez_raw["carbs"]),
        )

    def insert_day(self, date: str):
        snapshot = self.build_snapshot(date)
        base_date = datetime.fromisoformat(date)

        for f in fields(snapshot):
            value = getattr(snapshot, f.name)
            if value is None:
                continue

            offset = f.metadata.get("date_offset", 0)
            target_date = (base_date + timedelta(days=offset)).date().isoformat()

            self.sheets.insert_cell(
                target_date,
                f.metadata["sheet"],
                value,
            )

            color = self.colorer.get_color(f.metadata["sheet"], value)
            if color is not None:
                self.sheets.color_cell(
                    target_date,
                    f.metadata["sheet"],
                    color,
                )


    def insert_week_if_needed(self, date: str):
        if self.sheets.is_sunday(date):
            self.sheets.insert_week_template()