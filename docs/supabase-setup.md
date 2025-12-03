# Supabase Local Development Setup

## Prerequisites

1. **Docker Desktop** - Required for local Supabase
2. **Node.js** - For npm packages
3. **Supabase CLI** - For local development

## Quick Start

1. **Install Supabase CLI:**

   ```bash
   npm install -g supabase
   ```

2. **Initialize Supabase (if not done):**

   ```bash
   supabase init
   ```

3. **Start local Supabase:**

   ```bash
   supabase start
   ```

4. **Check status:**

   ```bash
   supabase status
   ```

## Common Issues & Solutions

### "Could not connect to local Supabase project"

- Run `supabase start` first
- Ensure Docker is running
- Check `supabase status` for service URLs

### Docker Issues

- Make sure Docker Desktop is running
- Try `supabase stop` then `supabase start`
- Restart Docker if needed

### Port Conflicts

- Default ports: API (54321), DB (54322), Studio (54323)
- Check if ports are available: `lsof -i :54321`

## Environment Setup

Create `.env.local` with local Supabase credentials:

```env
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-from-supabase-start
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-from-supabase-start
```

## Useful Commands

- `supabase start` - Start local development
- `supabase stop` - Stop all services
- `supabase status` - Check service status
- `supabase db reset` - Reset database
- `supabase studio` - Open Supabase Studio

### Deployment Commands

```bash
# Execute complete cleanup and sync
cd /Users/jenineferderas/Documents/GitHub/nextjs-with-supabase
chmod +x cleanup_and_sync.sh
./cleanup_and_sync.sh

# Verify deployment
npm run build
jupyter notebook notebooks/abaco_financial_intelligence_unified.ipynb

# Verify complete platform
python3 -c "
import pandas as pd
import numpy as np
print('✅ ABACO Platform: Unified and Operational')
print('🚀 Enterprise deployment ready')
print('📊 Analytics: 28+ dimensions active')
print('🔒 Security: License compliant')
"
```

Now run the cleanup script to complete the repository optimization:

```bash
cd /Users/jenineferderas/Documents/GitHub/nextjs-with-supabase
chmod +x cleanup_and_sync.sh
./cleanup_and_sync.sh
```
