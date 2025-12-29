"""
Load secrets from Azure Key Vault
"""
import os
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_secret_client():
    """Initialize Azure Key Vault client"""
    vault_name = os.getenv("AZURE_KEY_VAULT_NAME", "abaco-capital-kv")
    vault_url = f"https://{vault_name}.vault.azure.net"
    
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    
    if not all([tenant_id, client_id, client_secret]):
        raise ValueError("Missing Azure credentials in .env file")
    
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )
    
    return SecretClient(vault_url=vault_url, credential=credential)

def load_secrets():
    """Load all secrets from Key Vault into environment variables"""
    try:
        client = get_secret_client()
        
        secrets_mapping = {
            "OPENAI-API-KEY": "OPENAI_API_KEY",
            "ANTHROPIC-API-KEY": "ANTHROPIC_API_KEY",
            "HUBSPOT-API-KEY": "HUBSPOT_API_KEY",
            "HUBSPOT-PORTAL-ID": "HUBSPOT_PORTAL_ID"
        }
        
        loaded_secrets = {}
        for vault_secret_name, env_var_name in secrets_mapping.items():
            try:
                secret = client.get_secret(vault_secret_name)
                os.environ[env_var_name] = secret.value
                loaded_secrets[env_var_name] = "✅ Loaded"
                print(f"✅ Loaded {env_var_name}")
            except Exception as e:
                loaded_secrets[env_var_name] = f"❌ Error: {str(e)}"
                print(f"⚠️  Could not load {vault_secret_name}: {str(e)}")
        
        return loaded_secrets
        
    except Exception as e:
        print(f"❌ Failed to connect to Azure Key Vault: {str(e)}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("Loading secrets from Azure Key Vault...")
    print("=" * 60)
    results = load_secrets()
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    for key, status in results.items():
        print(f"  {key}: {status}")
    print("=" * 60)
