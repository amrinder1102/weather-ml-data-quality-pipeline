import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional
import os
from src.logging_config import get_logger

logger = get_logger(__name__)


class WeatherDB:
    def __init__(self, host="localhost", database="weather_pipeline", user="postgres", password=""):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.conn = None

    def connect(self, max_retries=3):
        """Connect to database with retry logic."""
        for attempt in range(max_retries):
            try:
                self.conn = psycopg2.connect(
                    host=self.host,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    connect_timeout=5
                )
                logger.info(f"✓ Connected to PostgreSQL: {self.database}")
                return
            except psycopg2.Error as e:
                logger.warning(f"Connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error("All connection attempts failed")
                    raise
                continue

    def disconnect(self):
        """Close database connection."""
        try:
            if self.conn:
                self.conn.close()
                logger.info("✓ Disconnected from database")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")

    def insert_raw_weather(self, weather_data: List[Dict]) -> List[int]:
        """Insert raw weather records and return their IDs."""
        if not weather_data:
            logger.warning("No weather data to insert")
            return []

        try:
            cursor = self.conn.cursor()
            ids = []

            for record in weather_data:
                cursor.execute(
                    """
                    INSERT INTO raw_weather
                    (timestamp, date, time, city, country, temp_current, temp_max, temp_min,
                     feels_like, humidity, pressure, wind_speed, clouds, weather_condition, weather_description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        record["timestamp"],
                        record["date"],
                        record["time"],
                        record["city"],
                        record.get("country"),
                        record.get("temp_current"),
                        record.get("temp_max"),
                        record.get("temp_min"),
                        record.get("feels_like"),
                        record.get("humidity"),
                        record.get("pressure"),
                        record.get("wind_speed"),
                        record.get("clouds"),
                        record.get("weather_condition"),
                        record.get("weather_description"),
                    ),
                )
                ids.append(cursor.fetchone()[0])

            self.conn.commit()
            logger.info(f"✓ Inserted {len(ids)} raw weather records")
            return ids

        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Error inserting raw weather: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error inserting weather data: {e}")
            raise

    def insert_processed_weather(self, processed_data: List[Dict], raw_ids: List[int]) -> None:
        """Insert processed/validated weather records."""
        if not processed_data:
            logger.warning("No processed data to insert")
            return

        try:
            cursor = self.conn.cursor()
            timestamp = datetime.now(timezone.utc).isoformat()

            for idx, record in enumerate(processed_data):
                cursor.execute(
                    """
                    INSERT INTO processed_weather
                    (raw_weather_id, timestamp, date, city, temp_max, temp_min, humidity, pressure, wind_speed)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        raw_ids[idx] if idx < len(raw_ids) else None,
                        timestamp,
                        record["date"],
                        record["city"],
                        record.get("temp_max"),
                        record.get("temp_min"),
                        record.get("humidity"),
                        record.get("pressure"),
                        record.get("wind_speed"),
                    ),
                )

            self.conn.commit()
            logger.info(f"✓ Inserted {len(processed_data)} processed weather records")

        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Error inserting processed weather: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def save_quality_report(self, report: Dict) -> None:
        """Save validation quality report."""
        try:
            cursor = self.conn.cursor()
            run_id = report.get("timestamp", datetime.now(timezone.utc).isoformat())

            cursor.execute(
                """
                INSERT INTO quality_reports
                (run_id, timestamp, quality_score, status, total_records, processed_records, checks)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    run_id,
                    report["timestamp"],
                    report["quality_score"],
                    report["status"],
                    report.get("records", 0),
                    report.get("processed_records"),
                    json.dumps(report.get("checks", {})),
                ),
            )

            self.conn.commit()
            logger.info(f"✓ Quality report saved (score: {report['quality_score']}%)")

        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Error saving quality report: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving report: {e}")
            raise

    def get_latest_report(self) -> Optional[Dict]:
        """Fetch the most recent quality report."""
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT * FROM quality_reports ORDER BY timestamp DESC LIMIT 1"
            )
            return cursor.fetchone()
        except psycopg2.Error as e:
            print(f"✗ Error fetching latest report: {e}")
            return None

    def get_reports_by_date_range(self, start_date, end_date) -> List[Dict]:
        """Fetch quality reports within a date range."""
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT * FROM quality_reports WHERE DATE(timestamp) BETWEEN %s AND %s ORDER BY timestamp DESC",
                (start_date, end_date),
            )
            return cursor.fetchall()
        except psycopg2.Error as e:
            print(f"✗ Error fetching reports: {e}")
            return []
