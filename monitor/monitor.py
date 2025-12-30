from dataclasses import fields
from datetime import datetime, timedelta
from monitor.snapshot import DaySnapshot
from infra.fitbit.client import FitbitClient
from infra.sheets.client import SheetsClient
from monitor.util import iso_to_hhmm, minutes_to_hhmm


class Monitor:
    def __init__(
        self,
        fitbit: FitbitClient,
        sheets: SheetsClient,
    ):
        self.fitbit = fitbit
        self.sheets = sheets

    def build_snapshot(self, date: str) -> DaySnapshot:
        d = datetime.fromisoformat(date)

        previous_date = (d - timedelta(days=1)).date().isoformat()

        sleep_raw = self.fitbit.sleep(date)
        main = next(s for s in sleep_raw["sleep"] if s.get("isMainSleep"))

        return DaySnapshot(
            sleep_start=iso_to_hhmm(main["startTime"]),
            sleep_end=iso_to_hhmm(main["endTime"]),
            sleep_asleep=minutes_to_hhmm(sleep_raw["summary"]["totalMinutesAsleep"]),
            sleep_in_bed=minutes_to_hhmm(sleep_raw["summary"]["totalTimeInBed"]),
            sleep_efficiency=main["efficiency"],
            sleep_deep=minutes_to_hhmm(sleep_raw["summary"]["stages"]["deep"]),
            sleep_light=minutes_to_hhmm(sleep_raw["summary"]["stages"]["light"]),
            sleep_rem=minutes_to_hhmm(sleep_raw["summary"]["stages"]["rem"]),
            sleep_wake=minutes_to_hhmm(sleep_raw["summary"]["stages"]["wake"]),
            hrv=self.fitbit.hrv(date),
            rhr=self.fitbit.rhr(date),
            steps=self.fitbit.steps(previous_date),
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


    def insert_week_if_needed(self, date: str):
        if self.sheets.is_sunday(date):
            self.sheets.insert_week_template()