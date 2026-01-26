"""Entrypoint wrapper for python -m src.abaco_pipeline.main."""

from src.abaco_pipeline.main import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
