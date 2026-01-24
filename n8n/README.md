# n8n Workflow Automation Setup

This directory contains the Docker Compose configuration for running n8n workflow automation platform with PostgreSQL database.

## Prerequisites

- Docker installed
- Docker Compose installed

## Quick Start

### 1. Setup Environment Variables

Copy the example environment file and configure with your credentials:

```bash
cp .env.example .env
```

Edit the `.env` file and replace the placeholder values with secure credentials:

- `POSTGRES_USER`: PostgreSQL username (default: n8n_user)
- `POSTGRES_PASSWORD`: Secure password for PostgreSQL
- `POSTGRES_DB`: Database name (default: n8n_db)
- `N8N_BASIC_AUTH_USER`: n8n admin username
- `N8N_BASIC_AUTH_PASSWORD`: Secure password for n8n admin
- `N8N_ENCRYPTION_KEY`: Random string (minimum 32 characters)

### 2. Generate Secure Credentials

Generate a secure encryption key:

```bash
openssl rand -hex 32
```

### 3. Start Services

Start n8n and PostgreSQL:

```bash
docker-compose up -d
```

### 4. Access n8n

Open your browser and navigate to:

```
http://localhost:5678
```

Login with the credentials you set in the `.env` file.

## Management Commands

### View Logs

```bash
docker-compose logs -f
```

### Stop Services

```bash
docker-compose down
```

### Restart Services

```bash
docker-compose restart
```

### Stop and Remove All Data

```bash
docker-compose down -v
```

## Architecture

- **n8n**: Workflow automation platform (port 5678)
- **PostgreSQL**: Database for n8n data persistence
- **Volumes**: Persistent storage for data

## Security Notes

- Never commit the `.env` file to version control
- Use strong, unique passwords
- Change default credentials immediately
- Keep the encryption key secure and backed up

## Integration with Azure and Supabase

This n8n instance can be configured to:

1. Receive data from Azure web forms (manual input)
2. Process and transform data through workflows
3. Store/retrieve data from Supabase
4. Output to Azure dashboard

## Troubleshooting

### Database Connection Issues

Check PostgreSQL logs:
```bash
docker-compose logs postgres
```

### Port Already in Use

Change the port in `docker-compose.yml`:
```yaml
ports:
  - "8080:5678"  # Change 8080 to your preferred port
```
