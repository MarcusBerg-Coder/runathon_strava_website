# Security and Privacy Notes

## Donation Integrity

- Create PayPal orders server-side.
- Capture approved PayPal orders server-side.
- Count donations only after `PAYMENT.CAPTURE.COMPLETED` webhooks verify successfully.
- Store webhook event IDs and capture IDs to keep processing idempotent.

## Strava Privacy

Strava data from a specific athlete should not be displayed publicly to other users. The public site intentionally shows aggregate campaign mileage only. If public leaderboards or per-run displays are desired later, request and document Strava Community Application approval first.

## Secrets

Never commit `.env.local` or raw secrets. Required production secrets:

- `DATABASE_URL`
- `ADMIN_PASSWORD`
- `ADMIN_SESSION_SECRET`
- `PAYPAL_CLIENT_ID`
- `PAYPAL_CLIENT_SECRET`
- `PAYPAL_WEBHOOK_ID`
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_VERIFY_TOKEN`
- `STRAVA_TOKEN_ENCRYPTION_KEY`

## Admin Sessions

Admin sessions use signed, HttpOnly cookies. The FastAPI service re-validates admin authorization on privileged endpoints; do not rely on frontend route hiding.

