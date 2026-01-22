"""Entrypoint wrapper for python -m src.abaco_pipeline.main."""

from src.abaco_pipeline.main import main

if __name__ == "__main__":
    raise SystemExit(main())
