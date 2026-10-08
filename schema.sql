-- Weather ML Pipeline Database Schema

-- Table 1: Raw weather data (ingested from API)
CREATE TABLE IF NOT EXISTS raw_weather (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(50),
    temp_current FLOAT,
    temp_max FLOAT,
    temp_min FLOAT,
    feels_like FLOAT,
    humidity INT,
    pressure INT,
    wind_speed FLOAT,
    clouds INT,
    weather_condition VARCHAR(50),
    weather_description VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: Processed/validated weather data
CREATE TABLE IF NOT EXISTS processed_weather (
    id SERIAL PRIMARY KEY,
    raw_weather_id INT NOT NULL REFERENCES raw_weather(id),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    date DATE NOT NULL,
    city VARCHAR(100) NOT NULL,
    temp_current FLOAT,
    temp_max FLOAT,
    temp_min FLOAT,
    humidity INT,
    pressure INT,
    wind_speed FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table 3: Quality validation reports
CREATE TABLE IF NOT EXISTS quality_reports (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) UNIQUE NOT NULL,  -- UUID or timestamp-based ID
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    quality_score FLOAT NOT NULL,
    status VARCHAR(20) NOT NULL,  -- "PASSED" or "FAILED"
    total_records INT NOT NULL,
    processed_records INT,
    checks JSONB,  -- Store all 5 checks as JSON
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_raw_weather_city ON raw_weather(city);
CREATE INDEX IF NOT EXISTS idx_raw_weather_date ON raw_weather(date);
CREATE INDEX IF NOT EXISTS idx_processed_weather_city ON processed_weather(city);
CREATE INDEX IF NOT EXISTS idx_quality_reports_timestamp ON quality_reports(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_quality_reports_status ON quality_reports(status);
