import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import requests
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load bearer token from .env
load_dotenv()
BEARER_TOKEN = os.getenv("SPOTIFY_BEARER_TOKEN")

# Define output directory
DATA_DIR = Path("weekly_data")
DATA_DIR.mkdir(exist_ok=True)


def get_latest_thursday() -> str:
    """Return the most recent Thursday date as a string."""
    today = datetime.today()
    offset = (today.weekday() - 3) % 7  # Thursday is weekday 3
    latest_thursday = today - timedelta(days=offset)
    return latest_thursday.strftime("%Y-%m-%d")


def fetch_weekly_charts(week_date: str):
    """
    Fetch Spotify Charts for a given week and save to a JSON file.
    
    Args:
        week_date (str): Date string in YYYY-MM-DD format.
    """
    if not BEARER_TOKEN:
        logger.error("Bearer token not found. Please run the login script first.")
        return

    logger.info(f"Fetching Spotify Charts for week ending: {week_date}")

    country_codes = [
        "GLOBAL", "AR", "AU", "AT", "BY", "BE", "BO", "BR", "BG", "CA", "CL", "CO", "CR", "CY", "CZ", "DK",
        "DO", "EC", "EG", "SV", "EE", "FI", "FR", "DE", "GR", "GT", "HN", "HK", "HU", "IS", "IN", "ID", "IE",
        "IL", "IT", "JP", "KZ", "LV", "LT", "LU", "MY", "MX", "MA", "NL", "NZ", "NI", "NG", "NO", "PK", "PA",
        "PY", "PE", "PH", "PL", "PT", "RO", "SA", "SG", "SK", "ZA", "KR", "ES", "SE", "CH", "TW", "TH", "TR",
        "AE", "UA", "GB", "UY", "US", "VE", "VN"
    ]

    all_chart_data = []

    for country in country_codes:
        logger.info(f"Fetching chart for {country}...")

        url = f"https://charts-spotify-com-service.spotify.com/auth/v0/charts/regional-{country.lower()}-weekly/{week_date}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "Origin": "https://charts.spotify.com",
            "Referer": "https://charts.spotify.com",
            "User-Agent": "Mozilla/5.0"
        }

        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 401:
                logger.error("401 Unauthorized — Bearer token may be expired.")
                return

            elif response.status_code == 200:
                data = response.json()
                entries = data.get("entries", [])

                for entry in entries:
                    chart = {
                        "week_id": week_date,
                        "country": country,
                        "rank": entry["chartEntryData"]["currentRank"],
                        "streams": entry["chartEntryData"]["rankingMetric"]["value"],
                        "track_id": entry["trackMetadata"]["trackUri"].split(":")[-1],
                        "track_name": entry["trackMetadata"]["trackName"],
                        "artist_names": [artist["name"] for artist in entry["trackMetadata"]["artists"]],
                    }
                    all_chart_data.append(chart)

                logger.info(f"Fetched {len(entries)} tracks for {country}")
            else:
                logger.warning(f"Failed to fetch data for {country} (Status: {response.status_code})")

        except Exception as e:
            logger.exception(f"Error while fetching data for {country}: {e}")

    output_path = DATA_DIR / f"weekly_charts_{week_date}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chart_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved weekly data to {output_path}")


if __name__ == "__main__":
    latest_thursday = get_latest_thursday()
    fetch_weekly_charts(latest_thursday)
