# Technical Architecture: Weather ML Pipeline with Quality Monitoring

## 📐 Project Overview

**Project Name:** `weather-ml-pipeline`  
**Goal:** Build an automated ML pipeline that predicts daily maximum temperature while ensuring data quality at every step.  
**Key Differentiator:** Quality gates prevent bad data from training models; production monitoring catches data drift.

---

## 🎯 ML Task Definition

**Problem Type:** Regression (predict tomorrow's max temperature)  
**Target Variable:** `temp_max` (in Celsius)  
**Features:** 
- Previous day's temperature, humidity, pressure, wind speed
- Month (seasonality)
- Day of week

**Data Source:** OpenWeather API (free tier - historical + current weather)  
**Prediction Horizon:** Tomorrow's max temperature  
**Retraining Frequency:** Daily (scheduled 2 AM UTC)

---

## 🏗️ Project Structure

```
weather-ml-pipeline/
│
├── README.md                           # Project overview & how to run
├── PROBLEM_STATEMENT.md                # (already created)
├── WORKFLOW_DIAGRAM.md                 # (already created)
├── TECHNICAL_ARCHITECTURE.md           # (this file)
│
├── data/
│   ├── raw/
│   │   └── weather_raw_YYYY-MM-DD.csv  # Raw data from API (git tracked)
│   ├── processed/
│   │   └── weather_processed.csv       # Cleaned data after QA
│   └── validation_logs/
│       └── quality_report_YYYY-MM-DD.json  # Quality check results
│
├── models/
│   ├── model_v1.pkl                    # Trained model (git tracked)
│   ├── model_registry.json             # Metadata: date, metrics, commit
│   └── scaler.pkl                      # Feature scaling object
│
├── src/
│   ├── __init__.py
│   ├── data_ingestion.py               # Fetch weather from API
│   ├── data_validation.py              # Quality checks (schema, stats, rules)
│   ├── model_training.py               # Train & evaluate model
│   ├── model_registry.py               # Version & track models
│   ├── inference.py                    # Make predictions (for API)
│   ├── monitoring.py                   # Production data monitoring
│   └── utils.py                        # Helpers, logging, config
│
├── api/
│   ├── main.py                         # FastAPI app
│   ├── models.py                       # Request/response schemas
│   └── requirements.txt
│
├── dashboard/
│   ├── app.py                          # Streamlit monitoring dashboard
│   ├── requirements.txt
│   └── assets/
│       └── (images, styles if needed)
│
├── .github/
│   └── workflows/
│       ├── daily_pipeline.yml          # GitHub Actions: daily retraining
│       ├── tests.yml                   # GitHub Actions: run tests on PR
│       └── deploy.yml                  # GitHub Actions: deploy API & dashboard
│
├── tests/
│   ├── test_data_validation.py         # Unit tests for QA rules
│   ├── test_model_training.py          # Unit tests for model
│   ├── test_inference.py               # Unit tests for API
│   └── conftest.py                     # Pytest fixtures
│
├── config.yaml                         # Configuration (thresholds, API keys)
├── requirements.txt                    # Python dependencies
├── Dockerfile                          # For API containerization
└── .gitignore                          # Ignore models, logs, large data
```

---

## 🔧 Technology Stack

| Layer | Technology | Why |
|-------|------------|-----|
| **Data Ingestion** | `requests` library + OpenWeather API | Simple, free, no auth needed |
| **Data Processing** | `pandas`, `numpy` | Industry standard for ML |
| **Data Validation** | `great_expectations` OR custom pandas | Explicit quality rules (easier for portfolio) |
| **ML Model** | `scikit-learn` (RandomForest/LinearRegression) | Fast, simple, interpretable |
| **Model Storage** | `.pkl` files in git + JSON metadata | Simple versioning, easy to demo |
| **Feature Scaling** | `scikit-learn.preprocessing.StandardScaler` | Required for better predictions |
| **API** | `FastAPI` + `Uvicorn` | Modern, fast, auto-documentation |
| **Deployment** | Render.com or Railway.app (free tier) | No credit card, easy deploys |
| **Monitoring Dashboard** | `Streamlit` | Quick visualization, free hosting on Streamlit Cloud |
| **Orchestration** | GitHub Actions (YAML workflows) | Free, native to git, no infra to manage |
| **Testing** | `pytest` | Standard Python testing |
| **Logging** | `logging` module + JSON logs | Structured logging for debugging |

---

## 📊 Data Quality Checks (The Heart of This Project)

These validation rules run BEFORE every training. If ANY fail, pipeline stops and alerts team.

### 1️⃣ **Schema Validation**
```python
Required columns: [date, city, temp_max, temp_min, humidity, pressure, wind_speed]
Data types: [date=datetime, city=str, temps=float, humidity=int, pressure=float, wind_speed=float]
```

### 2️⃣ **Missing Values Check**
```python
- No row is 100% missing
- temp_max: 0% missing (required)
- humidity: < 5% missing (acceptable)
- Any column: < 20% missing overall
```

### 3️⃣ **Statistical Bounds Check**
```python
temp_max: -50°C to 70°C (absolute physical bounds)
humidity: 0-100% (percentage bounds)
pressure: 900-1100 hPa (meteorological bounds)
wind_speed: 0-100 km/h (reasonable bounds)

Outlier detection (IQR method):
- Values beyond Q1 - 1.5*IQR or Q3 + 1.5*IQR are flagged
```

### 4️⃣ **Consistency Checks**
```python
- temp_min <= temp_max (always)
- No future dates (data collection error)
- Sequence: recent data present (not too stale)
```

### 5️⃣ **Data Distribution Checks**
```python
- Temperature std dev > 0.5 (no constant values)
- Mean temperature reasonable for location
- If distribution shifts > 2 std devs from historical, flag it
```

**Quality Score:** If N checks pass, score = (N_passed / N_total) * 100%  
**Gate Threshold:** Only train if score >= 80%

---

## 🔄 Pipeline Workflow (Step-by-Step)

### **Daily Scheduled Run (GitHub Actions - 2 AM UTC)**

#### Step 1: Data Ingestion
```python
# Fetch weather data from OpenWeather API
# Cities: London, New York, Tokyo, Sydney (diverse climates)
# Save raw data: data/raw/weather_YYYY-MM-DD.csv
```

#### Step 2: Data Validation
```python
# Run 5 quality checks above
# Generate report: data/validation_logs/quality_YYYY-MM-DD.json
# If score < 80%:
#   - Send Slack alert
#   - Log issue to GitHub Issue
#   - STOP (don't proceed to training)
# Else:
#   - Continue to Step 3
```

#### Step 3: Data Processing
```python
# Clean & prepare data for training
# Create features: lagged temps, month, day_of_week
# Handle any minor issues (e.g., fill small gaps if < 5%)
# Split: 70% train, 30% test
```

#### Step 4: Model Training
```python
# Train RandomForestRegressor on training data
# Evaluate on test data
# Calculate metrics:
#   - MAE (Mean Absolute Error)
#   - RMSE (Root Mean Squared Error)
#   - R² Score
```

#### Step 5: Model Comparison
```python
# Compare new model vs old model
# If new model better (R² improvement > 2%):
#   - Register in model_registry.json
#   - Commit to git
#   - Deploy to production
# Else:
#   - Keep old model
#   - Log why new model was rejected
```

#### Step 6: Deploy
```python
# Push API to Render/Railway
# New model served immediately
# Health check: /health endpoint returns 200
```

#### Step 7: Monitor
```python
# API runs 24/7
# Every prediction:
#   - Validate input data quality
#   - Log prediction + input features
#   - Store in metrics DB
```

---

## 🚨 Alerting & Monitoring

### Quality Gate Failures
**When:** Data validation fails (quality < 80%)  
**Alert To:** Email + GitHub Issue  
**Message:** "Data quality check failed on 2024-XX-XX. Review: [link to report]"

### Production Data Drift
**When:** Production data stats diverge from training data  
**Alert To:** Streamlit dashboard + console logs  
**Action:** Flag for manual review

### Model Performance Drop
**When:** Test set metrics drop > 10% from baseline  
**Alert To:** Email + Slack  
**Action:** Pause automatic retraining, manual investigation

---

## 📈 Dashboard Features (Streamlit)

The monitoring dashboard (deployed free on Streamlit Cloud) shows:

1. **Data Quality Trends** — Line chart of daily quality scores
2. **Data Statistics** — Current vs historical distributions
3. **Model Metrics** — MAE, RMSE, R² over time
4. **Prediction Accuracy** — Actual vs predicted temps
5. **Alert History** — Log of all alerts & issues
6. **System Health** — Last pipeline run time, uptime

---

## 🌐 API Specification

### Endpoint: `POST /predict`

**Request:**
```json
{
  "temp_max_prev": 22.5,
  "temp_min_prev": 15.0,
  "humidity_prev": 65,
  "pressure_prev": 1013.25,
  "wind_speed_prev": 8.5,
  "month": 9,
  "day_of_week": 2
}
```

**Response:**
```json
{
  "predicted_temp_max": 24.3,
  "confidence": "high",
  "model_version": "v1",
  "timestamp": "2024-09-22T14:30:00Z"
}
```

### Endpoint: `GET /health`
Returns: `{"status": "healthy", "model_version": "v1"}`

### Endpoint: `GET /metrics`
Returns current model metrics (MAE, RMSE, R²)

---

## 🧪 Testing Strategy

### Unit Tests (pytest)
```
tests/test_data_validation.py
  - Test each QA rule independently
  - Test with good data, bad data, edge cases

tests/test_model_training.py
  - Test model trains on sample data
  - Test metrics are calculated correctly
  - Test model degrades gracefully

tests/test_inference.py
  - Test API handles valid requests
  - Test API rejects invalid inputs
  - Test predictions are in reasonable bounds
```

### Integration Tests
- Full pipeline runs end-to-end
- Data flows from API → validation → training → deployment

### Data Tests
- Sample data included in repo for reproducibility
- Tests run before every PR merge (GitHub Actions)

---

## 🚀 Deployment Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    GitHub Repository                      │
│  (code, trained models, data, workflows)                  │
└────────┬─────────────────┬──────────────────┬─────────────┘
         │                 │                  │
         ▼                 ▼                  ▼
   ┌──────────┐      ┌──────────┐      ┌───────────────┐
   │ GitHub   │      │ Render   │      │ Streamlit     │
   │ Actions  │      │ FastAPI  │      │ Dashboard     │
   │(Scheduler)│      │ Server   │      │ (Monitoring)  │
   └──────────┘      └──────────┘      └───────────────┘
        │                  │                  │
   Runs daily         Serves predictions  Shows metrics
   Trains model       & metrics            & alerts
```

---

## 📋 Implementation Timeline (1-2 weeks)

### **Week 1: Core Pipeline**
- Day 1-2: Project setup, data ingestion, basic validation
- Day 3-4: Model training, evaluation, registry
- Day 5: Local testing, GitHub Actions workflow setup

### **Week 2: Deployment & Monitoring**
- Day 1-2: FastAPI app, deployment to Render
- Day 3-4: Streamlit dashboard, metrics logging
- Day 5: Documentation, tests, final polish

---

## 🎓 Key Learning Outcomes

By building this, you'll demonstrate:
✅ ML pipeline design (data → training → deployment)  
✅ Data quality frameworks (validation, gates, monitoring)  
✅ CI/CD for ML (GitHub Actions, automated retraining)  
✅ Production systems (API, monitoring, alerts)  
✅ Software engineering rigor (testing, versioning, logging)  

**Interview angle:** "I didn't just build a model; I built a *reliable system* that ensures data quality and catches problems before they hit production."

---

## ⚙️ Configuration (config.yaml)

```yaml
openweather:
  api_key: "your_free_api_key"
  cities: ["London", "New York", "Tokyo", "Sydney"]
  units: "metric"

data_validation:
  quality_threshold: 80  # % score needed to proceed
  temp_max_bounds: [-50, 70]
  humidity_bounds: [0, 100]
  pressure_bounds: [900, 1100]
  wind_speed_bounds: [0, 100]
  missing_value_tolerance: 0.05  # 5% max

model:
  test_split: 0.3
  random_state: 42
  algorithm: "RandomForestRegressor"
  min_improvement: 0.02  # 2% R² improvement to deploy

deployment:
  api_host: "render.com"  # or railway.app
  dashboard_host: "streamlit.app"
  
alerts:
  email: "your-email@gmail.com"
  slack_webhook: "https://hooks.slack.com/..."
```

---

## 📚 Dependencies (requirements.txt)

```
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0
requests==2.31.0
python-dotenv==1.0.0
pyyaml==6.0
fastapi==0.100.0
uvicorn==0.23.0
streamlit==1.28.0
pytest==7.4.0
python-multipart==0.0.6
```

---

## Next Steps

1. ✅ Problem Statement (done)
2. ✅ Workflow Diagram (done)
3. ✅ Technical Architecture (this document)
4. ⏭️ **Create project structure & start coding**

Ready to start building? Next: initialize the repo with folder structure and first Python modules.
