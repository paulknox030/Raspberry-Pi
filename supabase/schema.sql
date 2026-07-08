create extension if not exists "pgcrypto";

create table if not exists assistant_inbox (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  source text default 'raspberry-pi-v1',
  audio_path text,
  transcript_path text,
  transcript_text text,
  status text not null default 'new',
  command_type text,
  parsed_json jsonb,
  result_text text,
  error text
);

create index if not exists assistant_inbox_created_at_idx
on assistant_inbox (created_at desc);

create index if not exists assistant_inbox_status_idx
on assistant_inbox (status);
