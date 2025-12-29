import os
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv

load_dotenv()

def get_secret_client():
    vault_name = os.getenv("AZURE_KEY_VAULT_NAME", "abaco-capital-kv")
    vault_url = f"https://{vault_name}.vault.azure.net"
    
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    
    if not all([tenant_id, client_id, client_secret]):
        raise ValueError("Missing Azure credentials")
    
    credential = ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
    return SecretClient(vault_url=vault_url, credential=credential)

def load_secrets():
    try:
        client = get_secret_client()
        secrets = {"OPENAI-API-KEY": "OPENAI_API_KEY", "ANTHROPIC-API-KEY": "ANTHROPIC_API_KEY", "HUBSPOT-API-KEY": "HUBSPOT_API_KEY", "HUBSPOT-PORTAL-ID": "HUBSPOT_PORTAL_ID"}
        results = {}
        for vault_name, env_name in secrets.items():
            try:
                secret = client.get_secret(vault_name)
                os.environ[env_name] = secret.value
                results[env_name] = "✅"
                print(f"✅ {env_name}")
            except Exception as e:
                results[env_name] = f"❌ {str(e)}"
                print(f"❌ {vault_name}: {str(e)}")
        return results
    except Exception as e:
        print(f"❌ Key Vault failed: {str(e)}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("Loading Azure Key Vault secrets...")
    print("=" * 60)
    results = load_secrets()
    print("\n" + "=" * 60)
    for key, status in results.items():
        print(f"  {key}: {status}")
    print("=" * 60)
