"""
Weather MCP Server (Lab style) — FastMCP, one tool: get_weather(city).
Uses https://api.weather.gov/
Run: python server.py
"""

import json
import urllib.request
import urllib.error

from fastmcp import FastMCP

mcp = FastMCP("Weather Server")

NWS_USER_AGENT = "WeatherAgentLabs/1.0 (educational; api.weather.gov)"

CITIES = {
    "seattle": (47.6062, -122.3321),
    "boston": (42.3601, -71.0589),
    "chicago": (41.8781, -87.6298),
    "new york": (40.7128, -74.0060),
    "san francisco": (37.7749, -122.4194),
    "los angeles": (34.0522, -118.2437),
    "denver": (39.7392, -104.9903),
    "miami": (25.7617, -80.1918),
}


def _geocode(city: str) -> tuple[float, float, str] | None:
    """Resolve city to (lat, lon, display_name). Static map first, then Nominatim."""
    c = city.strip()
    if not c:
        return None
    key = c.lower().replace(" ", " ")
    if key in CITIES:
        lat, lon = CITIES[key]
        display = " ".join(p.capitalize() for p in c.split())
        return (lat, lon, display)
    try:
        import requests
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": c, "format": "json", "limit": 1},
            headers={"User-Agent": NWS_USER_AGENT},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        first = data[0]
        return (
            float(first["lat"]),
            float(first["lon"]),
            first.get("display_name", c),
        )
    except Exception:
        return None


def _nws_request(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": NWS_USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


@mcp.tool()
def get_weather(city: str) -> dict:
    """Get current weather for a city using the National Weather Service (api.weather.gov)."""
    if not city or not str(city).strip():
        return {"error": "Please provide a city name, e.g. \"What is the weather in Seattle?\""}

    city_str = str(city).strip()
    geo = _geocode(city_str)
    if not geo:
        return {"error": "I couldn't resolve that city name."}

    lat, lon, display_name = geo
    lat, lon = round(lat, 4), round(lon, 4)

    try:
        points = _nws_request(f"https://api.weather.gov/points/{lat},{lon}")
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return {"error": "Weather service request was rejected. Try again later."}
        return {"error": "Weather service is temporarily unavailable."}
    except Exception:
        return {"error": "Weather service is temporarily unavailable."}

    props = points.get("properties") or {}
    forecast_url = props.get("forecast")
    if not forecast_url:
        return {"error": "Weather service is temporarily unavailable."}

    relative = (props.get("relativeLocation") or {}).get("properties") or {}
    resolved = (
        f"{relative.get('city', '')}, {relative.get('state', '')}".strip(", ")
        or display_name or city_str
    )

    try:
        forecast_data = _nws_request(forecast_url)
    except Exception:
        return {"error": "Weather service is temporarily unavailable."}

    periods = (forecast_data.get("properties") or {}).get("periods") or []
    if not periods:
        return {"error": "No forecast data available for that location."}

    first = periods[0]
    temp = first.get("temperature")
    if temp is None:
        temp = 0
    return {
        "city": city_str,
        "resolved_location": resolved.strip(),
        "period": first.get("name", "Current"),
        "temperature": int(temp),
        "temperature_unit": first.get("temperatureUnit", "F"),
        "wind_speed": first.get("windSpeed") or "",
        "wind_direction": first.get("windDirection") or "",
        "short_forecast": first.get("shortForecast") or "",
        "detailed_forecast": first.get("detailedForecast") or "",
        "probability_of_precipitation": _parse_pop(first.get("probabilityOfPrecipitation")),
    }


def _parse_pop(v) -> int | None:
    if v is None:
        return None
    if isinstance(v, dict):
        v = v.get("value")
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    mcp.run()
