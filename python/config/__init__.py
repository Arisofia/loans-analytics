"""Configuration and setup utilities."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class EnvironmentSettings(BaseModel):
    """Environment-specific settings for data path resolution."""
    
    environment: Literal["dev", "staging", "prod"] = Field(
        default="dev",
        description="Current environment"
    )
    prod_data_path: str = Field(
        default="/data",
        description="Production data path"
    )
    
    def get_data_root(self) -> Path:
        """Get the root data directory based on environment."""
        if self.environment == "prod":
            return Path(self.prod_data_path)
        elif self.environment == "staging":
            return Path("./data/staging")
        else:  # dev
            return Path("./data/dev")
    
    def get_test_data_root(self) -> Path:
        """Get test data root. Raises error in production."""
        if self.environment == "prod":
            raise RuntimeError("Test data is not available in production environment")
        return Path("./tests/data")


class Settings(BaseModel):
    """Application settings."""
    
    environment: EnvironmentSettings = Field(default_factory=EnvironmentSettings)


# Global settings instance
settings = Settings()

__all__ = ["EnvironmentSettings", "Settings", "settings"]
