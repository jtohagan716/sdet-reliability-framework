import sqlite3
from pathlib import Path


class ReliabilityDataStore:

    def __init__(self, db_path="reports/reliability_data.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        return sqlite3.connect(self.db_path)

    def initialize(self):
        with self.connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS synthetic_transaction_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    journey_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duration_ms REAL NOT NULL,
                    signal TEXT NOT NULL,
                    health TEXT NOT NULL,
                    decision TEXT NOT NULL
                )
                """
            )

            connection.commit()

    def save_synthetic_result(
        self,
        timestamp: str,
        journey_name: str,
        status: str,
        duration_ms: float,
        signal: str,
        health: str,
        decision: str,
    ):
        with self.connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO synthetic_transaction_results (
                    timestamp,
                    journey_name,
                    status,
                    duration_ms,
                    signal,
                    health,
                    decision
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    journey_name,
                    status,
                    duration_ms,
                    signal,
                    health,
                    decision,
                ),
            )

            connection.commit()

    def fetch_all_synthetic_results(self):
        with self.connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    timestamp,
                    journey_name,
                    status,
                    duration_ms,
                    signal,
                    health,
                    decision
                FROM synthetic_transaction_results
                ORDER BY id
                """
            )

            rows = cursor.fetchall()

        results = []

        for row in rows:
            results.append(
                {
                    "timestamp": row[0],
                    "journey_name": row[1],
                    "status": row[2],
                    "duration_ms": row[3],
                    "signal": row[4],
                    "health": row[5],
                    "decision": row[6],
                }
            )

        return results

    def fetch_results_by_journey(self, journey_name: str):
        with self.connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    timestamp,
                    journey_name,
                    status,
                    duration_ms,
                    signal,
                    health,
                    decision
                FROM synthetic_transaction_results
                WHERE journey_name = ?
                ORDER BY id
                """,
                (journey_name,),
            )

            rows = cursor.fetchall()

        results = []

        for row in rows:
            results.append(
                {
                    "timestamp": row[0],
                    "journey_name": row[1],
                    "status": row[2],
                    "duration_ms": row[3],
                    "signal": row[4],
                    "health": row[5],
                    "decision": row[6],
                }
            )

        return results