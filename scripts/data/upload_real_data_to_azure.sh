#!/bin/bash
set -e

echo "🚀 Uploading Abaco Real Data to Azure..."

# Configuration
RESOURCE_GROUP="abaco-rg"
STORAGE_ACCOUNT="abacodata202602"
LOCATION="canadacentral"

# Files to upload
FILES=(
	"/Users/jenineferderas/Downloads/Abaco - Loan Tape_Historic Real Payment_Table (3).csv"
	"/Users/jenineferderas/Downloads/Abaco - Loan Tape_Collateral_Table (3).csv"
	"/Users/jenineferderas/Downloads/Abaco - Loan Tape_Customer Data_Table (3).csv"
	"/Users/jenineferderas/Downloads/Abaco - Loan Tape_Payment Schedule_Table (3).csv"
	"/Users/jenineferderas/Downloads/Abaco - Loan Tape_Loan Data_Table (3).csv"
)

# Create storage account if not exists
echo "📦 Creating Azure Storage..."
if ! az storage account show --name "${STORAGE_ACCOUNT}" --resource-group "${RESOURCE_GROUP}" &>/dev/null; then
	az storage account create \
		--name "${STORAGE_ACCOUNT}" \
		--resource-group "${RESOURCE_GROUP}" \
		--location "${LOCATION}" \
		--sku Standard_LRS \
		--output none
	echo "✅ Storage account created"
else
	echo "✅ Storage account exists"
fi

# Get storage key
STORAGE_KEY=$(az storage account keys list \
	--account-name "${STORAGE_ACCOUNT}" \
	--resource-group "${RESOURCE_GROUP}" \
	--query "[0].value" -o tsv)

# Create container
echo "📁 Creating container..."
az storage container create \
	--name loan-data \
	--account-name "${STORAGE_ACCOUNT}" \
	--account-key "${STORAGE_KEY}" \
	--output none 2>/dev/null || true

echo "✅ Container ready"

# Upload each file
echo ""
echo "⬆️  Uploading files..."
for FILE in "${FILES[@]}"; do
	if [[ -f "${FILE}" ]]; then
		BASENAME=$(basename "${FILE}")
		echo "  📄 Uploading ${BASENAME}"
		az storage blob upload \
			--account-name "${STORAGE_ACCOUNT}" \
			--account-key "${STORAGE_KEY}" \
			--container-name loan-data \
			--file "${FILE}" \
			--name "${BASENAME}" \
			--overwrite \
			--output none
		echo "     ✅ Done"
	else
		echo "  ⚠️  File not fou${d: $}FILE"
	fi
done

echo ""
echo "✅ All files uploaded to Azure!"
echo ""
echo "📊 View in Azure Portal:"
echo "https://portal.azure.com/#view/Microsoft_Azure_Storage/ContainerMenuBlade/~/overview/storageAccountId/%2Fsubscriptions%2F695e4491-d568-4105-a1e1-8f2baf3b54df%2FresourceGroups%2Fabaco-rg%2Fproviders%2FMicrosoft.Storage%2FstorageAccounts%2F${STORAGE_ACCOUNT}/path/loan-data"
echo ""
echo "Storage Account: ${STORAGE_ACCOUNT}"
echo "Container: loan-data"

# Save credentials for next steps
cat >.azure-credentials <<EOF
STORAGE_ACCOUNT=${STORAGE_ACCOUNT}
STORAGE_KEY=${STORAGE_KEY}
RESOURCE_GROUP=${RESOURCE_GROUP}
EOF

echo ""
echo "🔑 Credentials saved to .azure-credentials"
