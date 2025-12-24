$ErrorActionPreference = "Stop"

# Configuration
$resourceGroup = "rg-twitterbots"
$location = "eastus"
$randomSuffix = Get-Random -Minimum 1000 -Maximum 9999
$storageAccount = "sttwitterbots$randomSuffix"
$functionApp = "func-twitterbots$randomSuffix"

# Check for Azure CLI
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI (az) is not installed. Please install it first."
}

# Login check
$account = az account show | ConvertFrom-Json
if (-not $account) {
    Write-Host "Please login to Azure..."
    az login
}

Write-Host "Using subscription: $($account.name) ($($account.id))"
$confirm = Read-Host "Is this the correct subscription? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "Please use 'az account set --subscription <id>' to set the correct subscription and run this script again."
    exit
}

# Create Resource Group
Write-Host "Creating Resource Group '$resourceGroup'..."
az group create --name $resourceGroup --location $location

# Create Storage Account
Write-Host "Creating Storage Account '$storageAccount'..."
az storage account create --name $storageAccount --location $location --resource-group $resourceGroup --sku Standard_LRS

# Create Function App
Write-Host "Creating Function App '$functionApp'..."
az functionapp create --resource-group $resourceGroup --name $functionApp --storage-account $storageAccount --consumption-plan-location $location --runtime python --runtime-version 3.11 --os-type linux --functions-version 4

# Get Storage Connection String
Write-Host "Getting Storage Connection String..."
$connString = az storage account show-connection-string --name $storageAccount --resource-group $resourceGroup --query connectionString --output tsv

# Configure App Settings
Write-Host "Configuring App Settings..."
# Note: You need to fill in your Twitter secrets here or in the portal later
$settings = @(
    "BLOB_CONNECTION_STRING=$connString",
    "TEHILIM_CONSUMER_KEY=PLACEHOLDER",
    "TEHILIM_CONSUMER_SECRET=PLACEHOLDER",
    "TEHILIM_ACCESS_TOKEN=PLACEHOLDER",
    "TEHILIM_ACCESS_TOKEN_SECRET=PLACEHOLDER",
    "TEHILIM_CREDIT_CREATOR=PLACEHOLDER",
    "GILGAMESH_CONSUMER_KEY=PLACEHOLDER",
    "GILGAMESH_CONSUMER_SECRET=PLACEHOLDER",
    "GILGAMESH_ACCESS_TOKEN=PLACEHOLDER",
    "GILGAMESH_ACCESS_TOKEN_SECRET=PLACEHOLDER",
    "GILGAMESH_CREDIT_CREATOR=PLACEHOLDER",
    "GILGAMESH_CREDIT_INSPIRED=PLACEHOLDER",
    "AzureWebJobs.TehilimTrigger.Disabled=1",
    "AzureWebJobs.GilgameshTrigger.Disabled=1"
)
az functionapp config appsettings set --name $functionApp --resource-group $resourceGroup --settings $settings

Write-Host "Infrastructure created successfully!"
Write-Host "Function App Name: $functionApp"
Write-Host "To deploy the code, run: func azure functionapp publish $functionApp"
Write-Host "IMPORTANT: Go to the Azure Portal and update the Twitter API keys in the Function App Configuration."
