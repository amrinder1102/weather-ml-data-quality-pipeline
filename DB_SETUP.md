# PostgreSQL Database Setup Guide

## Quick Start (macOS)

### 1. Install PostgreSQL
```bash
# Using Homebrew
brew install postgresql@15
brew services start postgresql@15

# Verify installation
psql --version
```

### 2. Create Database
```bash
# Create the database
createdb weather_pipeline

# Verify it exists
psql -l | grep weather_pipeline
```

### 3. Load Schema
```bash
# From project root directory
psql weather_pipeline < schema.sql

# Verify tables were created
psql weather_pipeline -c "\dt"
```

### 4. Set Up Environment
```bash
# Copy template
cp .env.example .env

# Edit .env with your credentials
# The default postgres user has no password by default, but set one for security
```

### 5. Set Postgres Password (Optional but Recommended)
```bash
# Connect as postgres
psql postgres

# Set password for postgres user
\password postgres
# Enter new password twice

# Exit
\q
```

### 6. Install Python Dependencies
```bash
pip install -r requirements.txt
```

---

## Verify Connection

```python
from src.db import WeatherDB

db = WeatherDB(
    host="localhost",
    database="weather_pipeline",
    user="postgres",
    password="your_password"  # if you set one
)
db.connect()

# If successful, you'll see:
# ✓ Connected to PostgreSQL database: weather_pipeline
```

---

## Common Commands

### Connect to Database
```bash
psql weather_pipeline
```

### View All Tables
```bash
psql weather_pipeline -c "\dt"
```

### View Table Structure
```bash
psql weather_pipeline -c "\d raw_weather"
```

### Query Data
```bash
psql weather_pipeline -c "SELECT COUNT(*) FROM raw_weather;"
```

### Clear All Data (Keep Schema)
```bash
psql weather_pipeline -c "
TRUNCATE processed_weather CASCADE;
TRUNCATE raw_weather CASCADE;
TRUNCATE quality_reports CASCADE;
"
```

### Drop Everything and Start Over
```bash
dropdb weather_pipeline
createdb weather_pipeline
psql weather_pipeline < schema.sql
```

---

## Database Schema Overview

### raw_weather
- **Purpose:** Store raw data from API
- **Retention:** All history (for debugging & drift detection)
- **Records per run:** ~12 (4 cities × current + 8 forecast points)

### processed_weather
- **Purpose:** Store validated, cleaned data
- **Retention:** Only data that passed quality checks
- **Reference:** Links back to raw_weather via raw_weather_id

### quality_reports
- **Purpose:** Track validation results over time
- **Retention:** All reports (shows quality trends)
- **Key columns:**
  - `quality_score`: 0-100%
  - `status`: "PASSED" or "FAILED"
  - `checks`: JSONB with all 5 validation results

---

## Next Steps

1. **Test the connection** with `python -c "from src.db import WeatherDB; db = WeatherDB(); db.connect()"`
2. **Run the pipeline** with database: `python run.py` (we'll update run.py to use DB)
3. **Query results:** Check the database with `psql weather_pipeline`
4. **Build dashboard:** Query quality reports over time
