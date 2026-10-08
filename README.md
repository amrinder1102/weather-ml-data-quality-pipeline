# 🌦️ Weather ML Data Quality Pipeline - Production-Ready MLOps

A complete, production-grade data quality monitoring pipeline that demonstrates MLOps best practices. Fetches weather data, validates quality, stores in PostgreSQL, and monitors data quality over time.

**Status:** ✅ Production-Ready | 🐳 Containerized | 📊 Monitored | 🔍 Logged

---

## 🎯 What This Project Does

```
Weather API
    ↓
Fetch Data (4 cities + forecast)
    ↓
Store Raw Data → PostgreSQL (raw_weather table)
    ↓
Validate Quality (5 checks)
    ↓
Quality Gate: Score ≥ 80%?
    ├─ YES → Store Processed Data (processed_weather table)
    └─ NO  → Alert & Skip
    ↓
Save Quality Report → PostgreSQL (quality_reports table)
    ↓
Logs & Exit Code for Automation
```

---

## 🚀 Quick Start

### **Local Development (No Docker)**

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start PostgreSQL (if not running)
brew services start postgresql@15

# 3. Create database and load schema
createdb weather_pipeline
psql weather_pipeline < schema.sql

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 5. Run pipeline
python3 run.py
```

### **With Docker Compose (Recommended)**

```bash
# Single command - starts PostgreSQL + pipeline
docker-compose up

# View logs in real-time
docker-compose logs -f pipeline

# Stop everything
docker-compose down
```

---

## 📊 Data Model

### **3-Table Database Schema**

#### `raw_weather` (Raw API Data)
```sql
city        | temp_max | temp_min | humidity | pressure | wind_speed | timestamp
London      | 22.5     | 15.3     | 65       | 1013     | 4.2        | 2024-10-07...
New York    | 18.1     | 12.4     | 72       | 1015     | 5.1        | 2024-10-07...
Tokyo       | 25.0     | 20.1     | 58       | 1010     | 3.5        | 2024-10-07...
Sydney      | 28.3     | 22.1     | 45       | 1018     | 6.2        | 2024-10-07...
```

#### `processed_weather` (Validated & Cleaned)
```sql
city        | temp_max | temp_min | humidity | pressure | wind_speed | timestamp
London      | 22.5     | 15.3     | 65       | 1013     | 4.2        | 2024-10-07...
(Only records that passed quality checks)
```

#### `quality_reports` (Quality Metrics)
```sql
timestamp           | quality_score | status  | checks (JSON)
2024-10-07 17:00:00 | 100.0        | PASSED  | {"schema": "PASSED", "bounds": "PASSED", ...}
2024-10-06 17:00:00 | 80.0         | PASSED  | ...
```

---

## 🔄 Pipeline Workflow

### **Phase 1: Data Ingestion**
- Fetches current weather + 5-day forecast for 4 cities
- Uses OpenWeatherMap API
- Creates 36 records (4 cities × current + 8 forecast points)

### **Phase 2: Data Validation** (5 Checks)
1. **Schema Validation** — Required columns exist?
2. **Missing Values** — Less than 5% missing?
3. **Bounds Checking** — Values within physical limits?
4. **Consistency** — temp_min ≤ temp_max?
5. **Distribution** — Data has variance (std > 0.5)?

### **Phase 3: Quality Gating**
- **Score ≥ 80%** → Proceed to processing
- **Score < 80%** → Stop pipeline, log issues

### **Phase 4: Data Processing**
- Convert types, fill missing values
- Create temporal features (month, day_of_week)
- Create lagged features (previous day values)
- Store processed data in DB

### **Phase 5: Monitoring & Logging**
- Save quality report to database
- Log all activity to file + console
- Return exit code (0 = success, 1 = failure)

---

## 🏗️ Project Structure

```
weather-ml-pipeline/
├── run.py                      # Main pipeline orchestrator
├── schema.sql                  # Database schema
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container image
├── docker-compose.yml          # Local dev environment
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
│
├── src/
│   ├── __init__.py            # Package exports
│   ├── fetchData.py           # Weather API integration
│   ├── data_validation.py     # Quality validation logic
│   ├── db.py                  # Database operations
│   ├── logging_config.py      # Logging setup
│   └── health_check.py        # Pre-flight checks
│
├── logs/                       # Pipeline logs (git-ignored)
│   └── pipeline_YYYYMMDD_HHMMSS.log
│
└── docs/
    ├── README.md              # This file
    ├── DB_SETUP.md           # Database setup guide
    └── PRODUCTION_READY.md    # Production deployment guide
```

---

## 🔧 Production Features

### ✅ **Logging**
- Logs to console + file
- Timestamps on every entry
- Tracks all operations for debugging

```bash
# View latest logs
tail -f logs/pipeline_*.log

# Search for errors
grep ERROR logs/pipeline_*.log
```

### ✅ **Error Handling**
- Database connection retries (up to 3 attempts)
- Graceful failure modes
- Detailed error messages

### ✅ **Health Checks**
- Verifies API accessibility
- Verifies database connectivity
- Runs before pipeline starts

```bash
python3 -c "from src.health_check import HealthCheck; h = HealthCheck(...); h.run_all()"
```

### ✅ **Docker Containerization**
- Consistent runtime environment
- Easy deployment anywhere
- PostgreSQL client included
- Health checks built-in

```bash
docker build -t weather-pipeline .
docker run weather-pipeline
```

### ✅ **Exit Codes**
- `0` = Pipeline succeeded
- `1` = Pipeline failed

Useful for CI/CD, cron jobs, orchestration

---

## 📈 Monitoring & Querying Data

### **View Latest Quality Report**
```bash
psql weather_pipeline -c "
  SELECT timestamp, quality_score, status, checks 
  FROM quality_reports 
  ORDER BY timestamp DESC LIMIT 1;
"
```

### **Track Quality Over Time**
```bash
psql weather_pipeline -c "
  SELECT 
    DATE(timestamp) as date,
    AVG(quality_score) as avg_score,
    COUNT(CASE WHEN status='PASSED' THEN 1 END) as passed,
    COUNT(CASE WHEN status='FAILED' THEN 1 END) as failed
  FROM quality_reports
  GROUP BY DATE(timestamp)
  ORDER BY date DESC;
"
```

### **Find Data Issues**
```bash
psql weather_pipeline -c "
  SELECT * FROM quality_reports 
  WHERE status = 'FAILED' 
  ORDER BY timestamp DESC;
"
```

---

## 🚢 Deployment Options

### **Option 1: Local (Development)**
```bash
python3 run.py
```

### **Option 2: Docker (Consistent Environment)**
```bash
docker-compose up
```

### **Option 3: Cloud (GitHub Actions)**
See `PRODUCTION_READY.md` for automated scheduling

### **Option 4: Kubernetes (Enterprise)**
Similar to Docker, but with orchestration for high availability

---

## 📚 Configuration

### **Environment Variables** (`.env`)
```
# Weather API
API_KEY=your_openweathermap_key

# PostgreSQL Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=weather_pipeline
DB_USER=postgres
DB_PASSWORD=postgres_pwd
```

### **Data Validation Thresholds** (`src/data_validation.py`)
```python
# Adjust these for different requirements:
- Missing value tolerance: 5%
- Temperature bounds: -50°C to 70°C
- Humidity: 0-100%
- Pressure: 900-1100 hPa
- Quality gate: ≥ 80%
```

---

## 🧪 Testing

### **Test Health Checks**
```bash
python3 -c "
from src.health_check import HealthCheck
import os
h = HealthCheck(os.getenv('API_KEY'), 'localhost', 'weather_pipeline', 'postgres', '')
passed, checks = h.run_all()
print(f'Health Check: {\"PASS\" if passed else \"FAIL\"}')
print(f'Checks: {checks}')
"
```

### **Test Database Connection**
```bash
python3 -c "
from src.db import WeatherDB
db = WeatherDB()
db.connect()
print('✓ Database connected')
db.disconnect()
"
```

### **Test Full Pipeline**
```bash
python3 run.py
# Should complete with exit code 0
echo $?  # Print exit code
```

---

## 📊 What We Achieved

### **Phase 1: Core Pipeline** ✅
- ✅ Fetches weather data from OpenWeatherMap API
- ✅ Validates data quality (5 automated checks)
- ✅ Quality gate (only process if score ≥ 80%)
- ✅ Stores data in PostgreSQL (3 tables)

### **Phase 2: Database Integration** ✅
- ✅ Created database schema (raw, processed, reports)
- ✅ Migrated from CSV files to PostgreSQL
- ✅ Added database connection management
- ✅ Added permission handling

### **Phase 3: Production-Ready** ✅
- ✅ Logging system (file + console)
- ✅ Error handling with retries
- ✅ Health checks (API + Database)
- ✅ Docker containerization
- ✅ Docker Compose for local dev
- ✅ Exit codes for automation
- ✅ Comprehensive documentation

---

## 🎓 Learning Outcomes

This project demonstrates:

1. **MLOps Fundamentals**
   - Data quality as first-class concern
   - Quality gates preventing bad data
   - Monitoring & alerts

2. **Software Engineering**
   - Structured logging
   - Error handling & retries
   - Health checks & observability
   - Container orchestration

3. **Database Design**
   - Schema design (normalized tables)
   - Indexing for performance
   - Data relationships (foreign keys)

4. **Automation & Deployment**
   - Containerization (Docker)
   - Local dev environment (Docker Compose)
   - Exit codes for CI/CD
   - Production-ready practices

---

## 🔗 Key Files

- **Main Pipeline:** [run.py](run.py)
- **Database Schema:** [schema.sql](schema.sql)
- **Database Module:** [src/db.py](src/db.py)
- **Validation Logic:** [src/data_validation.py](src/data_validation.py)
- **Setup Guide:** [DB_SETUP.md](DB_SETUP.md)
- **Production Guide:** [PRODUCTION_READY.md](PRODUCTION_READY.md)

---

## 📋 Next Steps

1. **Try it locally:** `docker-compose up`
2. **Query the data:** See "Monitoring & Querying Data" section
3. **Schedule runs:** GitHub Actions (see PRODUCTION_READY.md)
4. **Add alerts:** Slack notifications on failure
5. **Scale up:** Deploy to cloud (AWS, GCP, Azure)

---

## 🤝 Contributing

This is a learning project. Feel free to:
- Extend validation checks
- Add new data sources
- Improve monitoring
- Add more tests

---

## 📝 License

Open source - use freely for learning & projects

---

**Built with:** Python • PostgreSQL • Docker • FastAPI (coming soon)

**Status:** Production-ready for deployment! 🚀
