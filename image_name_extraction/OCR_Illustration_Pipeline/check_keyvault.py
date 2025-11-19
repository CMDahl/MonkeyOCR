try:
    import azure.keyvault.secrets
    print("azure.keyvault.secrets is installed")
except ImportError as e:
    print(f"azure.keyvault.secrets is NOT installed: {e}")

try:
    from azure.keyvault.secrets import SecretClient
    print("SecretClient import successful")
except ImportError as e:
    print(f"SecretClient import failed: {e}")
