"""
Data Quality Tests for Weather Pipeline

These tests verify that ingested and processed weather data meets quality standards.
This is a critical part of MLOps - you can't trust ML models built on bad data.

Test Categories:
1. COMPLETENESS - Are all required fields present?
2. ACCURACY - Are values in valid/reasonable ranges?
3. CONSISTENCY - Do values follow business rules?
4. FRESHNESS - Is data timely?
5. UNIQUENESS - Are there unexpected duplicates?
"""

import pytest
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List
import os


class DatabaseConnection:
    """Helper class to connect to PostgreSQL"""

    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "weather_pipeline"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres_pwd"),
            port=os.getenv("DB_PORT", "5432")
        )
        self.cursor = self.conn.cursor()

    def query(self, sql: str) -> List[tuple]:
        """Execute query and return results"""
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()
        self.conn.close()


@pytest.fixture
def db():
    """Database fixture - connects before test, closes after"""
    database = DatabaseConnection()
    yield database
    database.close()


# ============================================================================
# TEST CATEGORY 1: COMPLETENESS
# ============================================================================
# Check that all required fields are present (not NULL where they shouldn't be)

class TestCompleteness:
    """Tests that required fields are not missing"""

    def test_raw_weather_has_required_fields(self, db):
        """
        WHAT: Verify all required fields exist in raw_weather table
        WHY: Missing data breaks downstream processing
        EXAMPLE: If 'city' is NULL, we can't identify the location
        """
        sql = """
        SELECT COUNT(*)
        FROM raw_weather
        WHERE city IS NULL
           OR timestamp IS NULL
           OR date IS NULL
        """
        result = db.query(sql)[0][0]
        assert result == 0, f"Found {result} records with missing required fields"

    def test_processed_weather_has_temperature(self, db):
        """
        WHAT: Verify processed weather has temperature data
        WHY: Temperature is the main metric we care about
        """
        sql = """
        SELECT COUNT(*)
        FROM processed_weather
        WHERE temp_max IS NULL OR temp_min IS NULL
        """
        result = db.query(sql)[0][0]
        assert result == 0, f"Found {result} records without temperature"

    def test_no_empty_cities(self, db):
        """
        WHAT: City names should not be empty strings
        WHY: Empty strings are as bad as NULL in practice
        """
        sql = """
        SELECT COUNT(*)
        FROM raw_weather
        WHERE city = '' OR city IS NULL
        """
        result = db.query(sql)[0][0]
        assert result == 0, "Found records with empty city names"


# ============================================================================
# TEST CATEGORY 2: ACCURACY
# ============================================================================
# Check that values are in valid/reasonable ranges

class TestAccuracy:
    """Tests that data values are within valid ranges"""

    def test_temperature_in_reasonable_range(self, db):
        """
        WHAT: Temperature should be between -50°C and 60°C
        WHY: Anything outside this is likely an error or extreme weather
        BUSINESS RULE: Our app operates in areas where this holds true
        """
        sql = """
        SELECT COUNT(*)
        FROM processed_weather
        WHERE temp_current < -50 OR temp_current > 60
        """
        result = db.query(sql)[0][0]
        assert result == 0, f"Found {result} records with invalid temperatures"

    def test_humidity_between_0_and_100(self, db):
        """
        WHAT: Humidity is always 0-100%
        WHY: Physical constraint - can't have negative or >100% humidity
        """
        sql = """
        SELECT COUNT(*)
        FROM processed_weather
        WHERE humidity < 0 OR humidity > 100
        """
        result = db.query(sql)[0][0]
        assert result == 0, f"Found {result} records with invalid humidity"

    def test_wind_speed_non_negative(self, db):
        """
        WHAT: Wind speed can't be negative
        WHY: Negative wind speed is physically impossible
        """
        sql = """
        SELECT COUNT(*)
        FROM processed_weather
        WHERE wind_speed < 0
        """
        result = db.query(sql)[0][0]
        assert result == 0, f"Found {result} records with negative wind speed"

    def test_pressure_in_valid_range(self, db):
        """
        WHAT: Atmospheric pressure 900-1050 hPa (normal is 1013)
        WHY: Extreme pressures indicate data error or extreme weather
        """
        sql = """
        SELECT COUNT(*)
        FROM processed_weather
        WHERE pressure < 900 OR pressure > 1050
        """
        result = db.query(sql)[0][0]
        assert result == 0, f"Found {result} records with invalid pressure"

    def test_temp_max_greater_than_min(self, db):
        """
        WHAT: Max temp should always be >= min temp
        WHY: Basic logic check
        """
        sql = """
        SELECT COUNT(*)
        FROM processed_weather
        WHERE temp_max < temp_min
        """
        result = db.query(sql)[0][0]
        assert result == 0, f"Found {result} records where temp_max < temp_min"


# ============================================================================
# TEST CATEGORY 3: CONSISTENCY
# ============================================================================
# Check that values follow business rules and are consistent

class TestConsistency:
    """Tests that data follows business rules and is internally consistent"""

    def test_forecast_times_are_in_future(self, db):
        """
        WHAT: Forecast records should have timestamp in the future
        WHY: Forecast data shouldn't be in the past
        NOTE: This assumes forecast records have a future timestamp
        """
        sql = """
        SELECT COUNT(*)
        FROM raw_weather
        WHERE timestamp < NOW()
          AND weather_condition LIKE '%Forecast%'
        """
        result = db.query(sql)[0][0]
        # This test is conditional - skip if no forecasts
        if result > 0:
            assert False, "Found forecast records with past timestamps"

    def test_processed_weather_references_valid_raw_weather(self, db):
        """
        WHAT: All processed_weather.raw_weather_id must exist in raw_weather
        WHY: Data integrity - foreign key constraint
        """
        sql = """
        SELECT COUNT(*)
        FROM processed_weather pw
        WHERE NOT EXISTS (
            SELECT 1 FROM raw_weather rw WHERE rw.id = pw.raw_weather_id
        )
        """
        result = db.query(sql)[0][0]
        assert result == 0, f"Found {result} orphaned processed records"

    def test_city_names_are_consistent(self, db):
        """
        WHAT: Same city should always have same country
        WHY: Data consistency - Paris should always be France, not Germany
        """
        sql = """
        SELECT DISTINCT city, country
        FROM raw_weather
        WHERE city IS NOT NULL
        ORDER BY city
        """
        results = db.query(sql)

        # Build a city->country map and check for conflicts
        city_country_map = {}
        for city, country in results:
            if city in city_country_map:
                assert city_country_map[city] == country, \
                    f"City '{city}' has inconsistent countries: {city_country_map[city]} vs {country}"
            else:
                city_country_map[city] = country


# ============================================================================
# TEST CATEGORY 4: FRESHNESS
# ============================================================================
# Check that data is timely and up-to-date

class TestFreshness:
    """Tests that data is recent and timely"""

    def test_recent_data_exists(self, db):
        """
        WHAT: Latest data should be less than 2 hours old
        WHY: Pipeline should run regularly; old data indicates failure
        SLO: Data freshness < 2 hours
        """
        sql = """
        SELECT MAX(timestamp)
        FROM raw_weather
        """
        result = db.query(sql)[0][0]

        if result:
            age = datetime.now(result.tzinfo) - result
            assert age < timedelta(hours=2), \
                f"Latest data is {age.total_seconds()/3600:.1f} hours old"

    def test_data_from_last_24_hours(self, db):
        """
        WHAT: Should have records from the last 24 hours
        WHY: Ensures pipeline ran recently
        """
        sql = """
        SELECT COUNT(*)
        FROM raw_weather
        WHERE timestamp > NOW() - INTERVAL '24 hours'
        """
        result = db.query(sql)[0][0]
        assert result > 0, "No data from the last 24 hours"


# ============================================================================
# TEST CATEGORY 5: UNIQUENESS
# ============================================================================
# Check for unexpected duplicates

class TestUniqueness:
    """Tests that data doesn't have unexpected duplicates"""

    def test_no_duplicate_records_for_same_timestamp_and_city(self, db):
        """
        WHAT: For the same city and timestamp, should only have 1 record
        WHY: Duplicates inflate counts and skew analysis
        """
        sql = """
        SELECT city, timestamp, COUNT(*) as count
        FROM raw_weather
        GROUP BY city, timestamp
        HAVING COUNT(*) > 1
        """
        result = db.query(sql)
        assert len(result) == 0, \
            f"Found {len(result)} duplicate records: {result}"

    def test_processed_records_not_duplicated(self, db):
        """
        WHAT: Processed weather shouldn't process same raw record twice
        WHY: Prevents data multiplication errors
        """
        sql = """
        SELECT raw_weather_id, COUNT(*) as count
        FROM processed_weather
        GROUP BY raw_weather_id
        HAVING COUNT(*) > 1
        """
        result = db.query(sql)
        assert len(result) == 0, \
            f"Found {len(result)} processed records processed multiple times"


# ============================================================================
# TEST CATEGORY 6: VOLUME/SANITY CHECKS
# ============================================================================
# Check that data volume meets expectations

class TestVolume:
    """Tests that data volume is as expected"""

    def test_expected_number_of_records_per_run(self, db):
        """
        WHAT: Each run should create ~36 records (4 cities × 9 records each)
        WHY: Sudden drops indicate pipeline failure
        EXPECTED: At minimum, should have records from 4 cities
        """
        sql = """
        SELECT COUNT(DISTINCT city)
        FROM raw_weather
        WHERE timestamp > NOW() - INTERVAL '1 hour'
        """
        result = db.query(sql)[0][0]
        assert result >= 4, \
            f"Expected >=4 cities, got {result}. Pipeline may have failed."

    def test_has_data_from_multiple_cities(self, db):
        """
        WHAT: Should have data from multiple cities
        WHY: Single city data might indicate ingestion failure
        """
        sql = """
        SELECT COUNT(DISTINCT city)
        FROM raw_weather
        """
        result = db.query(sql)[0][0]
        assert result >= 2, \
            f"Only have data from {result} city/cities. Expected at least 2."


# ============================================================================
# INTEGRATION TEST
# ============================================================================
# End-to-end data quality check

class TestDataQualityIntegration:
    """Full data quality check"""

    def test_overall_data_quality_score(self, db):
        """
        WHAT: Calculate overall data quality score
        WHY: Single metric to track quality over time

        SCORING:
        - 100% if all tests pass
        - Deduct points for each issue
        """
        checks = {
            "completeness": self._check_completeness(db),
            "accuracy": self._check_accuracy(db),
            "consistency": self._check_consistency(db),
            "freshness": self._check_freshness(db),
            "uniqueness": self._check_uniqueness(db),
        }

        quality_score = sum(checks.values()) / len(checks) * 100

        print(f"\n{'='*50}")
        print(f"Data Quality Report")
        print(f"{'='*50}")
        for check, score in checks.items():
            print(f"{check.capitalize():20s}: {score*100:.0f}%")
        print(f"{'='*50}")
        print(f"Overall Score:       {quality_score:.1f}%")
        print(f"{'='*50}\n")

        assert quality_score >= 80, \
            f"Data quality score {quality_score:.1f}% is below 80% threshold"

    def _check_completeness(self, db) -> float:
        sql = "SELECT COUNT(*) FROM raw_weather WHERE city IS NULL OR timestamp IS NULL"
        issues = db.query(sql)[0][0]
        return 1.0 if issues == 0 else 0.5

    def _check_accuracy(self, db) -> float:
        sql = """
        SELECT COUNT(*) FROM processed_weather
        WHERE humidity < 0 OR humidity > 100
           OR wind_speed < 0
           OR temp_current < -50 OR temp_current > 60
        """
        issues = db.query(sql)[0][0]
        return 1.0 if issues == 0 else 0.5

    def _check_consistency(self, db) -> float:
        sql = """
        SELECT COUNT(*) FROM processed_weather
        WHERE temp_max < temp_min
        """
        issues = db.query(sql)[0][0]
        return 1.0 if issues == 0 else 0.5

    def _check_freshness(self, db) -> float:
        sql = "SELECT COUNT(*) FROM raw_weather WHERE timestamp > NOW() - INTERVAL '24 hours'"
        recent = db.query(sql)[0][0]
        return 1.0 if recent > 0 else 0.0

    def _check_uniqueness(self, db) -> float:
        sql = """
        SELECT COUNT(*) FROM (
            SELECT city, timestamp, COUNT(*) as count
            FROM raw_weather
            GROUP BY city, timestamp
            HAVING COUNT(*) > 1
        ) t
        """
        duplicates = db.query(sql)[0][0]
        return 1.0 if duplicates == 0 else 0.5
