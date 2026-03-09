import asyncio
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python app.py server | agent [query] [--verbose]")
        sys.exit(1)
    mode = sys.argv[1].lower()
    if mode == "server":
        from server import mcp
        mcp.run()
    elif mode == "agent":
        sys.argv = ["agent.py"] + sys.argv[2:]
        from agent import main as agent_main
        asyncio.run(agent_main())
    else:
        print("Usage: python app.py server | agent [query] [--verbose]")
        sys.exit(1)


if __name__ == "__main__":
    main()
