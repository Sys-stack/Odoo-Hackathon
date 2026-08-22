# GlobeTrotter backend fixes — how to apply

## 1. Critical bug fix (apply this first)
`auth_utils.py` had a bug: `generate_token()` set the JWT `sub` claim to an
integer (`user.user_id`). Current PyJWT requires `sub` to be a string, so
**every login/register token was silently failing verification** — any
authenticated request would return 401. This is fixed in the patch.

## 2. New endpoints added
- **Budget & expenses** (`budget_routes.py`) — powers Screen 9 (Trip Budget &
  Cost Breakdown):
  - `GET /api/trips/<id>/budget` — total spent, remaining, category
    breakdown (transport/stay/activity/meals/misc), average cost/day,
    overbudget flag
  - `POST /api/trips/<id>/expenses`, `PUT/DELETE /api/expenses/<id>`
- **Public sharing** (`public_routes.py`) — powers Screen 11 (Shared/Public
  Itinerary View):
  - `POST /api/trips/<id>/share` — turns on sharing, issues a token
  - `DELETE /api/trips/<id>/share` — turns off sharing
  - `GET /api/public/trips/<token>` — unauthenticated read-only view
  - `POST /api/public/trips/<token>/copy` — "Copy Trip" button, clones into
    the logged-in user's account
- **Profile management** (`auth_routes.py`) — powers Screen 12 (User
  Profile / Settings):
  - `PUT /api/auth/me` — update name, email, photo, language, password
  - `DELETE /api/auth/me` — delete account (cascades to owned trips)
- **Admin analytics** (`admin_routes.py`) — powers Screen 13 (Admin
  Dashboard):
  - `GET /api/admin/stats` — user/trip counts, top cities, top activities
  - `GET /api/admin/users` — user list
  - Both require `role == "admin"` on the JWT (new `admin_required`
    decorator in `auth_utils.py`). To make a user an admin, set
    `role='admin'` directly in the `users` table for now — there's no
    promote-to-admin endpoint by design (shouldn't be self-service).
- `total_budget` is now accepted on trip create/update and returned in trip
  responses (previously in the DB model but never exposed).

## How to apply
1. Copy `budget_routes.py`, `public_routes.py`, and `admin_routes.py` into
   the root of your repo (same level as `app.py`).
2. Apply the patch for the modified files:
   ```
   cd Odoo-Hackathon
   git apply /path/to/backend_fixes.patch
   ```
   If `git apply` complains about whitespace, try
   `git apply --whitespace=fix backend_fixes.patch`. If it still fails,
   the diffs are small — open `backend_fixes.patch` and apply the hunks by
   hand to `app.py`, `auth_routes.py`, `auth_utils.py`, `setup.py`,
   `trip_routes.py`.
3. Delete `instance/waypoint.db` so it rebuilds with the updated schema
   (adds `to_dict()` support for `Expense`, cascade delete on `User.trips`),
   then re-run your seed script if you have one.
4. `python app.py` and re-test login — you should now get a 200 back from
   any authenticated route instead of a silent 401.

## Page routes added (need matching templates)
`app.py` now routes to templates that don't exist yet — you'll need to
create these (or point the frontend brief's screens at them):
`trip-budget.html`, `trip-calendar.html`, `city-search.html`,
`activity-search.html`, `shared-trip.html`, `profile.html`, `admin.html`.
