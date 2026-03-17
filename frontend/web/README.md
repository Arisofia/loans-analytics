# Next.js Web Dashboard

Next.js frontend application for Abaco Loans Analytics platform.

## Overview

This is the web-based dashboard for KPI visualization, portfolio analysis, and AI-powered insights. It provides an interactive interface for exploring loan analytics data.

## Features

- **Corporate Theme**: Black, Grayscale, and Purple color scheme
- **KPI Dashboard**: Real-time metrics visualization
- **Portfolio Analytics**: Loan performance and collection metrics
- **Financial Views**: Revenue, rotation, and profitability analysis
- **Risk Dashboard**: PAR-30, PAR-90, NPL tracking
- **Growth Metrics**: Client acquisition and TPV trends
- **Marketing Analytics**: Campaign performance and ROI
- **Data Quality**: Validation and completeness monitoring
- **AI Insights**: GPT-powered analysis and recommendations
- **Report Export**: PDF and Excel report generation

## Tech Stack

- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Plotly.js with react-plotly.js
- **API Client**: Axios
- **UI Components**: @headlessui/react, @heroicons/react
- **State Management**: React Context / Zustand
- **Form Handling**: React Hook Form
- **Validation**: Zod

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your API URL and keys
```

### Development

```bash
# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linter
npm run lint

# Run tests
npm test
```

The application will be available at `http://localhost:3000`

## Environment Variables

Create a `.env.local` file with:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_ENV=development
```

## Project Structure

```
apps/web/
├── public/           # Static assets (logo, icons, fonts)
├── src/
│   ├── app/          # Next.js App Router pages
│   ├── components/   # Reusable React components
│   ├── lib/          # Utilities and helpers
│   ├── hooks/        # Custom React hooks
│   ├── types/        # TypeScript type definitions
│   └── styles/       # Global styles
├── .env.example
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

## Key Pages

- `/` - Dashboard home with KPI summary
- `/portfolio` - Portfolio analytics
- `/financial` - Financial metrics
- `/risk` - Risk management dashboard
- `/growth` - Growth analytics
- `/marketing` - Marketing performance
- `/quality` - Data quality monitoring
- `/ai-insights` - AI-powered analysis
- `/reports` - Report generation and export

## API Integration

The frontend communicates with the FastAPI backend at `apps/analytics`:

- Data fetching via Axios with error handling
- Real-time updates for KPI metrics
- File upload for CSV/XLSX ingestion
- AI chat interface for insights

## Styling Guidelines

- **Colors**: Black (#000000), Grayscale (#808080), Purple (#4B0082)
- **Typography**: Roboto Condensed, Montserrat, Open Sans Condensed
- **Layout**: Dark mode by default
- **Charts**: Plotly with unified dark theme
- **Spacing**: Consistent with Tailwind spacing scale

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel
```

### Docker

```bash
# Build image
docker build -t abaco-web .

# Run container
docker run -p 3000:3000 abaco-web
```

## Testing

```bash
# Unit tests
npm test

# E2E tests
npm run test:e2e

# Coverage
npm run test:coverage
```

## Documentation

- [Fintech Dashboard Web App Guide](../../docs/FINTECH_DASHBOARD_WEB_APP_GUIDE.md)
- [API Reference](../../docs/API_REFERENCE.md)
- [Component Library](./docs/COMPONENTS.md)

## Status

⚠️ **Implementation Pending**: This directory structure is defined but not yet fully implemented. Current active dashboard: `streamlit_app.py`

## Related Resources

- Backend API: `apps/analytics/`
- Data Pipeline: `src/pipeline/`
- Streamlit Dashboard (Current): `streamlit_app.py`
