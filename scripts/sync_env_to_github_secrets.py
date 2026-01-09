import os
import subprocess
from dotenv import dotenv_values

# Load .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
secrets = dotenv_values(env_path)

def set_github_secret(secret_name, secret_value, repo):
    cmd = [
        'gh', 'secret', 'set', secret_name,
        '--repo', repo
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    proc.communicate(input=secret_value.encode())
    proc.wait()
    print("Set GitHub secret.")

if __name__ == "__main__":
    repo = "Abaco-Technol/abaco-loans-analytics"  # Update if needed
    for key, value in secrets.items():
        if value and not value.startswith('${'):
            set_github_secret(key, value, repo)
