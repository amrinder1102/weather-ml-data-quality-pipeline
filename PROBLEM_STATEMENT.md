# ML Data Quality Monitoring Pipeline
## Problem Statement

### 🎯 Problem
Machine Learning models in production fail silently when data quality degrades. Teams often discover issues only after models have made bad predictions, leading to:
- Inaccurate predictions affecting business decisions
- Wasted computational resources training on bad data
- No visibility into when/why models start failing
- Lack of automated safeguards before deploying new models

### 💡 Solution
Build an **automated Data Quality Monitoring Pipeline** that acts as a quality gate for ML workflows. The system ensures data meets quality standards BEFORE training, and monitors for drift AFTER deployment.

### 📊 What You're Building

A complete MLOps pipeline that:

1. **Fetches Data** → Pulls data from a public source (e.g., weather API, stock data, UCI dataset)
2. **Validates Quality** → Runs automated data quality checks:
   - Schema validation (correct column types, no missing columns)
   - Missing value detection (flagged if % missing > threshold)
   - Statistical anomalies (outliers, distribution shifts)
   - Business logic rules (e.g., temperature can't be < -50°C or > 70°C)
3. **Quality Gate** → Only proceeds if quality score ≥ threshold; otherwise alerts
4. **Trains Model** (if data passes) → Builds a simple predictive model
5. **Deploys** → Pushes model to production API
6. **Monitors Production** → Tracks if incoming prediction data meets same quality standards
7. **Alerts** → Sends notifications if data quality drops in production
8. **Reports** → Dashboard showing quality trends over time

### 🔧 Tech Stack
- **Language:** Python
- **Data Validation:** pandas, great-expectations (or custom validators)
- **ML Model:** scikit-learn (simple regressor or classifier)
- **Deployment:** FastAPI + Render/Railway (free tier)
- **Orchestration:** GitHub Actions (runs on schedule)
- **Monitoring Dashboard:** Streamlit (free deployment)
- **Storage:** GitHub (versioning) + simple SQLite for metrics

### 📈 Success Criteria

**By the end of this project, you'll have:**
- ✅ Automated pipeline running on a schedule (GitHub Actions)
- ✅ Data quality validation rules implemented
- ✅ Quality gates preventing bad model training
- ✅ Deployed model serving predictions via API
- ✅ Monitoring dashboard tracking quality over time
- ✅ Alert system for quality degradation
- ✅ Complete GitHub repo with clear documentation
- ✅ Live demo you can show in interviews

### 🎓 What This Demonstrates

**For your SDET → MLOps transition:**
- You understand **quality assurance** as a first-class concern in ML (not an afterthought)
- You can **automate testing** for data (similar to your testing background)
- You understand the **full ML lifecycle** (not just model building)
- You can **write reliable automation** with proper error handling and alerts
- You think like an **engineer** solving operational problems, not just a data scientist

### 🏗️ Project Scope (1-2 weeks)
- Week 1: Data pipeline + quality checks + basic model training
- Week 2: Deployment, monitoring dashboard, GitHub Actions automation, documentation

---

**Next Step:** Review the workflow diagram to see how all pieces connect.
