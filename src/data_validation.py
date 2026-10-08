import pandas as pd
import json
from datetime import datetime, timezone
import os


def validate_data(csv_path: str, output_processed: str = None) -> tuple:
    """Run 5 basic quality checks on weather data. Returns (quality_score, report, proceed)."""
    df = pd.read_csv(csv_path)
    results = {}
    checks_passed = 0

    # Check 1: Schema - required columns exist
    required = ["date", "city", "temp_max", "temp_min", "humidity", "pressure", "wind_speed"]
    missing = set(required) - set(df.columns)
    if missing:
        results["schema"] = f"FAILED: Missing columns {missing}"
    else:
        results["schema"] = "PASSED"
        checks_passed += 1

    # Check 2: Missing values
    missing_issues = []
    if df["temp_max"].isna().sum() > 0:
        missing_issues.append(f"temp_max: {df['temp_max'].isna().sum()} missing")
    for col in ["humidity", "pressure", "wind_speed"]:
        pct = df[col].isna().sum() / len(df)
        if pct > 0.05:  # 5% tolerance
            missing_issues.append(f"{col}: {pct*100:.1f}% missing")

    if missing_issues:
        results["missing_values"] = f"FAILED: {', '.join(missing_issues)}"
    else:
        results["missing_values"] = "PASSED"
        checks_passed += 1

    # Check 3: Bounds - values within physical limits
    bounds_issues = []
    for col, (min_val, max_val) in [
        ("temp_max", (-50, 70)),
        ("temp_min", (-50, 70)),
        ("humidity", (0, 100)),
        ("pressure", (900, 1100)),
        ("wind_speed", (0, 100)),
    ]:
        out_of_bounds = ((df[col] < min_val) | (df[col] > max_val)).sum()
        if out_of_bounds > 0:
            bounds_issues.append(f"{col}: {out_of_bounds} out of bounds")

    if bounds_issues:
        results["bounds"] = f"FAILED: {', '.join(bounds_issues)}"
    else:
        results["bounds"] = "PASSED"
        checks_passed += 1

    # Check 4: Consistency - temp_min <= temp_max
    violations = (df["temp_min"] > df["temp_max"]).sum()
    if violations > 0:
        results["consistency"] = f"FAILED: {violations} rows have temp_min > temp_max"
    else:
        results["consistency"] = "PASSED"
        checks_passed += 1

    # Check 5: Distribution - temperature variation exists
    temp_std = df["temp_max"].std()
    if temp_std < 0.5:
        results["distribution"] = f"FAILED: Low variance (std={temp_std:.2f})"
    else:
        results["distribution"] = "PASSED"
        checks_passed += 1

    # Generate score
    quality_score = (checks_passed / 5) * 100
    proceed = quality_score >= 80
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "quality_score": round(quality_score, 1),
        "status": "PASSED" if proceed else "FAILED",
        "checks": results,
        "records": len(df),
    }

    # If validation passed and output path provided, process data
    processed_df = None
    if proceed and output_processed:
        processed_df = _process_data(df)
        os.makedirs(os.path.dirname(output_processed), exist_ok=True)
        processed_df.to_csv(output_processed, index=False)
        report["processed_file"] = output_processed
        report["processed_records"] = len(processed_df)

    return quality_score, report, proceed


def save_report(report: dict, output_path: str) -> None:
    """Save validation report as JSON."""
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)


def validate_data_db(weather_data: list) -> tuple:
    """
    Validate weather data from API and return processed data.
    Returns (quality_score, report, proceed, processed_data_list)
    """
    df = pd.DataFrame(weather_data)
    results = {}
    checks_passed = 0

    required = ["date", "city", "temp_max", "temp_min", "humidity", "pressure", "wind_speed"]
    missing = set(required) - set(df.columns)
    if missing:
        results["schema"] = f"FAILED: Missing columns {missing}"
    else:
        results["schema"] = "PASSED"
        checks_passed += 1

    missing_issues = []
    if df["temp_max"].isna().sum() > 0:
        missing_issues.append(f"temp_max: {df['temp_max'].isna().sum()} missing")
    for col in ["humidity", "pressure", "wind_speed"]:
        pct = df[col].isna().sum() / len(df)
        if pct > 0.05:
            missing_issues.append(f"{col}: {pct*100:.1f}% missing")

    if missing_issues:
        results["missing_values"] = f"FAILED: {', '.join(missing_issues)}"
    else:
        results["missing_values"] = "PASSED"
        checks_passed += 1

    bounds_issues = []
    for col, (min_val, max_val) in [
        ("temp_max", (-50, 70)),
        ("temp_min", (-50, 70)),
        ("humidity", (0, 100)),
        ("pressure", (900, 1100)),
        ("wind_speed", (0, 100)),
    ]:
        out_of_bounds = ((df[col] < min_val) | (df[col] > max_val)).sum()
        if out_of_bounds > 0:
            bounds_issues.append(f"{col}: {out_of_bounds} out of bounds")

    if bounds_issues:
        results["bounds"] = f"FAILED: {', '.join(bounds_issues)}"
    else:
        results["bounds"] = "PASSED"
        checks_passed += 1

    violations = (df["temp_min"] > df["temp_max"]).sum()
    if violations > 0:
        results["consistency"] = f"FAILED: {violations} rows have temp_min > temp_max"
    else:
        results["consistency"] = "PASSED"
        checks_passed += 1

    temp_std = df["temp_max"].std()
    if temp_std < 0.5:
        results["distribution"] = f"FAILED: Low variance (std={temp_std:.2f})"
    else:
        results["distribution"] = "PASSED"
        checks_passed += 1

    quality_score = (checks_passed / 5) * 100
    proceed = quality_score >= 80

    processed_data = []
    if proceed:
        processed_df = _process_data(df)
        processed_data = processed_df.to_dict("records")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "quality_score": round(quality_score, 1),
        "status": "PASSED" if proceed else "FAILED",
        "checks": results,
        "records": len(df),
        "processed_records": len(processed_data) if proceed else 0,
    }

    return quality_score, report, proceed, processed_data


def _process_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and engineer features for training."""
    df = df.copy()

    # Convert date to datetime
    df["date"] = pd.to_datetime(df["date"])

    # Sort by city and date
    df = df.sort_values(by=["city", "date"]).reset_index(drop=True)

    # Convert numeric columns
    numeric_cols = ["temp_max", "temp_min", "humidity", "pressure", "wind_speed"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fill missing values with city mean (only numeric columns)
    for col in numeric_cols:
        df[col] = df.groupby("city")[col].transform(lambda x: x.fillna(x.mean()))

    # Create temporal features
    df["month"] = df["date"].dt.month
    df["day_of_week"] = df["date"].dt.dayofweek

    # Create lagged features (previous day's values)
    df["temp_max_prev"] = df.groupby("city")["temp_max"].shift(1)
    df["temp_min_prev"] = df.groupby("city")["temp_min"].shift(1)
    df["humidity_prev"] = df.groupby("city")["humidity"].shift(1)
    df["pressure_prev"] = df.groupby("city")["pressure"].shift(1)
    df["wind_speed_prev"] = df.groupby("city")["wind_speed"].shift(1)

    # Drop rows with NaN from lagged features (first row per city)
    df = df.dropna()

    # Select final columns
    final_cols = [
        "date",
        "city",
        "temp_max",
        "temp_min",
        "humidity",
        "pressure",
        "wind_speed",
        "month",
        "day_of_week",
        "temp_max_prev",
        "temp_min_prev",
        "humidity_prev",
        "pressure_prev",
        "wind_speed_prev",
    ]
    return df[final_cols]
