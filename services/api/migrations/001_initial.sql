create extension if not exists "pgcrypto";

create table if not exists campaigns (
  id uuid primary key default gen_random_uuid(),
  name varchar(160) not null,
  slug varchar(160) not null unique,
  beneficiary varchar(240) not null,
  mission text not null,
  dollars_per_mile numeric(10, 2) not null default 10.00,
  starts_at timestamptz not null,
  ends_at timestamptz not null,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists participants (
  id uuid primary key default gen_random_uuid(),
  campaign_id uuid not null references campaigns(id) on delete cascade,
  name varchar(160) not null,
  role varchar(120) not null default 'Runner',
  initials varchar(8) not null,
  bio text not null default '',
  avatar_url varchar(500),
  invite_token varchar(120) not null unique,
  strava_athlete_id bigint,
  strava_refresh_token text,
  strava_access_token text,
  strava_token_expires_at timestamptz,
  connection_status varchar(40) not null default 'invited',
  created_at timestamptz not null default now()
);

create table if not exists donations (
  id uuid primary key default gen_random_uuid(),
  campaign_id uuid not null references campaigns(id) on delete cascade,
  paypal_order_id varchar(120),
  paypal_capture_id varchar(120),
  amount numeric(10, 2) not null,
  currency varchar(3) not null default 'USD',
  status varchar(40) not null default 'pending',
  donor_name varchar(160),
  donor_message varchar(240),
  anonymous boolean not null default true,
  created_at timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists activities (
  id uuid primary key default gen_random_uuid(),
  campaign_id uuid not null references campaigns(id) on delete cascade,
  participant_id uuid not null references participants(id) on delete cascade,
  strava_activity_id bigint not null unique,
  distance_miles numeric(10, 3) not null,
  sport_type varchar(80) not null,
  started_at timestamptz not null,
  eligible boolean not null default false,
  inclusion_status varchar(40) not null default 'pending',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists audit_events (
  id uuid primary key default gen_random_uuid(),
  event_source varchar(80) not null,
  event_id varchar(160) not null,
  action varchar(120) not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (event_source, event_id)
);

create unique index if not exists uq_donations_paypal_order_id
  on donations(paypal_order_id)
  where paypal_order_id is not null;

create unique index if not exists uq_donations_paypal_capture_id
  on donations(paypal_capture_id)
  where paypal_capture_id is not null;

create index if not exists idx_participants_strava_athlete_id on participants(strava_athlete_id);
create index if not exists idx_donations_status on donations(status);
create index if not exists idx_activities_campaign_included on activities(campaign_id, inclusion_status, eligible);

insert into campaigns (name, slug, beneficiary, mission, dollars_per_mile, starts_at, ends_at, active)
values (
  'AEPI Runathon',
  'aepi-runathon',
  'Chapter philanthropy partner',
  'Brothers are turning every donation into miles for a cause our chapter is proud to support.',
  10.00,
  '2026-05-01T00:00:00Z',
  '2026-06-01T00:00:00Z',
  true
)
on conflict (slug) do nothing;

