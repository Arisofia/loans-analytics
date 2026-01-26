#!/usr/bin/env bash
# Azure OpenAI provider setup script
set -euo pipefail

# 1. Install required Python packages
pip install azure-identity azure-ai-ml azure-core openai python-dotenv

echo "\n---\n"
echo "Add the following to your .env file or CI environment variables:"
echo "AZURE_OPENAI_API_""KEY=REPLACE_WITH_REAL_KEY"
echo "AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/"
echo "AZURE_OPENAI_DEPLOYMENT=your-deployment-name"
echo "AZURE_OPENAI_API_VERSION=2024-02-15-preview"
echo "\n---\n"
echo "To export in your shell (optional):"
echo "export AZURE_OPENAI_API_""KEY=\"REPLACE_WITH_REAL_KEY\""
echo "export AZURE_OPENAI_ENDPOINT=\"https://your-resource-name.openai.azure.com/\""
echo "export AZURE_OPENAI_DEPLOYMENT=\"your-deployment-name\""
echo "export AZURE_OPENAI_API_VERSION=\"2024-02-15-preview\""
echo "\n---\n"
echo "To test connectivity, run the following Python snippet:"
echo 'import os; import openai; openai.api_type = "azure"; openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT"); openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION"); openai.api_key = os.getenv("AZURE_OPENAI_API_KEY"); response = openai.ChatCompletion.create(engine=os.getenv("AZURE_OPENAI_DEPLOYMENT"), messages=[{"role": "user", "content": "Hello from Azure OpenAI!"}]); print(response["choices"][0]["message"]["content"])'
echo "\n---\n"
echo "For CI (GitHub Actions), add to your workflow env block:"
echo "env:"
echo "  AZURE_OPENAI_API_KEY: \\${{ secrets.AZURE_OPENAI_API_KEY }}"
echo "  AZURE_OPENAI_ENDPOINT: \\${{ secrets.AZURE_OPENAI_ENDPOINT }}"
echo "  AZURE_OPENAI_DEPLOYMENT: \\${{ secrets.AZURE_OPENAI_DEPLOYMENT }}"
echo "  AZURE_OPENAI_API_VERSION: 2024-02-15-preview"
