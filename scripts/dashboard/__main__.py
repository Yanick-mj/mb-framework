"""Launch the mb-dashboard server.

Usage: python3 -m scripts.dashboard [--port PORT]
"""
import importlib.util
import sys

REQUIRED = ["fastapi", "uvicorn", "jinja2"]


def _check_deps() -> list[str]:
    return [pkg for pkg in REQUIRED if importlib.util.find_spec(pkg) is None]


def main() -> None:
    missing = _check_deps()
    if missing:
        print(
            f"Missing dependencies: {', '.join(missing)}\n"
            f"\nFix: pip install {' '.join(missing)}\n",
            file=sys.stderr,
        )
        sys.exit(2)

    import uvicorn

    port = 5111
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        port = int(sys.argv[idx + 1])

    print(f"mb-dashboard → http://localhost:{port}")
    uvicorn.run("scripts.dashboard.server:app", host="127.0.0.1", port=port, reload=True)


if __name__ == "__main__":
    main()
