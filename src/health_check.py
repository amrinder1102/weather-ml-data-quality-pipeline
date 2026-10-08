import requests
from src.db import WeatherDB
from src.logging_config import get_logger

logger = get_logger(__name__)

class HealthCheck:
    def __init__(self, api_key, db_host, db_name, db_user, db_password):
        self.api_key = api_key
        self.db_host = db_host
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.checks = {}

    def check_api(self):
        """Verify weather API is accessible."""
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {"q": "London", "appid": self.api_key}
            response = requests.get(url, params=params, timeout=5)
            self.checks["api"] = response.status_code == 200
            if self.checks["api"]:
                logger.info("✓ Weather API: OK")
            else:
                logger.warning(f"✗ Weather API: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"✗ Weather API check failed: {e}")
            self.checks["api"] = False

    def check_database(self):
        """Verify database connection."""
        try:
            db = WeatherDB(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            db.connect()
            db.disconnect()
            self.checks["database"] = True
            logger.info("✓ Database: OK")
        except Exception as e:
            logger.error(f"✗ Database check failed: {e}")
            self.checks["database"] = False

    def run_all(self):
        """Run all health checks."""
        logger.info("=== HEALTH CHECKS ===")
        self.check_api()
        self.check_database()

        all_passed = all(self.checks.values())
        status = "✓ PASSED" if all_passed else "✗ FAILED"
        logger.info(f"Health checks {status}")

        return all_passed, self.checks
