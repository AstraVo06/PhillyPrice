-- PhillyPrice saved homes. Run once in Supabase: SQL Editor -> New query -> paste -> Run.
create table if not exists public.saved_homes (
  id bigint generated always as identity primary key,
  user_email text not null,
  home_key text not null,
  address text not null,
  lat double precision,
  lon double precision,
  estimate integer,
  low integer,
  high integer,
  beds integer,
  baths integer,
  sqft integer,
  saved_at timestamptz not null default now(),
  unique (user_email, home_key)
);

-- Row level security on with no policies: the public (anon) key can't read or write anything.
-- Only the website's server, using the secret key, can reach this table.
alter table public.saved_homes enable row level security;

-- If "Automatically expose new tables" was turned off when the project was created, the website's
-- server role needs these privileges. Harmless if they were already granted.
grant select, insert, update, delete on public.saved_homes to service_role;
grant usage, select on all sequences in schema public to service_role;
