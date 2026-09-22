# Data Quality Monitoring Pipeline - Workflow Diagram

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         ML DATA QUALITY MONITORING PIPELINE                        │
└─────────────────────────────────────────────────────────────────────────────────────┘

                                    GITHUB ACTIONS WORKFLOW
                            (Triggered Daily @ 2 AM or on Manual Trigger)
                                            │
                                            ▼
                    ┌──────────────────────────────────────┐
                    │   1️⃣  DATA INGESTION & LOADING       │
                    │   ────────────────────────────────   │
                    │  • Fetch from API/Database           │
                    │  • Load CSV/Parquet file             │
                    │  • Store raw data (git tracked)      │
                    └──────────────────────────────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────────────┐
                    │  2️⃣  DATA QUALITY VALIDATION         │
                    │  ────────────────────────────────    │
                    │  Schema Check ✓                      │
                    │  • Correct column names?             │
                    │  • Correct data types?               │
                    │                                      │
                    │  Missing Values Check ✓              │
                    │  • % missing < threshold?            │
                    │  • Specific columns not null?        │
                    │                                      │
                    │  Statistical Anomalies ✓             │
                    │  • Outliers detected (IQR)?          │
                    │  • Distribution shift?               │
                    │  • Mean/std within bounds?           │
                    │                                      │
                    │  Business Logic Rules ✓              │
                    │  • Temperature: -50 to 70°C?         │
                    │  • Price: > $0?                      │
                    │  • Date: not in future?              │
                    └──────────────────────────────────────┘
                                    │
                        ┌───────────┴───────────┐
                        │                       │
                    PASS ✅                   FAIL ❌
                        │                       │
                        ▼                       ▼
            ┌──────────────────────┐  ┌──────────────────────┐
            │ 3️⃣  TRAIN MODEL      │  │  SEND ALERT          │
            │ ──────────────────   │  │  ──────────────────  │
            │ • Data is clean ✓    │  │  • Quality failed    │
            │ • Split train/test   │  │  • Stop pipeline     │
            │ • Train classifier   │  │  • Log to Slack/     │
            │ • Track metrics      │  │    Email/Teams       │
            │                      │  │  • Human review      │
            └──────────────────────┘  │    required          │
                        │              │                      │
                        │              └──────────────────────┘
                        │                        │
                        │                   (Manual Investigation)
                        │
                        ▼
            ┌──────────────────────┐
            │ 4️⃣  EVALUATE MODEL   │
            │ ──────────────────   │
            │ • Accuracy/Precision │
            │ • F1-Score           │
            │ • Performance vs old  │
            │ • Latency test       │
            └──────────────────────┘
                        │
                        ▼
            ┌──────────────────────┐
            │ 5️⃣  VERSION MODEL    │
            │ ──────────────────   │
            │ • Save model binary  │
            │ • Tag with commit ID │
            │ • Record metrics     │
            │ • Store in registry  │
            └──────────────────────┘
                        │
                        ▼
            ┌──────────────────────┐
            │ 6️⃣  DEPLOY TO PROD   │
            │ ──────────────────   │
            │ • Push to Render/    │
            │   Railway            │
            │ • Start FastAPI      │
            │ • Expose /predict    │
            │ • Health checks      │
            └──────────────────────┘
                        │
                        ▼

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        PRODUCTION ENVIRONMENT (CONTINUOUS)                         │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                    
                ┌──────────────────────────────────────┐
                │   7️⃣  SERVE PREDICTIONS              │
                │   ────────────────────────────────   │
                │   FastAPI Endpoint:                  │
                │   POST /predict                      │
                │   Response: {prediction, confidence} │
                └──────────────────────────────────────┘
                            │
                            ▼
                ┌──────────────────────────────────────┐
                │  8️⃣  MONITOR PRODUCTION DATA         │
                │  ────────────────────────────────    │
                │  (Continuous - every prediction)     │
                │                                      │
                │  • Log incoming features             │
                │  • Run same quality checks           │
                │  • Track data drift metrics          │
                │  • Store metrics (SQLite/CSV)        │
                └──────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
         QUALITY OK ✅            QUALITY DROP ⚠️
                │                       │
                ▼                       ▼
         ┌────────────┐        ┌──────────────────┐
         │ Continue   │        │ ALERT TRIGGERED  │
         │ Serving    │        │ ─────────────    │
         │ Data      │        │ • Email to team  │
         │ Logged    │        │ • Slack message  │
         │ for       │        │ • Pause retraining
         │ Analytics │        │ • Manual check   │
         └────────────┘        │ • Possible       │
                               │   rollback       │
                               └──────────────────┘
                                        │
                                        ▼
                        ┌──────────────────────────┐
                        │ 9️⃣  MONITORING DASHBOARD │
                        │ ────────────────────────│
                        │ (Streamlit Web App)     │
                        │                          │
                        │ • Quality Score Trends   │
                        │ • Data Drift Plots       │
                        │ • Model Performance      │
                        │ • Alert History          │
                        │ • Data Stats Tables      │
                        └──────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              FEEDBACK & ITERATION                                  │
└─────────────────────────────────────────────────────────────────────────────────────┘

    Daily/Weekly monitoring insights feed back into:
    ✓ Tuning quality thresholds
    ✓ Adding new validation rules
    ✓ Retraining with latest clean data
    ✓ Model performance improvements
    ✓ Alert sensitivity adjustments

```

---

## Component Breakdown

| Component | Responsibility | Tools | Frequency |
|-----------|-----------------|-------|-----------|
| **Data Ingestion** | Fetch/load data | Python requests, pandas | Daily (GitHub Actions) |
| **Quality Validation** | Check data integrity | great-expectations, custom pandas | Before each training |
| **Quality Gate** | Block bad data | if/else logic | Before each training |
| **Model Training** | Build ML model | scikit-learn | Only if quality ≥ threshold |
| **Model Evaluation** | Test performance | sklearn.metrics | After training |
| **Model Registry** | Version & store models | Git + SQLite | After evaluation |
| **Deployment** | Push to production | Render/Railway API | After passing tests |
| **Prediction API** | Serve predictions | FastAPI | Continuous (24/7) |
| **Production Monitoring** | Track data quality live | Python logging + SQLite | Every prediction |
| **Alerting** | Notify team of issues | Email/Slack webhook | When quality drops |
| **Dashboard** | Visualize trends | Streamlit | Continuous (refreshes hourly) |

---

## Data Flow

```
┌─────────────┐
│  Raw Data   │────▶ ┌──────────────┐     ┌────────────┐     ┌──────────┐
│   Source    │      │   Validated  │────▶│  Training  │────▶│  Model   │
│  (API/CSV)  │      │     Data     │     │  Dataset   │     │ Registry │
└─────────────┘      └──────────────┘     └────────────┘     └──────────┘
                                                                    │
                                          ┌─────────────────────────┘
                                          │
                                          ▼
                                  ┌──────────────────┐
                                  │  FastAPI Server  │
                                  │  (Production)    │
                                  └──────────────────┘
                                          │
                          ┌───────────────┼───────────────┐
                          │               │               │
                          ▼               ▼               ▼
                    ┌──────────┐  ┌──────────────┐  ┌──────────┐
                    │Prediction│  │ Metrics Log  │  │ Dashboard│
                    │  API     │  │ (SQLite)     │  │(Streamlit)
                    └──────────┘  └──────────────┘  └──────────┘
```

---

## Key Decision Points

1. **Data Quality Check Fails?**
   - ❌ Send alert, pause training
   - 🔧 Investigation needed before rerun

2. **Model Performance Drops?**
   - Quality gate catches it before deployment
   - Previous model remains in production

3. **Production Data Quality Drops?**
   - Alert team immediately
   - Flag for manual review
   - Consider rolling back model

---

## Interview Talking Points

When explaining this project:

1. **"Why this matters"**: "Bad data leads to bad predictions. I built an automated QA system that validates data before it trains the model."

2. **"Your SDET angle"**: "Just like I write tests to catch bugs before production, I wrote data quality rules to catch bad data before model training."

3. **"End-to-end thinking"**: "I didn't just build a model; I built a complete pipeline from data ingestion through monitoring."

4. **"Reliability focus"**: "The system alerts when something goes wrong, so humans can investigate and fix it—not automated blind faith."

5. **"Scalability ready"**: "The framework is designed so you could add more validation rules or models without major changes."
