from azure.identity import AzureCliCredential
from azure.keyvault.secrets import SecretClient


class KeyVault:
    def __init__(self):
        key_vault_uri = "https://rmaocr.vault.azure.net/"
        # Authenticate using Azure CLI credentials
        credential = AzureCliCredential()
        self.client = SecretClient(vault_url=key_vault_uri, credential=credential)

    def get_key(self, secret_name):
        # Retrieve a secret
        retrieved_secret = self.client.get_secret(secret_name)
        return retrieved_secret.value


if __name__ == "__main__":
    vault = KeyVault()
    
    key = vault.get_key("SDUGeminiAPI")
    key = vault.get_key("openaikey")