# GlobeTrotter (Waypoint)

A multi-city travel planning app: create trips, add city stops with dates,
attach activities and costs, track budget vs. spend, view a day-by-day or
calendar itinerary, and optionally share a trip publicly.

Stack: Flask + Flask-SQLAlchemy (SQLite) on the backend, server-rendered
Jinja templates + vanilla JS on the frontend, talking to a JSON API under
`/api/*` with JWT auth.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# optional: put SECRET_KEY, DATABASE_URL, ADMIN_EMAIL, ADMIN_PASSWORD
# into a .env file — sensible defaults are used if you skip this

python seed.py                  # creates tables, seeds cities/activities,
                                 # and creates an admin login
python app.py                   # runs on http://127.0.0.1:5000
```

`seed.py` is safe to re-run — it resets catalog data (cities/activities)
without touching users or trips, and won't duplicate the admin account.

Default admin login (override with `ADMIN_EMAIL` / `ADMIN_PASSWORD` env
vars before seeding): `admin@example.com` / `changeme123` — change this
password after first login, from `/profile`.

## Screens / routes

| # | Screen | Route |
|---|---|---|
| 1 | Login / Register | `/login`, `/register` |
| 2 | Dashboard | `/dashboard` |
| 3 | Create Trip | `/trips/new` |
| 4 | My Trips | `/trips` |
| 5 | Itinerary Builder | `/trips/<id>/plan` |
| 6 | Itinerary View | `/trips/<id>` |
| 7 | City Search | `/cities` |
| 8 | Activity Search | `/activities?city_id=&stop_id=&trip_id=` |
| 9 | Trip Budget | `/trips/<id>/budget` |
| 10 | Trip Calendar | `/trips/<id>/calendar` |
| 11 | Shared Trip (public) | `/shared/<token>` |
| 12 | Profile / Settings | `/profile` |
| 13 | Admin Dashboard | `/admin` (role=admin only) |
| 14 | AI Trip Estimator | `/estimate`, `/trips/<id>/estimate` |

City/Activity Search also work as in-page modals from the Itinerary
Builder (add a stop / add an activity), in addition to their standalone
routes above.

## API

All routes are under `/api`, JWT-authenticated via
`Authorization: Bearer <token>` (obtained from `/api/auth/login` or
`/api/auth/register`), except `GET /api/public/trips/<token>` which is
intentionally open. See the blueprint files for the full route list:
`auth_routes.py`, `trip_routes.py`, `catalog_routes.py`,
`budget_routes.py`, `public_routes.py`, `admin_routes.py`,
`ai_estimate_routes.py`.

## AI Trip Estimator

`POST /api/ai/estimate` calls the Gemini API to produce an approximate
distance/cost/travel-info estimate for a route — either loaded from a
saved trip's stops (`{"trip_id": ...}`) or entered manually
(`{"cities": [...], "start_date": ..., "end_date": ...}`). It's
stateless — nothing is written to the database unless you click "Save
as this trip's budget" on the results page, which just calls the
existing `PUT /api/trips/<id>` endpoint.

Requires `GEMINI_API_KEY` (get one at https://aistudio.google.com/apikey)
in your `.env` — without it the endpoint returns a clean `501` rather
than crashing. `GEMINI_MODEL` defaults to `gemini-2.0-flash`; override
it if that model is renamed or deprecated by the time you're reading
this. The numbers Gemini returns are LLM estimates, not live pricing —
say so in the UI, don't present them as quotes.

## Known gaps / notes

- **Community tab** (browsing other users' shared trips as a feed) has
  no backend endpoint and isn't built — flagging it rather than faking
  a feed with placeholder data.
- **Cover/profile photos** are stored as a pasted image URL, or as a
  base64 data URL when uploaded from a file picker (no object storage
  is wired up). SQLite doesn't enforce the declared `VARCHAR(255)`
  length so this works for a demo, but swap in real file storage
  (S3/Cloud Storage + a proper upload endpoint) before pointing this at
  a length-enforcing database like Postgres in production.
- **Google sign-in buttons** are present in the UI but intentionally
  inert (no OAuth backend) — clicking shows a "not available yet"
  message instead of failing silently.
- The dev server (`python app.py`) is for local development only; use
  a production WSGI server (gunicorn/uwsgi) behind a real database for
  deployment.

