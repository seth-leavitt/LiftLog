# Greenfield LiftLog (Web-First) Roadmap

## Product Goals

- **Portable web app** (PWA-first) that feels instant and works offline.
- **Fast food lookup** via OpenFoodFacts with smart caching and autocomplete.
- **Daily logging** equivalent to MyFitnessPal (meals + macros + custom foods).
- **Weight tracking** with simple plotting and **easy data access** for analysis.
- **Server-side predictions** from user data with results synced to client.

## Core MVP Scope

### 1) Food Search & Logging
- Search OpenFoodFacts with typeahead + barcode scan support.
- Display nutrition facts, serving sizes, and brands.
- Log foods to a day/meal (breakfast/lunch/dinner/snacks).
- Support **custom foods** and **manual nutrition entries**.
- Favorites + recently used foods for speed.

### 2) Daily Diary
- Day view with macro totals (calories, protein, carbs, fat).
- Meal sections with individual items and totals.
- Quick add for common foods.
- Edit / delete entries.

### 3) Weight Tracking
- Simple plotting (line chart) of weight over time.
- Add/edit/remove weight entries.
- Show 7/30/90 day summaries.

### 4) Data Access & Export
- One-click export of all user data (CSV/JSON).
- Read-only API token for analysis tooling.
- Optional webhooks for exporting updates.

## Technical Architecture (Suggested)

### Frontend
- **Web app (PWA)**: Next.js (App Router) with PWA support.
- **State management**: Zustand or Redux Toolkit.
- **Charting**: lightweight library (e.g., uPlot or Chart.js).
- **Offline support**: service worker + IndexedDB for recent lookups and logs.
- **Performance**: route-based code splitting, prefetching, and optimistic UI.

### Backend
- **API**: Node.js (Fastify) with background job processing.
- **Database**: Postgres (Supabase/Neon) with row-level security.
- **Caching**: Redis for OpenFoodFacts responses and frequent queries.
- **Search**: local index for recently fetched foods + trigram search for custom foods.
- **Auth**: email + magic link, OAuth (Google/Apple) optional.

### OpenFoodFacts Integration
- Use OpenFoodFacts search endpoints with tight caching to avoid latency.
- Normalize responses into internal `food` model.
- Store **food snapshots** at log time to preserve nutrition values.
- Provide barcode lookup endpoint (fast path).

## Data Model (Conceptual)

### Users
- `user_id`, `email`, `created_at`

### Foods (normalized)
- `food_id`, `source` (openfoodfacts/custom), `name`, `brand`, `barcode`,
  `serving_size`, `serving_unit`, `nutrients_json`, `created_at`

### Food Logs
- `log_id`, `user_id`, `date`, `meal`, `food_id`, `quantity`,
  `serving_size`, `nutrients_snapshot_json`, `created_at`

### Weight Entries
- `entry_id`, `user_id`, `date`, `weight`, `unit`, `created_at`

### Exports / API Tokens
- `token_id`, `user_id`, `scope`, `created_at`, `revoked_at`

### Prediction Jobs
- `job_id`, `user_id`, `status`, `input_snapshot_json`, `result_json`, `created_at`, `completed_at`

### Prediction Results
- `result_id`, `user_id`, `date`, `metrics_json`, `created_at`

## API Surface (Draft)

### Food
- `GET /foods/search?q=&page=`
- `GET /foods/barcode/:barcode`
- `POST /foods/custom`

### Diary
- `GET /diary/:date`
- `POST /diary/:date/entries`
- `PATCH /diary/entries/:id`
- `DELETE /diary/entries/:id`

### Weight
- `GET /weight`
- `POST /weight`
- `PATCH /weight/:id`
- `DELETE /weight/:id`

### Export / Data Access
- `GET /export/json`
- `GET /export/csv`
- `POST /tokens`
- `DELETE /tokens/:id`

### Predictions
- `POST /predictions/run`
- `GET /predictions/:id`
- `GET /predictions/latest`

## Performance & UX Considerations

- **Speed-first search**: cache hot queries, debounce, and return results under 200ms.
- **Offline mode**: allow logging and weight entry while offline, sync later.
- **Data consistency**: snapshot nutrients on log so historic totals remain stable.
- **Cold start**: prefetch last 7 days of logs + favorites on load.
- **Async predictions**: run jobs server-side, notify client via polling or websockets/SSE.

## Milestones

1. **Foundation**: auth + user profile + diary view + weight chart.
2. **Food search**: OpenFoodFacts integration + favorites + logging.
3. **Predictions**: server-side job runner + results sync to client.
4. **Export**: CSV/JSON export + API token management.
5. **Polish**: PWA offline mode + performance tuning.

## Decisions Needed (Before Implementation)

- Choose stack (React + Vite vs Next.js, Node vs .NET).
- Decide on hosting (Vercel/Netlify + Supabase, or single provider).
- Determine how nutrition totals are calculated (per serving vs per 100g).
- Define privacy + data retention policy.
