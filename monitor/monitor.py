from monitor.snapshot import DaySnapshot
from infra.fitbit.client import FitbitClient
from infra.sheets.client import SheetsClient
from util import iso_to_hhmm, minutes_to_hhmm


class Monitor:
    def __init__(
        self,
        fitbit: FitbitClient,
        sheets: SheetsClient,
    ):
        self.fitbit = fitbit
        self.sheets = sheets

    def build_snapshot(self, date: str) -> DaySnapshot:
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
            steps=self.fitbit.steps(date),
        )

    def insert_day(self, date: str):
        snapshot = self.build_snapshot(date)
        self.sheets.insert_day(date, snapshot)

    def insert_week_if_needed(self, date: str):
        if self.sheets.is_sunday(date):
            self.sheets.insert_week_template()