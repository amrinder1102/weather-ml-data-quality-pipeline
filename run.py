from src.fetchData import fetch_weather_for_cities
from src.data_validation import validate_data_db
from src.db import WeatherDB
from src.health_check import HealthCheck
from src.logging_config import setup_logging, get_logger
from dotenv import load_dotenv
import os
import sys

load_dotenv()
logger = setup_logging()

API_KEY = os.getenv("API_KEY", "51e66d293f315eb6295deed2003c5082")
CITIES = ["London", "New York", "Tokyo", "Sydney"]

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "weather_pipeline")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def main():
    """Main pipeline orchestrator."""
    try:
        logger.info("=== WEATHER ML PIPELINE STARTED ===")

        # Health checks
        health = HealthCheck(API_KEY, DB_HOST, DB_NAME, DB_USER, DB_PASSWORD)
        all_healthy, checks = health.run_all()

        if not all_healthy:
            logger.error("Health checks failed. Aborting pipeline.")
            return False

        # Connect to database
        logger.info("=== CONNECTING TO DATABASE ===")
        db = WeatherDB(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        db.connect()

        # Step 1: Fetch data
        logger.info("=== FETCHING DATA ===")
        weather_data = fetch_weather_for_cities(CITIES, API_KEY, include_forecast=True)

        if not weather_data:
            logger.error("No weather data fetched.")
            db.disconnect()
            return False

        # Insert raw data into database
        logger.info("=== STORING RAW DATA ===")
        raw_ids = db.insert_raw_weather(weather_data)

        # Step 2: Validate & Process
        logger.info("=== VALIDATING DATA ===")
        quality_score, report, proceed, processed_data = validate_data_db(weather_data)

        logger.info(f"Quality Score: {report['quality_score']}%")
        logger.info(f"Status: {report['status']}")

        if proceed:
            logger.info("Validation PASSED - Processing data...")
            db.insert_processed_weather(processed_data, raw_ids)
            logger.info(f"Processed records: {report['processed_records']}")
        else:
            logger.warning("Validation FAILED - Quality score < 80%")
            logger.info("Pipeline stopped. Issues:")
            for check, result in report["checks"].items():
                logger.info(f"  - {check}: {result}")

        # Save report to database
        logger.info("=== SAVING QUALITY REPORT ===")
        db.save_quality_report(report)

        db.disconnect()
        logger.info("=== PIPELINE COMPLETED SUCCESSFULLY ===")
        return True

    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        return False
    except Exception as e:
        logger.exception(f"Pipeline failed with error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
