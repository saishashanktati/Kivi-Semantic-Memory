# Kivi — Semantic Memory for Hey Kivi
### Part One: Position & Vision · Part Two: Build Specification
*Revision 3 — query understanding built out in full; scoped forgetting dropped*

---

# PART ONE — Product Position and Vision

## Positioning Statement

> Semantic memory should let Hey Kivi understand the arc of a person's work without asking permission at every turn. It infers silently, but stays fully answerable — a person can always ask what Kivi remembers, and correct it. Memory is weighted, not siloed: everything is visible everywhere, but priority follows what a person actually does most. What deserves retention is a fact, preference, or active project — not a one-off query. Kivi never overwrites a remembered fact without confirming the contradiction first. Trust comes from being legible after the fact, not from asking before it.

*(95 words)*

---

## Product Vision

### What semantic memory should let Kivi become

Styles and phonetic memory already make dictation sound like the person using it. Semantic memory makes a different claim — that Kivi should understand **what a person is working on**, not only what they said.

The unit of value is not the transcript. It is continuity. Someone who has spoken to Kivi for three months should not re-explain who Priya is, which deadline belongs to which project, or how they want a Slack message to sound. Semantic memory is what turns a dictation tool into something that has been paying attention.

### Where the value is created

At the moment of **resumption** — when a person returns to something already in motion. Three capabilities matter:

- **Recall** — retrieving a specific past moment ("the dictation I did around 5 PM yesterday in Slack").
- **Resume** — picking up an open thread without restating its context.
- **Apply** — producing new output shaped by known preferences, people, and projects.

Comprehensiveness is not value. A system that learns ten things and surfaces three usefully beats one that learns fifty. Over-remembering is a failure mode, not a neutral cost.

### What deserves to be remembered

Things with a lifecycle — a durable fact about the person's world, a stable preference, a named entity they return to, an open thread. Not one-off queries, not arithmetic, not the weather.

Kivi keeps a separate episodic record of what was dictated, so "find what I said on Tuesday" still works. But an episode is *evidence*, not a belief. Beliefs are earned: a candidate becomes a memory when it recurs, is explicitly named, or persists across turns. Everything Kivi believes carries a domain and a type, and how long it survives follows from both.

### What Kivi must never assume

**That access is permission.** Connecting Gmail does not license reading bank statements, medical results, or legal documents. Those exist to Kivi as metadata only — filtered before the embedding step, never vectorised, never reasoned over.

**That the newest statement is the true one.** A contradiction is surfaced, never silently applied.

**That a mention is a commitment.**

**That dictated content is addressed to Kivi.** When someone dictates a message, they are speaking to a colleague, not instructing Kivi.

**That an unclear request is an unanswerable one.** A fragment, a mistyped name, or a bare keyword is ordinary speech, not a malformed query. Kivi repairs what it can, asks one question when repair is not enough, and abstains only when neither works.

**That it knows.** When the history does not support an answer, Kivi says so rather than inventing one.

### Why someone should trust this enough to keep using it

Not because it asks. Seeking permission on every inference would destroy a voice-first interface — the cost of consent *is* the interaction. Kivi infers silently and earns trust by remaining **answerable after the fact**: anyone can ask what Kivi remembers about anything and receive a specific answer with its evidence — what was said, when, in which app — and correct or delete it in one action. Control without administration. The person never maintains a database; they occasionally overrule a belief.

Onboarding asks once: rank three of six domains. That ranking weights how long things survive and how readily they surface. Memory is weighted, not siloed.

The contract is short. Kivi will infer without asking. It will never conceal what it inferred, never overwrite a fact behind your back, never read what you did not offer, and never claim to know something it cannot show you.

*(585 words)*

---
---

# PART TWO — Build Specification

Everything below is checked against Part One. Any design that requires reading restricted content, asking permission on every turn, or answering without evidence is disqualified by the position, not merely disfavoured.

---

## 0. What changed from the original sketch, and why

| # | Addition | Why it is load-bearing |
|---|---|---|
| 1 | **Episodic layer split from semantic layer** | Axis B had no home for episodes, yet the canonical use case ("the dictation from 5 PM yesterday in Slack") is *purely* episodic. Episodes are evidence; memories are beliefs. |
| 2 | **Provenance as a first-class table** | "Which memories and source interactions produced each answer" is an explicit evaluation criterion. A `source` string in a metadata blob cannot answer it. |
| 3 | **Explicit abstention contract** | "Refuses to invent an answer when history does not contain one" is graded, and legibility includes being legible about ignorance. |
| 4 | **Decision log** | "How an engineer can inspect why memory did or did not affect a result." Every write, skip, repair, retrieve, clarify and abstain writes a row with its reason. |
| 5 | **Candidate pool with recurrence promotion** | Turns "value = continuity" into a mechanism, and makes *deliberate ignoring* demonstrable. |
| 6 | **Single-valued attribute registry** | Resolves conflict-vs-difference. Two values conflict only if the attribute can hold one value. |
| 7 | **Thread lifecycle states** | Without closure, `active_thread` becomes a growing pile of things that are not active. |
| 8 | **Query understanding layer (§7)** | The centrepiece. Real voice input is fragmentary, misspelled and mis-heard. A router that assumes well-formed sentences fails on the majority of genuine queries. |
| 9 | **Ambiguity clarification (§9)** | The brief explicitly asks how Kivi behaves when its understanding is *incomplete*. Previously only contradictions triggered interaction. |

**Dropped from revision 2: scoped bulk forgetting.** Deleting a whole subject cleanly requires suppression keys so the belief is not relearned from surviving transcripts, and those keys then conflict with the person re-stating the same fact later — a name, an email address — which the system must honour. Resolving that properly needs provenance-aware suppression and an override path, which is a larger feature than the value it returns here. **Per-item forget stays** (§10, inside the memory surface): one belief, one action, no suppression key, no ambiguity about scope. That covers the real need and carries none of the failure modes.

Two smaller notes:

- **Database-enforced sensitivity.** A `CHECK` constraint makes "restricted content is never embedded" a property of the schema, not a promise in the pipeline.
- **Multilingual embeddings.** This is a Sarvam product. Real dictation will be code-mixed (English/Hindi/Tamil, native script and transliterated). A monolingual English embedding model silently fails on exactly the corpus this product exists for.

---

## 1. Scope — the smallest product worth using

**Four capabilities. Nothing else gets built.**

**C1 — Episodic recall.** *"Find the dictation I did around 5 PM yesterday in Slack."*
Time + source + semantic query over episodes. Tolerant of fragmentary, misspelled and mis-heard phrasing (§7).

**C2 — Thread resumption.** *"Where am I on the membrane writeup?"*
Retrieves an active thread, its evidence, and its last state. Answers with what is done, what is open, when it was last touched.

**C3 — Memory-conditioned drafting.** *"Polish this for the meeting I'm walking into."*
Rewrites text using known preferences, known entities, and the destination app's register.

**C4 — The memory surface.** *"What do you remember about Priya?"*
Every belief, grouped by domain, each with plain-language evidence, each editable, pinnable or removable in one action. Not a settings page — the trust contract made visible.

Explicitly **not** built: scoped bulk forgetting, calendar scheduling, email sending, task management, proactive notifications, cross-device sync.

---

## 2. The dictation / Hey Kivi boundary

| | Regular dictation | Hey Kivi |
|---|---|---|
| **Writes memory** | Yes — the richest signal the product has | Yes |
| **Reads memory** | Almost never | Always |
| **Query repair (§7)** | **Never** | Always |
| **Exception** | Explicit format-level preferences only ("always sign off as Chatty") | — |

**Rule:** dictation is the *sensor*; Hey Kivi is the *actuator*.

Semantic memory must never alter the **content** of a dictation. If someone dictates "tell Ravi the deadline is Friday," Kivi does not consult memory and correct it to Thursday — that would be Kivi speaking in the person's voice about the world, which it has no standing to do.

The same line governs §7. **Query repair applies only to text addressed to Kivi.** Correcting spelling inside dictated content is Kivi editing what the person said; that is what styles and phonetic memory are for. Repair operates on requests, never on payloads. §7.10 makes this concrete for the case where a single utterance contains both.

---

## 3. Data model

### 3.1 Layers

```
EPISODES  (what happened)          →  evidence, high volume, time-indexed
    │
    │  extraction + scoring
    ▼
MEMORIES  (what is believed)       →  beliefs, low volume, semantically indexed
    │
    ├── memory_evidence            →  every belief points back at its episodes
    └── entity_aliases             →  the shorthand this person actually uses
```

### 3.2 Schema (Postgres + pgvector)

```sql
create extension if not exists vector;
create extension if not exists pg_trgm;        -- fuzzy matching (§7.4)
create extension if not exists fuzzystrmatch;  -- levenshtein + dmetaphone (§7.4)

create type sensitivity_t   as enum ('public','personal','restricted');
create type memory_type_t   as enum ('entity','preference','fact','active_thread','transient');
create type domain_t        as enum ('coding','creative','research','productivity','business','personal');
create type memory_status_t as enum ('active','pending_confirmation','superseded','archived','deleted');
create type thread_state_t  as enum ('open','stale','closed');

-- ── users & onboarding ──────────────────────────────────────────────
create table users (
  id           uuid primary key default gen_random_uuid(),
  display_name text,
  created_at   timestamptz not null default now()
);

create table domain_ranks (
  user_id uuid references users(id) on delete cascade,
  domain  domain_t not null,
  rank    smallint not null check (rank between 1 and 3),
  primary key (user_id, domain),
  unique (user_id, rank)
);

-- ── episodic layer ──────────────────────────────────────────────────
create table episodes (
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
  embedding      vector(1024),
  token_count    int,
  created_at     timestamptz not null default now(),
  deleted_at     timestamptz,

  constraint restricted_never_embedded
    check (sensitivity <> 'restricted' or embedding is null),
  constraint restricted_no_content
    check (sensitivity <> 'restricted' or (raw_asr is null and formatted_text is null))
);

create index on episodes using hnsw (embedding vector_cosine_ops);
create index on episodes (user_id, occurred_at desc) where deleted_at is null;
create index on episodes (user_id, source, occurred_at desc) where deleted_at is null;
create index on episodes using gin (app_context);

-- ── semantic layer ──────────────────────────────────────────────────
create table memories (
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
  embedding           vector(1024),

  constraint restricted_never_embedded_mem
    check (sensitivity <> 'restricted' or embedding is null)
);

create index on memories using hnsw (embedding vector_cosine_ops);
create index on memories (user_id, status, memory_type) where deleted_at is null;
create index on memories (user_id, subject, attribute) where status = 'active';
create index on memories (user_id, normalized_key);
create index on memories (user_id, thread_state) where memory_type = 'active_thread';
create index on memories using gin (subject gin_trgm_ops);

-- ── provenance ──────────────────────────────────────────────────────
create table memory_evidence (
  memory_id  uuid references memories(id) on delete cascade,
  episode_id uuid references episodes(id) on delete cascade,
  role       text not null,      -- origin | reinforcement | contradiction | clarification
  excerpt    text,
  created_at timestamptz not null default now(),
  primary key (memory_id, episode_id, role)
);

-- ── candidate pool ──────────────────────────────────────────────────
create table memory_candidates (
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

-- ── aliases: the shorthand a person actually uses (§7.4, §9.4) ──────
create table entity_aliases (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references users(id) on delete cascade,
  alias      text not null,      -- "the writeup", "priya s", "red cell", "CRE"
  memory_id  uuid not null references memories(id) on delete cascade,
  origin     text not null,      -- extraction | clarification | fuzzy_match | user_edit
  confidence real not null default 0.6,
  hit_count  int not null default 0,
  created_at timestamptz not null default now(),
  unique (user_id, alias, memory_id)
);
create index on entity_aliases using gin (alias gin_trgm_ops);

-- ── inspectability ──────────────────────────────────────────────────
create table decisions (
  id         bigserial primary key,
  user_id    uuid not null,
  episode_id uuid,
  query_id   uuid,
  stage      text not null,
  -- prefilter | extract | write | promote | contradict
  -- | normalize | repair | slots | focus | llm_parse | route
  -- | retrieve | clarify | answer | delete
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
create index on decisions (user_id, created_at desc);
create index on decisions (episode_id);
create index on decisions (query_id);

create table retrieval_items (
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
create index on retrieval_items (query_id, rank);
```

### 3.3 Per-user lexicon (materialised, for §7.4)

```sql
create materialized view user_lexicon as
select m.user_id,
       lower(m.subject)       as term,
       'subject'              as kind,
       m.id                   as memory_id,
       count(*) over (partition by m.user_id, lower(m.subject)) as freq,
       dmetaphone(m.subject)  as phonetic
from memories m
where m.subject is not null and m.deleted_at is null and m.status = 'active'
union all
select a.user_id, lower(a.alias), 'alias', a.memory_id,
       a.hit_count + 1, dmetaphone(a.alias)
from entity_aliases a
where a.confidence > 0.4;

create index on user_lexicon using gin (term gin_trgm_ops);
create index on user_lexicon (user_id, phonetic);
```

Refresh hourly and after any batch ingest. It stays small — hundreds of rows per user, not thousands — which is why §7 can afford to hit it on every token.

### 3.4 RLS

```sql
alter table episodes enable row level security;
alter table memories enable row level security;
-- repeat for every user-scoped table

create policy own_rows on episodes
  using (user_id = auth.uid()) with check (user_id = auth.uid());
```

Plus a `memories_safe` view excluding `sensitivity = 'restricted'` and soft-deleted rows, which all application reads go through except the memory surface.

---

## 4. Write pipeline

```
episode arrives
   ├─ Stage 0  SENSITIVITY PRE-FILTER   (deterministic, pre-embedding, fails closed)
   ├─ Stage 1  CHEAP GATE               (no model call)
   ├─ Stage 2  EXTRACTION               (one batched LLM call → candidate memories)
   ├─ Stage 3  WRITE DECISION           (scoring + candidate pool)
   └─ Stage 4  CONTRADICTION CHECK      (fact/preference only)
```

### Stage 0 — sensitivity pre-filter

Runs before embedding, always. Signals: sender domain patterns, attachment MIME and filename patterns, regex for account/policy/case numbers, a small classifier for financial/medical/legal language.

- Strong signal → `restricted`. Metadata only.
- Weak signal **and** high-risk channel (email, filesystem) → `restricted`. **Default to restriction under uncertainty**: a false positive costs one memory, a false negative costs the product's entire claim.
- Otherwise → `personal` (or `public`).

Every decision logged with its triggering signal, which is what makes the leak-canary test in §11 inspectable.

### Stage 1 — cheap gate (no model call)

Drop before spending tokens: pure lookups (weather, time, arithmetic, "what is X" with no first-person referent), episodes under ~8 tokens with no named entity, exact duplicates within a short window. Should discard 25–40% of a realistic corpus at near-zero cost. **Report the number** — deliberate ignoring is a graded criterion and you want a figure.

### Stage 2 — extraction

One LLM call per episode, batching 5–10 short episodes per call. Cheap model, strict JSON:

```json
{"candidates":[{
  "content": "Prefers Slack messages short, no greeting, no sign-off",
  "memory_type": "preference",
  "domain": "productivity",
  "subject": "user", "attribute": "slack_register", "value": "terse, no greeting",
  "is_multivalued": false, "confidence": 0.8,
  "excerpt": "just get to the point, skip the hi-hope-you're-well stuff"
}]}
```

Instruct it explicitly to return an empty array when nothing durable is present. Most episodes should yield zero. Averaging more than ~0.5 candidates per episode means the extractor is too eager.

**Alias harvesting happens here too.** When extraction sees a known entity referred to by a new shorthand, it emits an alias candidate. This is the passive half of what §9.4 does actively.

### Stage 3 — write decision

```
S = 0.25·specificity
  + 0.20·entity_named
  + 0.20·recurrence
  + 0.15·lifecycle_signal
  + 0.10·domain_rank_weight
  + 0.10·extractor_confidence
  − 0.30·transient_pattern
```

`domain_rank_weight`: 1.0 / 0.85 / 0.7 / 0.5 for ranks 1, 2, 3, unranked.

| Score | Action |
|---|---|
| `S ≥ 0.65` | Write memory, with evidence row |
| `0.35 ≤ S < 0.65` | Insert/increment in `memory_candidates`. Promote at **2 sightings** (facts, entities) or **3** (preferences) |
| `S < 0.35` | Discard, log reason |

Reinforcement of an existing memory: `reinforcement_count += 1`, `last_reinforced_at = now()`, `confidence ← c + 0.3·(1−c)`, new evidence row. Never duplicated.

---

## 5. Retention and decay

```
retention(m) = durability[type]
             × domain_weight[rank]
             × (1 + ln(1 + reinforcement_count))
             × exp(−Δt_since_reinforced / halflife)

halflife = base_halflife[type] × domain_weight[rank]
```

| memory_type | durability | base_halflife |
|---|---|---|
| preference | 1.00 | 365 d |
| fact | 0.90 | 180 d |
| entity | 0.75 | 120 d |
| active_thread (open) | 0.85 | 30 d, refreshed on mention |
| active_thread (stale) | 0.45 | 14 d |
| transient | 0.05 | 1 d |

`user_pinned` → retention pinned at 1.0, exempt from eviction.

**Decay governs retrieval ranking long before it governs deletion.** A decayed memory stops surfacing; deletion happens only under storage pressure, in order: transient → unranked candidates → stale threads → low-retention entities. Facts, preferences, and open threads in ranked domains are never auto-evicted.

### Thread lifecycle

```
open ──(no mention 21d)──▶ stale ──(no mention 30d more)──▶ closed
 ▲                           │
 └──────(mentioned again)────┘

open ──(explicit completion, or user closes it)──▶ closed
```

On close the thread is demoted to an `entity` memory, not deleted.

---

## 6. Contradiction detection

Conflict is a property of the **attribute**, not the values.

### Single-valued attribute registry

```
user.employer        user.role             user.timezone
user.city            user.primary_language user.default_signoff
<entity>.deadline    <entity>.status       <entity>.owner
<person>.role        <person>.team
```

Everything else — projects, tools, collaborators, context-scoped preferences ("terse in Slack", "formal in email") — is `is_multivalued` and accumulates. Multivalued memories never conflict.

### Detection

```
on new memory M (type ∈ {fact, preference}):
  find active P where P.subject = M.subject
                  and P.attribute = M.attribute
                  and P.is_multivalued = false

  none                                     → write M as active
  normalize(P.value) == normalize(M.value) → reinforce P, discard M
  M.value strictly refines P.value          → update P in place, add evidence, no prompt
  else                                      → M.status = 'pending_confirmation'
                                              P stays active; log 'contradict'
```

The refinement check prevents the most annoying false positive — interrupting over two statements that are both true at different granularity ("Bangalore" → "Indiranagar, Bangalore").

### Surfacing

**Never interrupt dictation.** Raised at the next moment it matters: the next Hey Kivi turn where the attribute is retrieved, or passively in the memory surface.

> I had you at **Sarvam AI**. Yesterday you mentioned **Cohere**. Which is current?
> `[ Sarvam AI ]  [ Cohere ]  ·  both true`

"Both true" converts the attribute to multivalued for that user — a quiet escape hatch when the registry is wrong. On answer: winner `active`, loser `superseded`. Nothing deleted.

---

## 7. Query understanding

This is the feature the rest of the product leans on. Every other capability is reached through a spoken or typed request, and those requests are not sentences.

### 7.0 The problem

Genuine Hey Kivi input looks like this:

```
"wat did i say abt the membrne thing yestrday"
"priya deadline"
"where am i on red cell writeup"
"the slack one from around 5"
"membrne writeup — status?"
"kal priya ku enna sonnen"          (code-mixed)
"pritha mail — find it"
```

Three distinct failure modes are tangled together there, and they need different treatments:

| Failure | Cause | Shape |
|---|---|---|
| **Misspelling** | typing | edit-distance errors: `yestrday`, `membrne`, `recieve` |
| **Mis-hearing** | ASR | *phonetically* close, lexically far: `membrain`, `Preetha` for `Pritha`, `read cell` for `RED cell` |
| **Fragmentation** | speech | no verb, no subject, bare keywords, trailing ellipsis |

A pipeline tuned only for keyboard typos misses every ASR error, which for a voice product is the majority case. Levenshtein distance between "Preetha" and "Pritha" is 3 on a 7-character word — below any sane threshold — yet they are the same sound. This is why the repair layer is three-way, not one-way.

### 7.1 Design principle — deterministic fast path, model only on the residual

Products like Claude and ChatGPT tolerate mangled input because a large model does the interpreting on every turn. Kivi cannot afford that shape: it is voice-first, latency-sensitive, and a model call on every query multiplies cost by the number of turns.

So the pipeline is **two-tier**:

- A **deterministic fast path** handles the common cases with indexed SQL and static maps. No model call, target under 30 ms.
- An **LLM fallback parse** (§7.8) fires only when the fast path's confidence is low. On a realistic corpus this should be 10–20% of queries. Measure it and report the ratio — it is the honest way to show the cheap path is doing real work.

```
raw query
  │
  ├─ A  tokenise, preserve raw verbatim                 ~0 ms
  ├─ B  static normalisation map                        ~1 ms
  ├─ C  lexicon repair (trigram / levenshtein / phonetic) ~10 ms   [1 indexed query]
  ├─ D  slot extraction from bag of tokens              ~2 ms
  ├─ E  focus inheritance for missing slots             ~0 ms
  ├─ F  time expression resolution                      ~2 ms
  │
  ├─ G  confidence check ──── high ──▶ route (§7.9)
  │            │
  │            └──── low ───▶ LLM fallback parse (§7.8)  ~400–900 ms
  │                                   │
  └───────────────────────────────────┴──▶ route, or clarify (§9), or abstain
```

### 7.2 Stage A — tokenise, preserve the raw query

The raw query is stored verbatim and logged before anything touches it. Every later stage works on a copy. This is not fussiness: the raw string is evidence in the decision log, and an engineer must be able to see that `membrne` became `membrane` and on what grounds. It also means a bad repair is diagnosable rather than invisible.

Tokenisation is deliberately crude — split on whitespace and punctuation, lowercase a copy, keep the original casing alongside (proper-noun casing is a weak but free signal for entity detection).

### 7.3 Stage B — static normalisation map

A JSON file, a couple of hundred entries, no model call. Three groups:

```json
{
  "shorthand": {
    "wat":"what", "abt":"about", "wrt":"with respect to", "tmrw":"tomorrow",
    "yest":"yesterday", "pls":"please", "idk":"i don't know", "asap":"as soon as possible",
    "msg":"message", "mtg":"meeting", "doc":"document", "u":"you", "ur":"your",
    "thx":"thanks", "btw":"by the way", "fyi":"for your information"
  },
  "typos": {
    "yestrday":"yesterday", "yesterdy":"yesterday", "recieve":"receive",
    "teh":"the", "adn":"and", "wehn":"when", "wich":"which", "beacuse":"because"
  },
  "time_words_indic": {
    "kal":"AMBIGUOUS_DAY", "parso":"day_before_or_after",
    "abhi":"now", "aaj":"today", "indru":"today", "nethu":"yesterday",
    "naalaikku":"tomorrow"
  }
}
```

`kal` is intentionally flagged ambiguous rather than resolved — in Hindi it means both yesterday and tomorrow, and guessing is worse than asking (§9.1 temporal ambiguity). This is the kind of case a monolingual pipeline silently gets wrong 50% of the time.

Keep this file in the repo, not in code, and let it grow from observed eval failures. It is the cheapest accuracy you will ever buy.

### 7.4 Stage C — lexicon repair against the person's own vocabulary

**The central design choice.** A general spellchecker does not know that `membrne` is a project, `CRE` is a course, and `Pritha` is a person. The user's own memory store does. So repair matches against `user_lexicon` (§3.3) — their entity names, subjects and learned aliases — not a dictionary.

Three matchers, best score wins:

| Matcher | Catches | Mechanism |
|---|---|---|
| **Trigram similarity** | transposition, insertion, truncation | `similarity(term, token)` (`pg_trgm`) |
| **Levenshtein** | short typos, threshold scaled to length | `levenshtein()` ≤ 1 (≤4 chars), ≤ 2 (5–8), ≤ 3 (9+) |
| **Double metaphone** | ASR mis-hearings | `dmetaphone(term) = dmetaphone(token)` |

```sql
-- one indexed query resolves every candidate token in the query
with tokens as (select unnest($1::text[]) as tok)
select t.tok, l.term, l.kind, l.memory_id,
       greatest(
         similarity(l.term, t.tok),
         1 - (levenshtein(l.term, t.tok)::real / greatest(length(l.term), 1)),
         case when dmetaphone(l.term) = dmetaphone(t.tok) then 0.85 else 0 end
       ) as score
from tokens t
join user_lexicon l
  on l.user_id = $2
 and (l.term % t.tok or dmetaphone(l.term) = dmetaphone(t.tok))
order by t.tok, score desc;
```

**Acceptance rule — both conditions, not either:**

```
accept top candidate if score ≥ 0.62
                     and (score − second_score) ≥ 0.10
```

The margin condition is doing something important. If two lexicon entries score close, that is **not** a spelling problem — it is an ambiguity, and it goes to §9 instead of being silently resolved. A confident wrong repair is worse than a question, because the person never learns it happened.

Multi-token entities need a windowed pass: after single-token repair, try bigrams and trigrams against the lexicon so `read cell writeup` resolves to `RED cell writeup` as a unit rather than three bad token matches.

**Do not over-build this.** For the *semantic* half of a query, modern multilingual embeddings are already robust to minor misspellings — `membrne writeup` and `membrane writeup` embed close together. Repair exists for where exact strings matter: entity resolution, alias lookup, and structured filters. Stating this in the README makes the effort read as deliberate scoping rather than naivety.

### 7.5 Stage D — slot extraction, not parsing

Never parse for grammar. Pull **slots** from a bag of tokens:

```json
{
  "time_window": null,
  "source": null,
  "entities": ["Priya"],
  "attribute": "deadline",
  "action_verb": null,
  "payload": null,
  "semantic_residue": ""
}
```

`"priya deadline"` fills two slots and that is enough to route. No verb, no article, no problem. Word order is ignored entirely — `"deadline priya"` and `"priya's deadline"` and `"whats the deadline for priya"` all produce the same slot set. This is what makes bare-keyword input work, and it is why the router must never depend on sentence structure.

Slot sources:

- `entities` — lexicon hits from Stage C, plus capitalised unknowns (candidate new entities)
- `attribute` — match against the single-valued registry (§6) plus a small attribute vocabulary (deadline, status, owner, email, number, address)
- `source` — app names and their aliases (`slack`, `gmail`/`mail`/`email`, `wa`/`whatsapp`, `browser`, `chrome`)
- `action_verb` — a closed list: find, search, show, polish, draft, rewrite, summarise, remind, forget, remember
- `payload` — quoted text or text following a drafting verb (see §7.10)
- `semantic_residue` — everything unclaimed, which is what gets embedded

### 7.6 Stage E — focus inheritance

A fragment is usually *elliptical*, not incomplete: the missing slots were established a turn ago. Keep an ephemeral focus object in process memory or Redis.

```json
{
  "entities": ["RED cell membrane writeup"],
  "source": "slack",
  "time_window": null,
  "last_turn_at": "2026-09-12T14:21:00Z"
}
```

Rules, deliberately dumb:

- Slots absent from the current query inherit from focus.
- Focus expires after **10 minutes** of inactivity, or on explicit topic change (a new entity introduced with no pronoun or definite article).
- Pronouns (`it`, `that`, `she`, `him`, `the same`) force inheritance rather than merely permitting it. If focus is empty and a pronoun is present, that is a referent ambiguity → §9.
- Focus is **never persisted** to the memory store. It is conversation state, not a belief. Persisting it would turn a passing mention into a durable fact — exactly the noise failure mode the position rejects.
- Every inherited slot is logged, so an answer that depended on inheritance is inspectable.

### 7.7 Stage F — time expression resolution

Resolve to **windows with tolerance**, never points. A hard boundary on a vague expression is how you lose the episode the person meant.

| Input | Window |
|---|---|
| "around 5" | 16:00–18:00, day from focus or today |
| "yestrday" | 00:00–23:59 previous day |
| "couple days back" | 72 h window ending 24 h ago |
| "this morning" | 05:00–12:00 today |
| "last week sometime" | previous Mon–Sun, full |
| "just now", "abhi" | last 30 min |
| "kal" | **ambiguous** → §9 |

Use a library (`chrono-node` for JS, `dateparser` for Python) rather than hand-rolling, then widen every resolved window by ±20% before filtering.

### 7.8 Stage G — the LLM fallback parse

When the fast path is not confident, one cheap model call does the interpreting. This is what makes Kivi feel like the assistants you are used to, without paying for that on every turn.

**Trigger conditions** (any one):

- No entity resolved **and** `semantic_residue` under 3 tokens
- An `action_verb` present but no `payload` and no entity
- Stage C found matches but none cleared the acceptance rule
- The token set is dominated by unknown words (>50% not in lexicon, not stopwords)
- Detected language is non-English and the static map produced nothing

**The call.** Send the raw query, the user's entity list (names only — cheap, a few hundred tokens), the current focus, and today's date. Ask for the slot JSON directly, with an explicit instruction to return `null` for slots it cannot determine rather than guessing:

```json
{
  "system": "Extract query slots. Return only JSON. Use null for anything you cannot determine from the input — do not guess. Entity names must come from the provided list or be null.",
  "input": {
    "query": "kal priya ku enna sonnen",
    "known_entities": ["Priya Sharma", "RED cell writeup", "CRE assignment", "..."],
    "focus": {"entities": ["RED cell writeup"], "source": "slack"},
    "today": "2026-09-12"
  }
}
```

The `null`-rather-than-guess instruction matters more than it looks. A model asked to fill slots will confabulate plausible ones, and a confabulated slot is indistinguishable from a real one downstream. Returning `null` routes cleanly to clarification or abstention instead.

**Cost control:** cheap model, entity list capped at the 200 highest-frequency lexicon terms, response capped at ~150 tokens. Log tokens and cost against `stage='llm_parse'` so the eval can report what fraction of total spend the fallback accounts for.

### 7.9 Intent routing

Route on **slot shape**, never on sentence structure:

| Slots present | Intent | Capability |
|---|---|---|
| `time_window` + `source` (± residue) | `recall_episode` | C1 |
| `entity` + `attribute` | `fact_lookup` | C2/C4 |
| `entity` that is an open thread | `thread_status` | C2 |
| `action_verb ∈ {polish, draft, rewrite}` + payload or episode ref | `draft` | C3 |
| "what do you know/remember" + entity | `memory_query` | C4 |
| `forget`/`remove` + a specific belief | `delete_item` | C4 / §10 |
| entity only, nothing else | `entity_summary` | C2/C4 |
| nothing resolvable | → §7.11 rung 5 | — |

### 7.10 What must never be repaired

Repair operates on **requests**, never on **payloads**. When one utterance contains both — *"draft a slack to pritha saying the membrne data is redy"* — the request half (`draft`, `slack`, `pritha`) is repaired and routed; the payload half (`the membrne data is redy`) is passed to C3 **unrepaired**, because fixing it is drafting, not parsing, and C3 does that under the person's own style preferences.

Payload boundaries:

- Anything in quotes
- Everything following a drafting verb plus `saying` / `that` / `:` 
- Any text explicitly handed over ("polish this: …")

Getting this wrong produces a subtle and very annoying bug: Kivi silently "corrects" a deliberate spelling in a message the person is sending someone else. Per §2, that is Kivi editing what the person said, which is out of bounds.

### 7.11 The fallback ladder

Repair, clarification and abstention are one mechanism at descending confidence. This ladder is the whole of Kivi's behaviour under uncertainty:

```
1. Confident parse — all needed slots, no close-second entity
     → answer, with citations

2. Repaired parse — substitutions applied above threshold
     → answer, and show the repair inline:
       "Found it — I read 'membrne' as the membrane writeup."

3. LLM fallback parse succeeded
     → answer, citations, no special UI (it is still a parse)

4. Ambiguous — two candidates within margin, or an unfillable required slot
     → ONE clarifying question (§9)

5. No parse, but a usable semantic hit above the score floor
     → answer broadly, hedged, citations attached:
       "Not sure exactly which you mean, but on the membrane writeup you said…"

6. Nothing above the floor
     → abstain
```

Rung 2 deserves care in the UI. Showing the repair costs one clause and converts a possibly-wrong answer into a visibly correctable one — the same trust move as citation chips, and the reason a mis-repair never becomes a silent error.

### 7.12 Worked examples

| Raw input | Repairs | Slots | Route |
|---|---|---|---|
| `wat did i say abt the membrne thing yestrday` | wat→what, abt→about, membrne→**membrane writeup** (trigram .71 + phonetic) | time: prev day; entity: RED cell membrane writeup | `recall_episode` → rung 2 |
| `priya deadline` | none | entity: Priya Sharma; attribute: deadline | `fact_lookup` → rung 1 |
| `the slack one from around 5` | none | source: slack; time: 16:00–18:00 today | `recall_episode` → rung 1 |
| `pritha mail — find it` | pritha→**Pritha R** (phonetic, .85) | entity: Pritha R; source: gmail; verb: find | `recall_episode` → rung 2 |
| `where am i on the writeup` | none; **two lexicon hits within .04** | entity: ambiguous | → §9 clarification (rung 4) |
| `kal priya ku enna sonnen` | kal→AMBIGUOUS_DAY; non-English → **LLM fallback** | entity: Priya; time: null | → §9 temporal clarification |
| `draft a slack to pritha saying the membrne data is redy` | pritha→Pritha R; **payload untouched** | verb: draft; source: slack; payload: `the membrne data is redy` | `draft` → C3 |

That table is worth building into the eval as fixtures — it is the clearest possible demonstration that the layer works, and it doubles as regression tests.

### 7.13 Logging

Every query writes one `decisions` row per stage that did something:

```json
{
  "stage": "repair",
  "verdict": "applied",
  "reason": "membrne → membrane writeup via trigram 0.71 / dmetaphone match; margin 0.19",
  "detail": {
    "raw": "wat did i say abt the membrne thing yestrday",
    "normalized": "what did i say about the membrane writeup yesterday",
    "substitutions": [
      {"from":"membrne","to":"membrane writeup","method":"trigram+phonetic",
       "score":0.71,"second":0.52,"memory_id":"…"}
    ],
    "llm_fallback": false
  },
  "latency_ms": 11
}
```

The `/inspect` route (§10) renders the full chain for any query: raw input → repairs → slots → inheritance → retrieval candidates → citations → verdict. That chain is the answer to "how can an engineer inspect why memory did or did not affect a result," and §7 is the part of it most likely to be where a wrong answer actually came from.

---

## 8. Retrieval and the answer contract

### Routing

The canonical example — *"the dictation I did around 5 PM yesterday in Slack"* — is roughly 80% **structured filter**, 20% semantic. Pure vector search fails it.

1. **Structured prefilter** on episodes/memories (resolved time window, source, domain, type, `status = 'active'`, `deleted_at is null`).
2. **Vector top-k** within the filtered set (k = 20), embedding the normalised `semantic_residue`.
3. **Rerank**: `final = 0.55·cosine + 0.25·retention + 0.20·filter_exactness`.
4. **Absolute score floor**, not just top-n. Nothing above the floor is a valid, meaningful outcome.
5. Write every candidate to `retrieval_items` with `used_in_prompt` marked.

### Answer contract

```json
{
  "answer": "...",
  "citations": [{"type":"episode","id":"...","when":"Tue 4:52 PM","source":"slack"}],
  "abstained": false,
  "repairs": [{"from":"membrne","to":"membrane writeup"}],
  "clarified": false,
  "llm_parse_used": false,
  "reason": "3 supporting episodes above floor"
}
```

**Abstention rule:** if `citations` is empty, `answer` must be an admission of not knowing. Enforce in code — check the array before returning and substitute the abstention string regardless of what the model produced. A prompt instruction is a preference; a code path is a guarantee.

Citations render as inline chips: *"because you said this in Slack on Tuesday."*

---

## 9. Clarification — one question, learned once

The brief asks how Kivi behaves when its understanding is **incomplete**. This is the second and only other interaction type besides contradiction.

### 9.1 When to ask

| Type | Example | Question |
|---|---|---|
| **Entity** | two projects match "the writeup" | which one |
| **Referent** | "it"/"she" with empty or multi-valued focus | who, what |
| **Temporal** | "kal", or "Tuesday" near a week boundary | which day |
| **Intent** | "the Priya message" — find it, or draft one? | which action |

Numeric trigger: top-1 and top-2 are **distinct referents** and `final_score₁ − final_score₂ < 0.08`. Below that margin, picking one is a coin flip dressed as an answer.

### 9.2 When not to ask

- Never about sensitivity, or whether to remember something — settled by the position.
- Never when one candidate clearly wins. Guessing confidently is correct there.
- Never twice in a row. If a clarification's answer is still ambiguous, **abstain and list the candidates** rather than asking again. Two questions in a row is an interrogation, and voice makes it worse.
- Never mid-dictation.
- Budget: one clarification per turn.

### 9.3 Shape

Short, spoken-answerable, with an escape:

> Two things match "the writeup" —
> `[ RED cell membrane writeup ]  ·  [ CRE assignment writeup ]  ·  neither`

Voice answers ("the first one", "the membrane one", "red cell") resolve by fuzzy match against the option labels using the same §7.4 machinery.

### 9.4 Clarifications must decay to zero

A system that asks the same question every week is worse than one that guesses. **Every clarification writes an alias:**

```sql
insert into entity_aliases (user_id, alias, memory_id, origin, confidence)
values ($user, 'the writeup', $memory_id, 'clarification', 0.9)
on conflict (user_id, alias, memory_id)
do update set confidence = least(entity_aliases.confidence + 0.1, 1.0),
              hit_count  = entity_aliases.hit_count + 1;
```

Next time, "the writeup" resolves directly. Because `entity_aliases` feeds `user_lexicon`, clarifications also improve **spelling repair** — the alias table accumulates the exact shorthand and mis-hearings this particular person produces, so §7 gets more accurate the longer Kivi is used. That compounding is the strongest argument for building §7 and §9 as one system rather than two features.

Aliases are visible and editable in the memory surface, and an evidence row is written with `role = 'clarification'` so provenance records that the person, not the extractor, established the mapping.

**Target:** any given shorthand is clarified at most once. Measured in §11.

---

## 10. Surfaces

1. **Replay client** — the "client of your own design": feeds transcripts, app context and timestamps into the pipeline. Replay-at-speed, single-step, reset.
2. **Hey Kivi panel** — conversation with inline citation chips, visible repair notes ("read 'membrne' as the membrane writeup"), clarification prompts, and an abstention state that looks deliberate rather than broken.
3. **"What Kivi knows"** — memories grouped by domain, each with plain-language evidence and three actions: *edit*, *pin*, *forget*. **Per-item forget** is a single belief, removed on confirmation, with a 24-hour undo toast — no scope resolution, no suppression keys, no relearn semantics. Also hosts superseded items behind a "changed" filter, and learned aliases.
4. **Contradiction prompt** — inline, one question, two buttons plus "both true".
5. **`/inspect`** — the decisions log rendered, showing the full chain for any query (§7.13). Secondary route; the product is fully intelligible without it.

---

## 11. Evaluation

### Corpus (~500 records, one synthetic persona, ground truth committed as JSON)

| Class | Count | Tests |
|---|---:|---|
| Durable facts | 40 | Write recall |
| Preferences | 25 | Write recall + drafting influence |
| Named entities / projects | 12 | Entity continuity |
| Threads (3 open, 3 closed) | 6 | Lifecycle transitions |
| Transient / one-off distractors | 150 | **Deliberate ignoring** |
| Contradiction pairs | 10 | Conflict vs. difference |
| **Restricted leak canaries** | 15 | Must never be embedded |
| Cross-dictation facts (need ≥2 records) | 30 | Distributed recovery |
| Code-mixed / transliterated records | 40 | Multilingual retrieval + §7.3 |
| **Near-duplicate entity names** | 8 | Ambiguity + fuzzy matching ("two writeups", "Priya S"/"Priya R") |
| Remaining filler | ~164 | Realistic volume |

### Question sets

- **60 answerable** questions with known answers.
- **25 unanswerable** questions whose answers are genuinely absent.
- **240 perturbed variants** — four per answerable question, generated mechanically. This set is the point of §7 and is nearly free to produce:

  | Perturbation | Method |
  |---|---|
  | **Typo** | 1–2 random character edits in the key noun |
  | **Phonetic** | substitute a homophone-ish corruption of the entity name (`membrane`→`membrain`, `Pritha`→`Preetha`) |
  | **Keyword-only** | strip all function words and verbs; keep 2–3 content tokens |
  | **Code-mixed** | replace the time expression and one function word with Hindi/Tamil transliteration |

- **12 deliberately ambiguous** questions where two candidates genuinely match.
- **20 payload-safety** cases — drafting requests containing deliberate misspellings in the payload, which must survive untouched (§7.10).

### Metrics

| Metric | Target | Why |
|---|---|---|
| Write precision | ≥ 0.85 | Noise control |
| Write recall | ≥ 0.80 | Usefulness |
| Transient suppression | ≥ 0.90 | Proves ignoring |
| Retrieval hit rate @5, clean queries | ≥ 0.85 | Core function |
| **Hit rate @5, typo variants** | **≥ 0.82** | §7.4 lexical path |
| **Hit rate @5, phonetic variants** | **≥ 0.78** | §7.4 phonetic path — the ASR case |
| **Hit rate @5, keyword-only variants** | **≥ 0.75** | §7.5 slot extraction |
| **Hit rate @5, code-mixed variants** | **≥ 0.70** | §7.3 + multilingual embeddings |
| **Aggregate perturbed hit rate** | **within 5 pts of clean** | The headline §7 number |
| Entity repair precision | ≥ 0.90 | A wrong repair is worse than none |
| **Payload preservation** | **1.00** | §7.10 — never edit what the person is sending |
| **LLM fallback rate** | **0.10–0.20** | Fast path is doing real work |
| Answer groundedness | ≥ 0.90 | Honesty |
| **Abstention on unanswerable set** | **≥ 0.90** | Refusing to invent |
| False abstention on answerable set | ≤ 0.10 | Not uselessly cautious |
| **Clarification precision / recall** | ≥ 0.80 / ≥ 0.75 | Asks when it should, not when it shouldn't |
| **Repeat-clarification rate** | **≤ 0.05** | Aliases are actually learned |
| Contradiction precision / recall | ≥ 0.80 / ≥ 0.70 | Conflict vs. difference |
| **Restricted leak rate** | **0.00 — hard fail** | The entire trust claim |
| Cross-dictation recovery | ≥ 0.70 | Multi-record synthesis |
| p50 / p95 query-understanding latency | < 30 / 60 ms (fast path) | §7.1 budget |
| p50 / p95 end-to-end latency | < 400 / 1200 ms | |
| DB growth per 500 records | report | |
| Model calls + cost per 500 records, split by stage | report | Extraction vs. fallback parse vs. answer |

The bolded rows are the ones that follow most directly from the position and that almost nobody produces. The four-way perturbation breakdown in particular is worth more than a single aggregate: it shows *which* repair path carries which failure mode, which is the difference between a tuned system and a lucky one.

### Failure surfacing

The eval must print failures, not just aggregates. For every miss: raw input, repairs applied, slots resolved, whether the fallback fired, the write decision and reason, what was retrieved, what was answered. A report where failures are visible reads as far more credible than one showing only green.

---

## 12. Build order

| Phase | Work | Outcome |
|---|---|---|
| 1 | Schema + migrations + RLS + extensions + seed user | Constraints visible in `psql` |
| 2 | Corpus generator + ground-truth key + perturbation generator | 500 records, 240 perturbed questions, key committed |
| 3 | Ingestion: Stage 0 + 1 + embeddings | Leak canaries provably unembedded |
| 4 | Stages 2 + 3: extraction, scoring, candidates, alias harvesting | Memories appear; distractors do not |
| 5 | Decay + thread lifecycle + eviction | Retention behaves over simulated time |
| 6 | **§7 fast path (A–F) + lexicon view** | Perturbed queries resolve; repairs logged |
| 7 | Retrieval + fallback ladder rungs 1–2, 5–6 + answer contract | C1 and C2 work end to end |
| 8 | **§7.8 LLM fallback parse** | Code-mixed and heavily mangled queries resolve; ratio measurable |
| 9 | **§9 clarification + alias learning** | Ambiguity asked once, never twice |
| 10 | Contradiction detection + surfacing | C4 partially live |
| 11 | UI: replay client, Hey Kivi panel, memory surface, per-item forget | Usable by a normal person |
| 12 | C3 drafting + §7.10 payload protection | Memory visibly changes output; payloads untouched |
| 13 | Eval harness + report generation | Numbers, failures, cost by stage |
| 14 | README + RUN.md + reset path | Reproducible from a clean clone |

Phase 6 before 7 is deliberate — build retrieval against already-normalised queries rather than retrofitting repair afterwards. Phase 8 after 7 is also deliberate: get the cheap path's accuracy measured *before* adding a model call, or you will never know how much the fallback is actually buying you.

---

## 13. Known limitations to state openly

- Sensitivity pre-filtering is heuristic. It fails closed, so it will over-restrict and some legitimate memories will be lost. That is the deliberate trade.
- Query repair is bounded by the lexicon: a misspelled entity Kivi has never seen cannot be corrected to it. Repair helps most for things already known — the common case, but not every case.
- Double metaphone is tuned for English orthography. Transliterated Indic names ("Krishnan"/"Krishna", "Rakshith"/"Rakshit") will sometimes collide and sometimes miss; the near-duplicate-name set measures this rather than assuming it.
- The LLM fallback parse adds 400–900 ms to the queries that trigger it, so the worst-case latency a person experiences is noticeably worse than the median. The fallback rate is reported for exactly this reason.
- Session focus expires on a fixed timer, so a fragment resumed after a long gap loses inherited slots and may trigger a clarification the person considers unnecessary.
- Recurrence-based promotion delays genuinely important one-time statements by one sighting unless the extractor scores them highly on lifecycle signal.
- **Bulk forgetting is not supported.** A person can remove individual beliefs; removing an entire subject in one action is out of scope, because doing it honestly requires suppression that does not also block the person from re-stating the same fact later.
- Tier B integrations (WhatsApp Desktop, browser, filesystem) are read-only and best-effort; their metadata is less reliable than Tier A OAuth sources, which weakens time-and-source recall for those channels.
- The domain ranking is a one-time signal and never re-elicited; if someone's work changes substantially, weights lag until reinforcement catches up.

---

## 14. AI use disclosure

Part One's position — the two-axis model, the infer-silently-stay-answerable trust contract, the access-is-not-permission boundary, the weighted-not-siloed stance, and the contradiction policy — was developed independently. This document organises that position into deliverable form and adds the Part Two architecture. The original assignment deadline has passed; this build is a personal project, not a submission.
