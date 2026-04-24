# Libya CARA

**Comprehensive Assessment of Risk Analytics — Libya national and subnational risk dashboard**

Libya CARA is a bilingual (Arabic primary, English secondary) subnational
disaster and crisis risk assessment platform for Libya. It produces a
headline INFORM Risk Index score at the national level and across 106
municipalities, decomposed into the three INFORM pillars (Hazard &
Exposure, Vulnerability, Lack of Coping Capacity) and into 34 individual
indicators with full data provenance and "data not available" handling.

This is an operational, jurisdiction-specific deployment, not a generic
template. It was forked from a US-state template implementation in 2026
and rebuilt around Libya-specific data sources, governance terminology,
and the bilingual RTL UI.

## Status

- **Deployment scope:** Libya — national level (LY) plus 106 verified
  municipalities (52 west, 34 east, 20 south).
- **Methodology:** INFORM Risk Index 2024
  (`https://drmkc.jrc.ec.europa.eu/inform-index`), aligned with the
  Sendai Framework for Disaster Risk Reduction 2015-2030.
- **Risk formula:** geometric mean of the three pillars,
  `(Hazard x Vulnerability x Coping)^(1/3)`, calculated in
  `routes/dashboard.py::_run_pillars()` and pinned by automated tests
  in `tests/test_inform.py`.
- **Access:** restricted. The application is gated behind the
  `CARA_ACCESS_PASSWORD` session secret and is intended for official
  Libyan government use only. It is not a public website.
- **Languages:** Modern Standard Arabic (primary, RTL) and English
  (secondary, LTR) on every page, every dashboard tile, every action
  plan item, and every methodology note.
- **Out of scope by design:** the armed-clashes / political-violence
  domain present in the upstream INFORM model is intentionally omitted
  from the published risk score. The legacy US-specific
  active-shooter, NCES, and Gun Violence Archive components have been
  fully removed.

## What you get

- A national dashboard at `/dashboard/LY` and a per-municipality
  dashboard at `/dashboard/<jurisdiction_id>` (e.g. `/dashboard/LY-063`
  for Misrata).
- A bilingual three-tier action plan at
  `/action-plan/<jurisdiction_id>` covering 11 INFORM-component
  domains with 0-3 month, 3-12 month, and 1-3 year timelines, mapped
  to UN Cluster leads, Libyan government counterparts, and Sendai
  priorities.
- Per-indicator transparency popovers showing the raw upstream value,
  the formula used, the data source, and a green "محلي / Local" or
  amber "وطني / National" badge indicating whether a measurement is a
  direct municipal upload or a country-level proxy applied to the
  municipality.
- A bilingual methodology page (`/methodology`) and a data-sources
  page (`/data-sources`) listing every connector with its license,
  refresh cadence, and license-reference URL.
- A JSON API at `/api/jurisdictions` returning the canonical
  municipality list. `/api/municipalities` is kept as a synonym.

## Data sources (Libya profile)

| Source | Use | Key required |
|---|---|---|
| WHO GHO and WHO Libya via HDX | Health metrics, capacity indicators | No |
| EM-DAT (CRED / UCLouvain) | Disaster history | Free registration |
| IDMC via HDX | Internal displacement (IDPs, returnees) | No |
| IOM DTM via HDX | Mobility tracking, displacement flows | No |
| OCHA Libya 3W via HDX | Humanitarian operational presence | No |
| UNHCR Libya via HDX | Refugees and asylum-seekers | No |
| HeiGIT | Healthcare and water-point accessibility | No |
| World Bank Open Data | Socioeconomic and infrastructure indicators | No |
| OpenAQ | PM2.5 and other air-quality measurements | No (optional key for higher rate limits) |
| NOAA GSOD | Climate / extreme heat | No (optional token) |
| GADM | Administrative boundaries | No |
| ACLED | Conflict-event reference data (not scored) | Free registration |
| Libya MoH / NCDC / COI | National reference figures | Manual import |

Refresh cadence is set per-connector in
`config/profiles/libya.yaml` and runs via APScheduler when the
`CARA_PROFILE=libya` environment variable is set. The two scheduled
jobs are `refresh_libya_hdx` (every 7 days) and `refresh_libya_global`
(every 30 days).

## Repository layout

```
app.py                        Flask app factory, session config, login gate
main.py                       gunicorn entry point
models.py                     SQLAlchemy models (audit log + uploads)
routes/
  public.py                   Home, methodology, data-sources, about, /login
  dashboard.py                Dashboard + action plan + INFORM pillar pipeline
  api.py                      JSON endpoints
  admin/                      Restricted upload + audit-log views
utils/
  domains/                    12 domain modules (3 pillars + 9 sub-domains)
  connectors/worldwide/       Per-source data connectors (HDX, WHO, IDMC, ...)
  geography/                  Jurisdiction manager, GADM lookups
  action_plan_content.py      Bilingual action-plan templates
  local_overrides.py          Municipal upload override engine
config/
  jurisdiction.yaml           Country wiring (Libya)
  risk_weights.yaml           Per-pillar / per-domain weights
  profiles/libya.yaml         Libya scheduler + connector profile
data/
  libya_municipalities.json   Authoritative 106-municipality list
  cache/                      On-disk caches per connector
templates/                    Jinja2 templates (Arabic + English, RTL)
static/css/                   Bootstrap 5 RTL build + custom CSS
static/js/cara-libya.js       The single bundled front-end script
tests/                        pytest suite (44 tests)
```

## Quick start (local development)

```
git clone https://github.com/jdn63/CARA-libya.git
cd CARA-libya

# Required secrets (do not commit these)
export CARA_ACCESS_PASSWORD="<set a strong shared password>"
export SESSION_SECRET="<random 64+ char string>"
export DATABASE_URL="postgresql://..."

# Optional: activate the Libya scheduled refreshes
export CARA_PROFILE=libya

pip install -r requirements.txt
gunicorn --bind 0.0.0.0:5000 main:app
```

The app serves on port 5000. Visit `/login` first.

On Replit the equivalent workflow is configured in `.replit` as
"Start application" and runs `gunicorn --bind 0.0.0.0:5000
--reuse-port --reload main:app`.

## Tests

```
pytest -q
```

The current suite contains 44 tests across three files:

- `tests/smoke_test.py` — domain-class load and shape checks.
- `tests/test_inform.py` — INFORM cube-root composition, banding cut
  points (very_low / low / medium / high / very_high), and an
  end-to-end fixture pinning the headline national score.
- `tests/test_login_redirect.py` — open-redirect regression tests
  for the `next=` parameter on `/login`.

## Operations

- All seven public smoke routes (`/`, `/login`, `/dashboard/LY`, a
  municipality dashboard, `/data-entry/master`, `/api/jurisdictions`,
  `/health`) must return HTTP 200 before any deploy.
- Audit events are written via `utils.logging_config.audit(event, **fields)`
  to the `audit_event` table. Log in / failed login / municipal upload
  events are all captured.
- API keys, where used, are validated through `utils/api_key_manager.py`,
  which redacts secret values out of all log output and cached error
  messages.

## License

GNU Affero General Public License v3.0 (AGPLv3). See `LICENSE`.

Network-accessible deployments must make their complete source code
available to users.

## Citation

Originally developed and maintained by Jaime Niedermeier. If you use
Libya CARA in a publication or policy document, please cite this
repository and the INFORM Risk Index methodology.
