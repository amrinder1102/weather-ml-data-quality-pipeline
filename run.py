from src.fetchData import fetch_weather_for_cities
from src.data_validation import validate_data, save_report
import csv
from datetime import datetime, timezone

API_KEY = "51e66d293f315eb6295deed2003c5082"
CITIES = ["London", "New York", "Tokyo", "Sydney"]

date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
raw_file = f"data/raw/weather_raw_{date_str}.csv"
processed_file = "data/processed/weather_processed.csv"
report_file = f"data/validation_logs/quality_report_{date_str}.json"

# Step 1: Fetch data
print("=== FETCHING DATA ===")
weather_data = fetch_weather_for_cities(CITIES, API_KEY, include_forecast=True)

if weather_data:
    with open(raw_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=weather_data[0].keys())
        writer.writeheader()
        writer.writerows(weather_data)
    print(f"✓ Raw data saved to {raw_file}")
else:
    print("✗ No weather data fetched.")
    exit(1)

# Step 2: Validate & Process
print("\n=== VALIDATING DATA ===")
quality_score, report, proceed = validate_data(raw_file, processed_file)

print(f"Quality Score: {report['quality_score']}%")
print(f"Status: {report['status']}")

if proceed:
    print(f"✓ Validation PASSED - Processing data...")
    print(f"✓ Processed data saved to {processed_file}")
    print(f"✓ Processed records: {report['processed_records']}")
else:
    print(f"✗ Validation FAILED - Quality score < 80%")
    print("Pipeline stopped. Check issues:")
    for check, result in report["checks"].items():
        print(f"  - {check}: {result}")

save_report(report, report_file)
print(f"✓ Report saved to {report_file}")
