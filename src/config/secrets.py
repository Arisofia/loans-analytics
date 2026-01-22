import os

class SecretsManager:
    def get(self, key: str, default=None):
        return os.getenv(key, default)

def get_secrets_manager():
    return SecretsManager()
