"""
Agent (Lab style) — Natural language → intent → delegate to MCP tool → formatted response.
Spawns the Weather MCP server (server.py) and calls get_weather(city).
Run: python agent.py [--verbose] [query]
"""

import asyncio
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

WEATHER_KEYWORDS = frozenset({
    "weather", "forecast", "climate", "temperature", "rain", "rainy", "sunny",
    "cold", "hot", "snow", "windy", "cloudy", "storm", "thunder", "humidity", "wind",
})


def detect_intent(query: str) -> str | None:
    if not query or not query.strip():
        return None
    words = {w.rstrip("?.,!") for w in query.strip().lower().split()}
    return "weather" if (words & WEATHER_KEYWORDS) else None


def extract_city(query: str) -> str | None:
    q = query.strip()
    if not q:
        return None
    for pattern in [
        r"\bin\s+(.+?)(?:\?|$)",
        r"\bfor\s+(.+?)(?:\?|$)",
        r"\bat\s+(.+?)(?:\?|$)",
        r"^(.+?)\s+weather(?:\?|$)",
        r"^(.+?)\s+forecast(?:\?|$)",
    ]:
        m = re.search(pattern, q, re.I)
        if m:
            return m.group(1).strip().rstrip("?.,")
    parts = re.split(r"\s+(?:is|the|a|an)\s+", q, flags=re.I)
    if len(parts) >= 2:
        last = parts[-1].strip().rstrip("?")
        if last and len(last) > 1:
            return last
    return None


def format_response(tool_output: str, user_query: str = "") -> str:
    try:
        data = json.loads(tool_output)
    except json.JSONDecodeError:
        return "I received an invalid response from the weather service."

    if isinstance(data, dict) and "error" in data:
        return data["error"]

    resolved = data.get("resolved_location", data.get("city", ""))
    period = data.get("period", "")
    temp = data.get("temperature", "")
    unit = data.get("temperature_unit", "F")
    short = data.get("short_forecast", "")
    wind_speed = data.get("wind_speed", "")
    wind_dir = data.get("wind_direction", "")
    pop = data.get("probability_of_precipitation")

    if "rain" in (user_query or "").lower():
        if pop is not None and pop > 0:
            msg = f"There's a {pop}% chance of precipitation {period.lower()} in {resolved}."
        elif pop is not None and pop == 0:
            msg = f"No precipitation expected {period.lower()} in {resolved}."
        else:
            msg = f"{period} in {resolved}: {short}."
        if temp != "":
            msg += f" Temperature around {temp}°{unit}."
        if wind_dir or wind_speed:
            msg += " Wind " + f"{wind_dir} {wind_speed}".strip() + "."
        return msg

    temp_str = f"{temp}°{unit}" if temp != "" else "N/A"
    wind_str = " ".join(p for p in [wind_dir, wind_speed] if p) or ""
    if wind_str:
        return f"Weather for {resolved}: {period} it will be {temp_str} with {short}. Wind {wind_str}."
    return f"Weather for {resolved}: {period} it will be {temp_str} with {short}."


async def handle_query(session: ClientSession, query: str, verbose: bool = False) -> str:
    async def call_tool(name: str, arguments: dict) -> str:
        result = await session.call_tool(name, arguments)
        if result.structuredContent is not None:
            return json.dumps(result.structuredContent)
        if result.content:
            for block in result.content:
                text = getattr(block, "text", None) or (block.get("text") if isinstance(block, dict) else None)
                if text:
                    return text
        return "{}"

    if not query or not query.strip():
        return "Please ask a question, e.g. \"What is the weather in Seattle?\""

    intent = detect_intent(query)
    if verbose:
        print(f"  [Intent] {intent or '(unsupported)'}")
    if intent != "weather":
        return "I currently support weather-related queries only."

    city = extract_city(query)
    if verbose:
        print(f"  [City] {city or '(none)'}")
    if not city:
        return "Please provide a city name, e.g. \"What is the weather in Seattle?\""

    stopwords = {"the", "a", "an", "in", "for", "at", "what", "is", "it"}
    if set(city.lower().split()) <= (WEATHER_KEYWORDS | stopwords):
        return "Please provide a city name, e.g. \"What is the weather in Seattle?\""

    if verbose:
        print(f"  [Tool] get_weather(city={city!r})")

    tool_out = await call_tool("get_weather", {"city": city})
    return format_response(tool_out, query)


async def main() -> None:
    args = sys.argv[1:]
    verbose = "--verbose" in args or "-v" in args
    for flag in ("--verbose", "-v"):
        if flag in args:
            args.remove(flag)

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["server.py"],
        env=os.environ,
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            if args:
                query = " ".join(args)
                if verbose:
                    print("--- Processing ---")
                out = await handle_query(session, query, verbose=verbose)
                if verbose:
                    print("--- Response ---")
                print(out)
                return

            print("Weather Agent (lab style). Ask about weather or type 'quit'.")
            if verbose:
                print("Verbose: intent, city, and tool calls will be shown.\n")
            while True:
                try:
                    query = input("You: ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                if not query:
                    continue
                if query.lower() in ("quit", "exit", "q"):
                    break
                if verbose:
                    print("--- Processing ---")
                print("Agent:", await handle_query(session, query, verbose=verbose), "\n")


if __name__ == "__main__":
    asyncio.run(main())
