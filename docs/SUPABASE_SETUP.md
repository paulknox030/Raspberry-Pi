# Supabase Setup

1. Create a Supabase project.
2. Open the SQL editor and run `supabase/schema.sql`.
3. Create a Storage bucket named `assistant-audio`.
4. Put `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `.env` on the Pi.
5. The service role key is backend-only and must never be committed.

The app uses Supabase as an inbox. The Raspberry Pi captures audio, transcribes it, uploads files, and inserts a row into `assistant_inbox`. Future agents can read that table and decide what to do next.
