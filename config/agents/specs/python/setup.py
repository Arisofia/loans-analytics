# Fintech Factory Python Package Setup
from setuptools import setup, find_packages

setup(
    name="fintech-factory",
    version="1.0.0",
    description="Agentic fintech ecosystem with Vibe Solutioning",
    author="Abaco Technologies",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "requests>=2.26.0",
        "pydantic>=1.8.0",
        "python-dotenv>=0.19.0",
        "sqlalchemy>=1.4.0",
        "psycopg2-binary>=2.9.0",
        "google-cloud-bigquery>=2.30.0",
        "slack-sdk>=3.19.0",
        "notion-client>=2.0.0",
        "aiohttp>=3.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2.0",
            "pytest-cov>=2.12.0",
            "black>=21.6b0",
            "flake8>=3.9.0",
            "mypy>=0.910",
        ],
    },
)
