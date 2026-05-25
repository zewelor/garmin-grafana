from __future__ import annotations

import os
import time

import requests


BASE_URL = f"http://{os.environ['INFLUXDB_HOST']}:{os.environ['INFLUXDB_PORT']}"
ACTIVITY_ID = "123"
OTHER_ACTIVITY_ID = "999"
POINT_TIME = "2024-01-01T00:00:00+00:00"
POINT_TIME_NS = "1704067200000000000"
REFRESHED_POINT_TIME = "2024-01-01T00:05:00+00:00"


def exec_sql(query: str) -> dict:
    response = requests.get(f"{BASE_URL}/exec", params={"query": query}, timeout=15)
    if response.status_code != 200:
        raise AssertionError(f"SQL failed ({response.status_code}): {response.text}")
    return response.json() if response.text else {}


def write_ilp(line: str) -> None:
    response = requests.post(f"{BASE_URL}/write", data=line, timeout=15)
    if response.status_code != 204:
        raise AssertionError(f"ILP write failed ({response.status_code}): {response.text}")


def wait_for_dataset(query: str, predicate, timeout: float = 10.0) -> list:
    deadline = time.monotonic() + timeout
    last_dataset = []
    while time.monotonic() < deadline:
        result = exec_sql(query)
        last_dataset = result.get("dataset") or []
        if predicate(last_dataset):
            return last_dataset
        time.sleep(0.2)
    raise AssertionError(f"Timed out waiting for query {query!r}; last dataset: {last_dataset!r}")


def seed_old_rows() -> None:
    write_ilp(
        "StrengthExerciseSet,"
        "ActivityID=123,ActivitySelector=sel,Device=dev,Database_Name=GarminStats,"
        "ExerciseCategory=OLD,ExerciseLabel=OLD_LABEL "
        'Activity_ID=123i,ActivityName="Strength",SetOrder=1i,SetType="ACTIVE",'
        f"Reps=10i,Weight_kg=20.0,Duration_s=30.0 {POINT_TIME_NS}"
    )
    write_ilp(
        "StrengthExerciseSet,"
        "ActivityID=123,ActivitySelector=sel,Device=dev,Database_Name=GarminStats,"
        "ExerciseCategory=STALE,ExerciseLabel=REMOVED_LABEL "
        'Activity_ID=123i,ActivityName="Strength",SetOrder=2i,SetType="ACTIVE",'
        f"Reps=8i,Weight_kg=15.0,Duration_s=25.0 {POINT_TIME_NS}"
    )
    write_ilp(
        "StrengthExerciseSet,"
        "ActivityID=999,ActivitySelector=other,Device=dev,Database_Name=GarminStats,"
        "ExerciseCategory=KEEP,ExerciseLabel=KEEP_LABEL "
        'Activity_ID=999i,ActivityName="Strength",SetOrder=1i,SetType="ACTIVE",'
        f"Reps=5i,Weight_kg=5.0,Duration_s=15.0 {POINT_TIME_NS}"
    )
    wait_for_dataset(
        "SELECT ActivityID, ExerciseLabel FROM StrengthExerciseSet",
        lambda rows: len(rows) == 3,
    )


def assert_final_rows() -> None:
    rows = wait_for_dataset(
        "SELECT ActivityID, ExerciseLabel, SetOrder, Reps, Weight_kg "
        "FROM StrengthExerciseSet ORDER BY ActivityID",
        lambda dataset: dataset == [
            [ACTIVITY_ID, "NEW_LABEL", 1, 12, 22.0],
            [OTHER_ACTIVITY_ID, "KEEP_LABEL", 1, 5, 5.0],
        ],
    )
    assert rows == [
        [ACTIVITY_ID, "NEW_LABEL", 1, 12, 22.0],
        [OTHER_ACTIVITY_ID, "KEEP_LABEL", 1, 5, 5.0],
    ]


def main() -> None:
    exec_sql("DROP TABLE IF EXISTS StrengthExerciseSet")
    seed_old_rows()

    from garmin_grafana import garmin_fetch

    assert garmin_fetch.purge_existing_strength_exercise_sets(ACTIVITY_ID)
    garmin_fetch.write_points_to_influxdb([
        {
            "measurement": "StrengthExerciseSet",
            "time": REFRESHED_POINT_TIME,
            "tags": {
                "Device": "dev",
                "Database_Name": "GarminStats",
                "ActivityID": ACTIVITY_ID,
                "ActivitySelector": "sel",
                "ExerciseCategory": "NEW",
                "ExerciseLabel": "NEW_LABEL",
            },
            "fields": {
                "Activity_ID": int(ACTIVITY_ID),
                "ActivityName": "Strength",
                "SetOrder": 1,
                "SetType": "ACTIVE",
                "Reps": 12,
                "Weight_kg": 22.0,
                "Duration_s": 35.0,
            },
        }
    ])

    assert_final_rows()
    print("QuestDB StrengthExerciseSet dedup cleanup test passed")


if __name__ == "__main__":
    main()
