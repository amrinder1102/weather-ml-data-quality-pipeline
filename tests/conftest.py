"""
Shared pytest configuration and fixtures

Fixtures are reusable test setup - they run before each test and clean up after.
Think of them like @Before and @After in Java/C# testing frameworks.
"""

import pytest
import psycopg2
import os
from datetime import datetime


@pytest.fixture(scope="session")
def db_config():
    """Database configuration - used once per test session"""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME", "weather_pipeline"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres_pwd"),
        "port": os.getenv("DB_PORT", "5432"),
    }


@pytest.fixture
def db_connection(db_config):
    """
    Database connection fixture

    USAGE:
        def test_something(db_connection):
            conn = db_connection
            # Use connection...
            conn.close()

    Automatically closes connection after test
    """
    try:
        conn = psycopg2.connect(**db_config)
        yield conn
    finally:
        if conn:
            conn.close()


@pytest.fixture
def db_cursor(db_connection):
    """Database cursor fixture for executing queries"""
    cursor = db_connection.cursor()
    yield cursor
    cursor.close()


def pytest_configure(config):
    """Hook that runs before any tests"""
    print("\n" + "="*70)
    print("DATA QUALITY TEST SUITE")
    print("="*70)
    print(f"Testing database: {os.getenv('DB_NAME', 'weather_pipeline')}")
    print(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")


def pytest_collection_modifyitems(config, items):
    """Hook to add markers to tests that lack them"""
    for item in items:
        # Auto-categorize tests by their class name
        if "Completeness" in item.nodeid:
            item.add_marker(pytest.mark.completeness)
        elif "Accuracy" in item.nodeid:
            item.add_marker(pytest.mark.accuracy)
        elif "Consistency" in item.nodeid:
            item.add_marker(pytest.mark.consistency)
        elif "Freshness" in item.nodeid:
            item.add_marker(pytest.mark.freshness)
        elif "Uniqueness" in item.nodeid:
            item.add_marker(pytest.mark.uniqueness)
        elif "Integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
