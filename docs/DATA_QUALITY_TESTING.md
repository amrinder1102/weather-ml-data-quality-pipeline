# Data Quality Testing Guide

## Overview

Data Quality Tests verify that ingested and processed data meets standards. This is **critical for MLOps** — you can't trust ML models built on bad data.

This guide teaches you the 5 core categories of data quality testing applied to your weather pipeline.

---

## The 5 Categories of Data Quality Tests

### 1. **COMPLETENESS** - Are all required fields present?

**What:** Verify no essential fields are NULL/missing

**Why:** Missing data breaks downstream processing and ML models

**Example in your pipeline:**
```python
def test_raw_weather_has_required_fields(self, db):
    sql = """
    SELECT COUNT(*) 
    FROM raw_weather 
    WHERE city IS NULL OR timestamp IS NULL
    """
    result = db.query(sql)[0][0]
    assert result == 0, f"Found {result} records with missing fields"
```

**What this catches:**
- ❌ Records without city names
- ❌ Records without timestamps  
- ❌ NULL temperature values

**Interview talking point:** "If you're missing 10% of temperature values, your ML model is trained on biased data"

---

### 2. **ACCURACY** - Are values in valid/reasonable ranges?

**What:** Verify data falls within expected bounds

**Why:** Out-of-range values are usually errors or edge cases

**Example in your pipeline:**
```python
def test_temperature_in_reasonable_range(self, db):
    sql = """
    SELECT COUNT(*) 
    FROM processed_weather 
    WHERE temp_current < -50 OR temp_current > 60
    """
    result = db.query(sql)[0][0]
    assert result == 0, f"Found invalid temps: {result}"
```

**What this catches:**
- ❌ Temperature = 999°C (API error)
- ❌ Humidity = 150% (impossible)
- ❌ Wind speed = -5 m/s (negative)

**Interview talking point:** "I define business rules for valid data ranges and continuously validate against them"

---

### 3. **CONSISTENCY** - Do values follow business rules?

**What:** Verify data is internally consistent and follows logic

**Why:** Prevents logical contradictions that break analysis

**Example in your pipeline:**
```python
def test_temp_max_greater_than_min(self, db):
    sql = """
    SELECT COUNT(*) 
    FROM processed_weather 
    WHERE temp_max < temp_min
    """
    result = db.query(sql)[0][0]
    assert result == 0, "Max temp should never be less than min temp"
```

**What this catches:**
- ❌ Max temp (5°C) < Min temp (10°C)
- ❌ Same city with different countries in same dataset
- ❌ Processed records referencing non-existent raw records (foreign key)

**Interview talking point:** "Consistency checks catch logical errors that would be silently wrong in ML models"

---

### 4. **FRESHNESS** - Is data timely and up-to-date?

**What:** Verify data is recent (not stale)

**Why:** Old data indicates pipeline failure or maintenance window

**Example in your pipeline:**
```python
def test_recent_data_exists(self, db):
    sql = """
    SELECT MAX(timestamp) FROM raw_weather
    """
    result = db.query(sql)[0][0]
    age = datetime.now(result.tzinfo) - result
    assert age < timedelta(hours=2), f"Data is {age.total_seconds()/3600:.1f} hours old"
```

**What this catches:**
- ❌ Pipeline hasn't run in 24+ hours
- ❌ API is down
- ❌ Data ingestion is stuck

**Interview talking point:** "Freshness SLOs are critical for real-time ML systems. I define and monitor: 'Data must be < 2 hours old'"

---

### 5. **UNIQUENESS** - Are there unexpected duplicates?

**What:** Verify no unexpected duplicate records

**Why:** Duplicates inflate metrics and bias ML models

**Example in your pipeline:**
```python
def test_no_duplicate_records_for_same_timestamp_and_city(self, db):
    sql = """
    SELECT city, timestamp, COUNT(*) 
    FROM raw_weather
    GROUP BY city, timestamp
    HAVING COUNT(*) > 1
    """
    result = db.query(sql)
    assert len(result) == 0, f"Found {len(result)} duplicates"
```

**What this catches:**
- ❌ Same city/time ingested twice
- ❌ Raw records processed multiple times
- ❌ Batch jobs running twice

**Interview talking point:** "Duplicate detection prevents training data leakage"

---

## How to Run the Tests

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the database (if using Docker)
```bash
docker-compose up -d
```

### 3. Run all tests
```bash
pytest tests/test_data_quality.py -v
```

### 4. Run specific test category
```bash
pytest tests/test_data_quality.py::TestCompleteness -v
```

### 5. Run with coverage report
```bash
pytest tests/test_data_quality.py --cov=src --cov-report=html
```

### 6. Run with detailed output
```bash
pytest tests/test_data_quality.py -v -s
```

---

## Understanding the Test Output

```
test_data_quality.py::TestCompleteness::test_raw_weather_has_required_fields PASSED
test_data_quality.py::TestAccuracy::test_temperature_in_reasonable_range PASSED
test_data_quality.py::TestFreshness::test_recent_data_exists PASSED
...

============================ PASSED 15 ============================
```

**Green (PASSED):** All checks passed - data quality is good ✅

**Red (FAILED):** Issues found - investigate immediately ⚠️

---

## The Data Quality Score

The integration test calculates an overall **Data Quality Score** (0-100%):

```
==================================================
Data Quality Report
==================================================
Completeness:        100%
Accuracy:            100%
Consistency:          95%
Freshness:           100%
Uniqueness:          100%
==================================================
Overall Score:        99.0%
==================================================
```

**Scoring:**
- 100% if all checks pass for that category
- 50% if issues found
- Must be ≥80% to pass

---

## Key Concepts for MLOps

### SLO (Service Level Objective)
A target for how good your data should be.

Example SLOs for weather pipeline:
- Completeness: ≥99% (all required fields present)
- Accuracy: 100% (all values valid)
- Freshness: Data < 2 hours old
- Uniqueness: Zero duplicates

### Data Contract
Agreement between data producer and consumer about data quality.

Example: "Processed weather will have 36 records per run with temperature within -50 to 60°C"

### Data Lineage
Tracking where data comes from and how it transforms.

Example:
```
OpenWeatherMap API 
  → Fetch Data 
  → Raw Table 
  → Validate 
  → Processed Table 
  → ML Model
```

Each step has quality gates.

---

## Common Patterns

### Pattern 1: Range Validation
```python
def test_value_in_range(self, db):
    sql = "SELECT COUNT(*) FROM table WHERE column < min_val OR column > max_val"
    assert db.query(sql)[0][0] == 0
```

### Pattern 2: Null Validation
```python
def test_required_field_not_null(self, db):
    sql = "SELECT COUNT(*) FROM table WHERE required_column IS NULL"
    assert db.query(sql)[0][0] == 0
```

### Pattern 3: Consistency Validation
```python
def test_logical_constraint(self, db):
    sql = "SELECT COUNT(*) FROM table WHERE max_value < min_value"
    assert db.query(sql)[0][0] == 0
```

### Pattern 4: Freshness Validation
```python
def test_data_freshness(self, db):
    sql = "SELECT MAX(timestamp) FROM table"
    latest = db.query(sql)[0][0]
    age = datetime.now(latest.tzinfo) - latest
    assert age < timedelta(hours=2)
```

### Pattern 5: Uniqueness Validation
```python
def test_no_duplicates(self, db):
    sql = """
    SELECT COUNT(*) FROM (
        SELECT col1, col2, COUNT(*) FROM table
        GROUP BY col1, col2 HAVING COUNT(*) > 1
    ) t"""
    assert db.query(sql)[0][0] == 0
```

---

## Interview Tips

When discussing data quality testing:

1. **Lead with the problem:** "Bad data breaks ML models. I test for..."
2. **Show business impact:** "Duplicates bias training; nulls reduce accuracy"
3. **Mention SLOs:** "I define and monitor freshness SLO: data < 2 hours old"
4. **Emphasize automation:** "These tests run automatically in CI/CD on every pipeline run"
5. **Show the score:** "We track a data quality score that must stay ≥80%"

---

## Next Steps

1. ✅ Understand the 5 categories
2. ✅ Write tests for your data
3. ⬜ Add tests to GitHub Actions (CI/CD)
4. ⬜ Create monitoring dashboard
5. ⬜ Define SLOs for your team

---

## Additional Resources

- [Great Expectations](https://greatexpectations.io/) - Popular data validation library
- [dbt tests](https://docs.getdbt.com/docs/build/tests) - SQL-based data testing
- [Soda](https://www.soda.io/) - Data quality monitoring platform
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL toolkit
