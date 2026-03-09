# Weather Agent - Agentic AI with Weather MCP

**Assignment:** Build an Agentic AI using Weather MCP — one MCP tool (api.weather.gov) and one agent that accepts natural language, delegates to the tool, and returns a formatted response.

---

## What Is Implemented

### 1. MCP Tool — Weather Information Tool

- **Tool name:** `get_weather(city)`
- **API:** https://api.weather.gov/
- **Input:** City name
- **Behaviour:** Resolves city to coordinates, calls NWS points and forecast endpoints, parses the response, and returns structured weather data (temperature, forecast, wind, precipitation chance, etc.) or a clear error message.

### 2. Agent

- **Input:** Natural language (e.g. “What is the weather in Seattle?”)
- **Intent detection:** Weather-related keywords → delegate to the Weather MCP Tool; other queries → “I currently support weather-related queries only.”
- **Delegation:** Exactly one tool per query; city is extracted from the query and passed as the `city` parameter.
- **Response:** Tool output is converted into a short, user-friendly message (and rain-focused when the user asks about rain).

---

## Requirements

- Python 3.10+
- Dependencies: `fastmcp`, `mcp`, `requests` (see `requirements.txt`)

---

## Setup

```bash
cd nagp-mcp-ai-weather-agent
pip install -r requirements.txt
```

---

## How to Run

**Run the agent** (recommended — starts the MCP server as a subprocess and runs the agent):

```bash
python agent.py
```

One-shot query:

```bash
python agent.py "What is the weather in Seattle?"
```

With verbose output (intent, city, tool call):

```bash
python agent.py --verbose "Will it rain in Boston?"
```

**Run the MCP server only** (e.g. for testing or another client):

```bash
python server.py
```

---

## Example Interactions

| User query | Example behaviour |
|------------|-------------------|
| “What is the weather in Seattle?” | Weather summary for Seattle (e.g. temperature, short forecast, wind). |
| “Will it rain in Boston?” | Rain-focused answer with precipitation chance when available. |
| “Tell me a joke” | “I currently support weather-related queries only.” |
| “What is the weather?” (no city) | “Please provide a city name, e.g. ‘What is the weather in Seattle?’” |

---

## Project Layout

| File | Role |
|------|------|
| `server.py` | FastMCP MCP server; exposes `get_weather(city)`; geocoding and api.weather.gov logic in this file. |
| `agent.py` | Agent: connects to the server via stdio, intent detection, city extraction, single-tool delegation, response formatting. |
| `app.py` | Entrypoint: `python app.py server` or `python app.py agent [query] [--verbose]`. |
| `requirements.txt` | Python dependencies. |

