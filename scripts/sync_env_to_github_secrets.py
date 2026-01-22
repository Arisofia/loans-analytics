import os
import re
import subprocess

from dotenv import dotenv_values

# Load .env file
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
secrets = dotenv_values(env_path)

SECRET_NAME_RE = re.compile(r"^[A-Za-z0-9_]+$")


def _validate_secret_name(secret_name: str) -> None:
    if not SECRET_NAME_RE.fullmatch(secret_name):
        raise ValueError(f"Invalid GitHub secret name: {secret_name}")


def set_github_secret(secret_name, secret_value, repo):
    _validate_secret_name(secret_name)
    cmd = ["gh", "secret", "set", secret_name, "--repo", repo]
    subprocess.run(cmd, input=secret_value.encode(), check=True, shell=False)


if __name__ == "__main__":
    repo = "Abaco-Technol/abaco-loans-analytics"  # Update if needed
    for key, value in secrets.items():
        if value and not value.startswith("${"):
            set_github_secret(key, value, repo)
