# ABACO — Loan Analytics Platform

## ContosoTeamStats Local Development Guide

This service-oriented API is built with .NET 6, backed by SQL Server, containerized with Docker, and wired to Azure services, SendGrid, and Twilio. Follow this guide to provision the required tools, configure secrets, and run the API locally before relying on the automated GitHub Actions workflow for Azure deployments.

### Prerequisites
Install the following on your workstation:
- **.NET 6 SDK** – required to build and run the ContosoTeamStats Web API. Download from the [.NET 6.0 download page](https://dotnet.microsoft.com/download/dotnet/6.0).
- **IDE** – Visual Studio 2022 (Community is fine) or VS Code with the C# Dev Kit extension for editing, debugging, and working with solution files.
- **Docker Desktop** – builds and runs the containerized app, and it can also host a SQL Server container if you prefer not to install SQL Server locally.
- **SQL Server** – either SQL Server Express with Management Studio (SSMS) or a SQL Server container. The app uses Entity Framework Core migrations, so you need a reachable SQL Server instance before running `dotnet ef database update`.

### Optional Azure Tooling

For parity with the cloud workflow and GitHub Actions deployment (.github/workflows/main.yml), create these Azure resources using a free Azure account:

| Resource                           | Purpose                                               | Free option                                                                                      |
| ---------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| **Azure SQL Database**             | Host the production database.                         | Choose the Serverless compute tier for generous free monthly grants.                             |
| **Azure App Service**              | Host the Docker container in Azure.                   | Create an App Service Plan on the F1 (Free) tier and set the publish method to Docker Container. |
| **Azure Container Registry (ACR)** | Store the Docker image pushed by CI.                  | Basic tier is very low cost; it works well for dev/test pipelines.                               |
| **Azure Storage Account**          | Store blobs such as team logos or other file uploads. | General Purpose v2 includes a free tier (5 GB storage, 20K transactions/month).                  |

### Step-by-step Local Setup

#### 1. Fill in `appsettings.Development.json`
Populate the configuration file with the services you plan to consume. Example snippet:
```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "ConnectionStrings": {
    // Option A: Local SQL Server
  "SqlConnectionString": "Server=localhost\\SQLEXPRESS;Database=ContosoTeamStats;Trusted_Connection=True;MultipleActiveResultSets=true"
    // Option B: Azure SQL Database (swap the URI shown in the Azure portal)
    // "SqlConnectionString": "Server=tcp:your-server-name.database.windows.net,1433;Initial Catalog=your-db-name;..."
  },
  "SendGridKey": "YOUR_SENDGRID_API_KEY",
  "Twilio": {
    "AccountSid": "YOUR_TWILIO_SID",
    "AuthToken": "YOUR_TWILIO_TOKEN",
    "PhoneNumber": "+15551234567"
  },
  "StorageConnectionString": "YOUR_AZURE_STORAGE_CONNECTION_STRING"
}
```
Use secrets or environment variables in your IDE to keep API keys and connection strings out of source control.

#### 2. Prepare the Database
From the repo root, run:
```bash
dotnet ef database update
```
This applies the Entity Framework Core migrations against the configured `SqlConnectionString` and creates the needed schema.
If you prefer Docker for SQL Server, start a container such as:
```bash
docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=Your@Passw0rd" -p 1433:1433 --name sqlserver -d mcr.microsoft.com/mssql/server:2019-latest
```
Then point `SqlConnectionString` to `Server=localhost,1433;User Id=sa;Password=Your@Passw0rd;...`.

#### 3. Run the API Locally
- In Visual Studio, hit the Run button (select the ContosoTeamStats project or Docker profile as needed).
- From the terminal: `dotnet run` from the project directory.
Swagger will be available at `https://localhost:<port>/swagger`, which you can use to play with endpoints and verify that data flows to/from SQL Server, SendGrid, Twilio, and Azure Storage.

#### 4. Container and Azure Validation

- Build the Docker image locally:

```bash
docker build -t contoso-team-stats .
```

- Run it against your local SQL Server or Azure SQL using environment overrides (pass connection strings via `-e` flags or a `.env` file).
- If you configure Azure services, confirm the values match what the GitHub Actions workflow expects so CI/CD can push to your ACR and deploy to App Service.

### Automating Configuration

- Store secrets in a `.env` file and load them with a script (for example, `set -a && . .env && set +a` on macOS/Linux) before running `dotnet run`.
- Add a `docker-compose.yml` that declares the API service plus SQL Server, allowing `docker compose up` to wire everything together for faster validation.
- Use the Azure CLI to automate resource creation (`az sql db create`, `az acr create`, `az webapp create`, etc.) matching the workflow's expectations.

### Post-setup Checklist
1. Verify the sync service is running (if applicable).
2. Run the application and call a few endpoints via Swagger or Postman.
3. Ensure test objects land in SQL Server and that SendGrid/Twilio/Storage calls succeed (use sandbox test accounts if available).
4. Once everything looks good, expand OU filtering and sync in the Azure AD Connect scenario described earlier before scaling up the sync scope.

### Reproducible Validation Steps
Run these commands sequentially to confirm the documentation works:
```bash
# Ensure env vars are loaded (adjust for your shell if not bash/zsh)
set -a && . .env && set +a
# Confirm Entity Framework migrations apply cleanly
dotnet ef database update
# Start the API as described earlier
dotnet run
# While the API runs, hit a Swagger endpoint (substitute the port from the console)
curl -k https://localhost:5001/swagger/index.html
```
Leave `dotnet run` running while you manually explore the Swagger UI or Postman to confirm SQL Server, SendGrid, Twilio, and Storage interactions behave as expected.

### Container Diligence and GitHub Actions Verification
Use the commands below to build the Docker image, push it to Azure Container Registry, and run the GitHub workflow tied to that image. Replace placeholders with your actual ACR name and workflow branch.
```bash
# Build locally
docker build -t contoso-team-stats:local .

# Tag for ACR (replace with your registry)
docker tag contoso-team-stats:local <your-registry>.azurecr.io/contoso-team-stats:latest

# Login and push
az acr login --name <your-registry>
docker push <your-registry>.azurecr.io/contoso-team-stats:latest
# Push docs/changes to trigger workflow
git checkout -b validation/contoso-team-stats
git add docs/ContosoTeamStats-setup.md README.md
git commit -m "docs: document ContosoTeamStats validation"
git push -u origin validation/contoso-team-stats
# Trigger GitHub Actions workflow (GH CLI or portal)
gh workflow run main --ref validation/contoso-team-stats
```

After the workflow finishes, review the GitHub run summary plus Azure portal logs to confirm the image landed in ACR and the App Service deployment succeeded.
