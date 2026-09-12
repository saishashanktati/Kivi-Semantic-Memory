-- Kivi semantic memory — initial schema
-- Run this ONCE in the Supabase SQL editor (or via psql).
-- Embedding dimension is 768 to match Google's text-embedding-004.
-- If you switch embedding models, change EVERY vector(768) below to match.

create extension if not exists vector;
create extension if not exists pg_trgm;
create extension if not exists fuzzystrmatch;

-- ── enums ────────────────────────────────────────────────────────────
do $$ begin
  create type sensitivity_t   as enum ('public','personal','restricted');
  create type memory_type_t   as enum ('entity','preference','fact','active_thread','transient');
  create type domain_t        as enum ('coding','creative','research','productivity','business','personal');
  create type memory_status_t as enum ('active','pending_confirmation','superseded','archived','deleted');
  create type thread_state_t  as enum ('open','stale','closed');
exception when duplicate_object then null; end $$;

-- ── users & onboarding ───────────────────────────────────────────────
create table if not exists users (
  id           uuid primary key default gen_random_uuid(),
  display_name text,
  created_at   timestamptz not null default now()
);

create table if not exists domain_ranks (
  user_id uuid references users(id) on delete cascade,
  domain  domain_t not null,
  rank    smallint not null check (rank between 1 and 3),
  primary key (user_id, domain),
  unique (user_id, rank)
);

-- ── episodic layer: what happened ────────────────────────────────────
create table if not exists episodes (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null references users(id) on delete cascade,
  occurred_at    timestamptz not null,
  mode           text not null check (mode in ('dictation','hey_kivi')),
  source         text not null,
  app_context    jsonb,
  raw_asr        text,
  formatted_text text,
  language       text,
  sensitivity    sensitivity_t not null default 'personal',
  embedding      vector(768),
  token_count    int,
  created_at     timestamptz not null default now(),
  deleted_at     timestamptz,

  -- Part One commitment, enforced by the database itself:
  constraint restricted_never_embedded
    check (sensitivity <> 'restricted' or embedding is null),
  constraint restricted_no_content
    check (sensitivity <> 'restricted' or (raw_asr is null and formatted_text is null))
);

create index if not exists episodes_embedding_idx
  on episodes using hnsw (embedding vector_cosine_ops);
create index if not exists episodes_time_idx
  on episodes (user_id, occurred_at desc) where deleted_at is null;
create index if not exists episodes_source_time_idx
  on episodes (user_id, source, occurred_at desc) where deleted_at is null;
create index if not exists episodes_appctx_idx
  on episodes using gin (app_context);

-- ── semantic layer: what is believed ─────────────────────────────────
create table if not exists memories (
  id                  uuid primary key default gen_random_uuid(),
  user_id             uuid not null references users(id) on delete cascade,
  content             text not null,
  memory_type         memory_type_t not null,
  domain              domain_t not null,
  sensitivity         sensitivity_t not null default 'personal',

  subject             text,
  attribute           text,
  value               text,
  normalized_key      text,
  is_multivalued      boolean not null default false,

  status              memory_status_t not null default 'active',
  superseded_by       uuid references memories(id),
  thread_state        thread_state_t,
  user_pinned         boolean not null default false,

  confidence          real not null default 0.5,
  reinforcement_count int  not null default 1,
  created_at          timestamptz not null default now(),
  last_reinforced_at  timestamptz not null default now(),
  last_retrieved_at   timestamptz,
  deleted_at          timestamptz,
  embedding           vector(768),

  constraint restricted_never_embedded_mem
    check (sensitivity <> 'restricted' or embedding is null)
);

create index if not exists memories_embedding_idx
  on memories using hnsw (embedding vector_cosine_ops);
create index if not exists memories_type_idx
  on memories (user_id, status, memory_type) where deleted_at is null;
create index if not exists memories_slot_idx
  on memories (user_id, subject, attribute) where status = 'active';
create index if not exists memories_key_idx
  on memories (user_id, normalized_key);
create index if not exists memories_thread_idx
  on memories (user_id, thread_state) where memory_type = 'active_thread';
create index if not exists memories_subject_trgm_idx
  on memories using gin (subject gin_trgm_ops);

-- ── provenance: every belief points at its evidence ──────────────────
create table if not exists memory_evidence (
  memory_id  uuid references memories(id) on delete cascade,
  episode_id uuid references episodes(id) on delete cascade,
  role       text not null,   -- origin | reinforcement | contradiction | clarification
  excerpt    text,
  created_at timestamptz not null default now(),
  primary key (memory_id, episode_id, role)
);

-- ── candidate pool: things seen once, not yet believed ───────────────
create table if not exists memory_candidates (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null references users(id) on delete cascade,
  normalized_key text not null,
  proposed       jsonb not null,
  score          real not null,
  sightings      int not null default 1,
  first_seen     timestamptz not null default now(),
  last_seen      timestamptz not null default now(),
  status         text not null default 'pending',
  unique (user_id, normalized_key)
);

-- ── aliases: the shorthand this person actually uses ─────────────────
create table if not exists entity_aliases (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references users(id) on delete cascade,
  alias      text not null,
  memory_id  uuid not null references memories(id) on delete cascade,
  origin     text not null,   -- extraction | clarification | fuzzy_match | user_edit
  confidence real not null default 0.6,
  hit_count  int not null default 0,
  created_at timestamptz not null default now(),
  unique (user_id, alias, memory_id)
);
create index if not exists aliases_trgm_idx
  on entity_aliases using gin (alias gin_trgm_ops);

-- ── inspectability: why the system did what it did ───────────────────
create table if not exists decisions (
  id         bigserial primary key,
  user_id    uuid not null,
  episode_id uuid,
  query_id   uuid,
  stage      text not null,
  verdict    text not null,
  reason     text not null,
  detail     jsonb,
  model      text,
  tokens_in  int,
  tokens_out int,
  cost_usd   numeric(10,6),
  latency_ms int,
  created_at timestamptz not null default now()
);
create index if not exists decisions_user_idx on decisions (user_id, created_at desc);
create index if not exists decisions_episode_idx on decisions (episode_id);
create index if not exists decisions_query_idx on decisions (query_id);

create table if not exists retrieval_items (
  query_id        uuid not null,
  memory_id       uuid,
  episode_id      uuid,
  rank            int,
  vector_score    real,
  retention_score real,
  filter_boost    real,
  final_score     real,
  used_in_prompt  boolean not null
);
create index if not exists retrieval_query_idx on retrieval_items (query_id, rank);

-- ── per-user lexicon for query repair (§7.4) ─────────────────────────
drop materialized view if exists user_lexicon;
create materialized view user_lexicon as
select m.user_id,
       lower(m.subject)      as term,
       'subject'             as kind,
       m.id                  as memory_id,
       1                     as freq,
       dmetaphone(m.subject) as phonetic
from memories m
where m.subject is not null
  and m.deleted_at is null
  and m.status = 'active'
union all
select a.user_id, lower(a.alias), 'alias', a.memory_id,
       a.hit_count + 1, dmetaphone(a.alias)
from entity_aliases a
where a.confidence > 0.4;

create index if not exists lexicon_trgm_idx on user_lexicon using gin (term gin_trgm_ops);
create index if not exists lexicon_phonetic_idx on user_lexicon (user_id, phonetic);

-- ── safe read view (excludes restricted + deleted) ───────────────────
create or replace view memories_safe as
select * from memories
where sensitivity <> 'restricted' and deleted_at is null;
