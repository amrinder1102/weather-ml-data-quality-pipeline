# Data Quality Tests

This directory contains pytest-based data quality tests for the weather ML pipeline.

## Quick Start

### 1. Install test dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the database (if using Docker)
```bash
docker-compose up -d
```

### 3. Run all tests
```bash
pytest -v
```

---

## Test Commands

### Run all tests with output
```bash
pytest tests/ -v -s
```

### Run specific test category
```bash
# Completeness tests only
pytest tests/test_data_quality.py::TestCompleteness -v

# Accuracy tests only
pytest tests/test_data_quality.py::TestAccuracy -v

# All Freshness tests
pytest tests/test_data_quality.py::TestFreshness -v
```

### Run by marker
```bash
# Run all completeness-marked tests
pytest -m completeness -v

# Run all accuracy tests
pytest -m accuracy -v

# Skip slow tests
pytest -m "not slow" -v
```

### Generate coverage report
```bash
pytest --cov=src --cov=tests --cov-report=html
# Opens: htmlcov/index.html
```

### Run with detailed failure output
```bash
pytest -v -s --tb=long
```

### Run single test
```bash
pytest tests/test_data_quality.py::TestCompleteness::test_raw_weather_has_required_fields -v
```

---

## Test Categories

| Category | Purpose | What It Catches |
|----------|---------|-----------------|
| **Completeness** | All required fields present | Missing values, NULLs |
| **Accuracy** | Values in valid ranges | Out-of-range data, errors |
| **Consistency** | Logical constraints met | Contradictions, invalid relationships |
| **Freshness** | Data is recent | Stale data, pipeline failures |
| **Uniqueness** | No unexpected duplicates | Data multiplication, retries |

---

## Example Test Run

```bash
$ pytest tests/test_data_quality.py -v

test_data_quality.py::TestCompleteness::test_raw_weather_has_required_fields PASSED [  6%]
test_data_quality.py::TestCompleteness::test_processed_weather_has_temperature PASSED [ 13%]
test_data_quality.py::TestAccuracy::test_temperature_in_reasonable_range PASSED [ 20%]
test_data_quality.py::TestAccuracy::test_humidity_between_0_and_100 PASSED [ 26%]
test_data_quality.py::TestFreshness::test_recent_data_exists PASSED [ 33%]
...

========================== PASSED 15 ========================
```

---

## Writing New Tests

### Pattern: Add a Completeness Test

```python
def test_your_new_check(self, db):
    """WHAT: What are you checking?
    WHY: Why does this matter?
    """
    sql = """
    SELECT COUNT(*) 
    FROM your_table 
    WHERE your_condition
    """
    result = db.query(sql)[0][0]
    assert result == 0, "Your error message"
```

### Pattern: Add an Accuracy Test

```python
def test_value_in_range(self, db):
    """WHAT: Value should be between X and Y
    WHY: Physical/business constraint
    """
    sql = """
    SELECT COUNT(*) 
    FROM your_table 
    WHERE column < min_value OR column > max_value
    """
    result = db.query(sql)[0][0]
    assert result == 0, f"Found {result} out-of-range values"
```

---

## Troubleshooting

### "Connection refused" error
**Problem:** Database not running  
**Solution:**
```bash
docker-compose up -d
# or
psql -h localhost -U postgres -d weather_pipeline
```

### "Permission denied" error
**Problem:** No permission to connect to database  
**Solution:**
```bash
# Check credentials in conftest.py
export DB_USER=postgres
export DB_PASSWORD=postgres_pwd
```

### Tests pass locally but fail in CI
**Problem:** Environment variables not set in CI  
**Solution:** Add to GitHub Actions secrets (see CI/CD docs)

---

## Integration with CI/CD

These tests run automatically in GitHub Actions (see `.github/workflows/`):

```yaml
- name: Run Data Quality Tests
  run: pytest tests/ -v --cov
```

---

## For Interviews

**Talking points:**
- "I write automated data quality tests using pytest"
- "Tests verify completeness, accuracy, consistency, freshness, uniqueness"
- "These run on every pipeline execution in CI/CD"
- "Data quality score must be ≥80% to pass"
- "This prevents bad data from training ML models"

---

## Further Reading

- [DATA_QUALITY_TESTING.md](../docs/DATA_QUALITY_TESTING.md) - Detailed guide
- [pytest docs](https://docs.pytest.org/)
- [Great Expectations](https://greatexpectations.io/) - Production data validation
