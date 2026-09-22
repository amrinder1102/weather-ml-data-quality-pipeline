import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional


def get_current_weather(city_name: str, api_key: str, units: str = "metric") -> Optional[Dict]:
    """Fetch current weather for a single city."""
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city_name, "appid": api_key, "units": units}

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred for {city_name}: {http_err}")
        if response.status_code == 401:
            print("Hint: Check if your API key is valid and activated.")
        elif response.status_code == 404:
            print(f"Hint: The city '{city_name}' could not be found.")
    except Exception as err:
        print(f"An error occurred fetching {city_name}: {err}")
    return None


def get_forecast(city_name: str, api_key: str, units: str = "metric") -> Optional[Dict]:
    """Fetch 5-day forecast (includes hourly data that gives historical-like granularity)."""
    base_url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"q": city_name, "appid": api_key, "units": units}

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred for forecast {city_name}: {http_err}")
    except Exception as err:
        print(f"An error occurred fetching forecast {city_name}: {err}")
    return None


def fetch_weather_for_cities(
    cities: List[str], api_key: str, units: str = "metric", include_forecast: bool = True
) -> List[Dict]:
    """
    Fetch current weather and optionally forecast for multiple cities.
    Returns structured data ready for CSV storage.
    """
    all_data = []
    timestamp = datetime.now(timezone.utc).isoformat()

    for city in cities:
        current = get_current_weather(city, api_key, units)
        if current:
            record = {
                "timestamp": timestamp,
                "date": datetime.fromtimestamp(current["dt"]).strftime("%Y-%m-%d"),
                "time": datetime.fromtimestamp(current["dt"]).strftime("%H:%M:%S"),
                "city": current.get("name", city),
                "country": current.get("sys", {}).get("country", ""),
                "temp_current": current["main"]["temp"],
                "temp_max": current["main"]["temp_max"],
                "temp_min": current["main"]["temp_min"],
                "feels_like": current["main"]["feels_like"],
                "humidity": current["main"]["humidity"],
                "pressure": current["main"]["pressure"],
                "wind_speed": current["wind"]["speed"],
                "clouds": current["clouds"]["all"],
                "weather_condition": current["weather"][0]["main"],
                "weather_description": current["weather"][0]["description"],
            }
            all_data.append(record)
            print(f"✓ Fetched current weather for {current['name']}")

        if include_forecast:
            forecast = get_forecast(city, api_key, units)
            if forecast and "list" in forecast:
                for forecast_point in forecast["list"][:8]:  # First 8 points = 24 hours
                    record = {
                        "timestamp": datetime.fromtimestamp(forecast_point["dt"]).isoformat(),
                        "date": datetime.fromtimestamp(forecast_point["dt"]).strftime("%Y-%m-%d"),
                        "time": datetime.fromtimestamp(forecast_point["dt"]).strftime("%H:%M:%S"),
                        "city": forecast["city"]["name"],
                        "country": forecast["city"]["country"],
                        "temp_current": forecast_point["main"]["temp"],
                        "temp_max": forecast_point["main"]["temp_max"],
                        "temp_min": forecast_point["main"]["temp_min"],
                        "feels_like": forecast_point["main"]["feels_like"],
                        "humidity": forecast_point["main"]["humidity"],
                        "pressure": forecast_point["main"]["pressure"],
                        "wind_speed": forecast_point["wind"]["speed"],
                        "clouds": forecast_point["clouds"]["all"],
                        "weather_condition": forecast_point["weather"][0]["main"],
                        "weather_description": forecast_point["weather"][0]["description"],
                    }
                    all_data.append(record)
                print(f"✓ Fetched 5-day forecast for {forecast['city']['name']}")

    return all_data
