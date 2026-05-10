# Runathon Philanthropy Website

A Vercel Services monorepo for an AEPI philanthropy runathon: Next.js App Router + shadcn-style UI in `apps/web`, FastAPI in `services/api`, and Postgres for campaign totals.

## Stack

- Frontend: Next.js App Router, React, TypeScript, Tailwind CSS, shadcn-style components
- Backend: FastAPI, SQLAlchemy, Postgres
- Integrations: PayPal Checkout with Venmo funding enabled, Strava OAuth and webhooks
- Deployment: Vercel Services with the frontend at `/` and FastAPI at `/api`

## Local Setup

1. Install JavaScript dependencies:

   ```bash
   npm install
   ```

2. Install Python dependencies:

   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r services/api/requirements.txt
   ```

3. Copy `.env.example` to `.env.local` and fill in secrets.

4. Run both services through Vercel:

   ```bash
   npm run dev
   ```

   If Vercel Services is not enabled locally, run the services separately:

   ```bash
   npm run dev:web
   python -m uvicorn services.api.main:app --reload --port 8000
   ```

   When running services separately, set `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` for the web app and `API_PUBLIC_URL=http://127.0.0.1:8000` for the API service.

## Deployment Notes

Set the Vercel project Framework Preset to **Services**. Provision Postgres through the Vercel Marketplace Neon integration, then add the PayPal, Strava, and admin secrets as Vercel environment variables. PayPal webhook events should point at:

```text
https://your-domain.com/api/paypal/webhook
```

Strava webhook events should point at:

```text
https://your-domain.com/api/strava/webhook
```

## Safety Notes

Donation totals update only from verified PayPal webhooks. Strava webhook payloads are treated as notifications; the API fetches source activity before counting. Public pages show aggregate mileage, not individual Strava activity details.
