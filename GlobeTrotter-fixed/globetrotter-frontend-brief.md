# GlobeTrotter — frontend build brief
### For Lovable / Emergent (or any AI app builder). Paste this whole document as your build prompt.

---

## 0. App overview (paste this first)

Build **GlobeTrotter**, a responsive travel-planning web app. Users create
multi-city trips, add stops (cities) with dates, attach activities to each
stop with costs, track budget vs. actual spend, view their itinerary as a
calendar/timeline, and optionally share a trip publicly.

**Stack assumption:** React + Tailwind CSS. Talk to an existing Flask REST
API (already built and running) — do not invent a backend or mock data
beyond loading states; wire every screen to the real endpoints listed below.

**Auth:** JWT-based. On login/register, store the returned `token` (e.g. in
memory + localStorage). Every subsequent API call sends
`Authorization: Bearer <token>`. On a 401 response, clear the token and
redirect to `/login`.

**API base URL:** expose as an env var, e.g. `VITE_API_BASE_URL`, default
`http://localhost:5000/api`.

**Global layout:** persistent top nav with logo "GlobeTrotter", links to
Dashboard, My Trips, and a user avatar menu (Profile, Logout). Mobile: nav
collapses to a hamburger menu. Use a clean, warm, travel-brand palette
(avoid generic blue-SaaS look) — off-white background, one accent color,
rounded cards, generous whitespace.

---

## 1. Login / Signup screen
**Route:** `/login`, `/register`

**Layout (per wireframe):** centered card, app logo/photo circle at top,
fields below, primary action button, link to switch between login/register.

- Login fields: email, password, "Login" button, "Forgot password?" link
  (no backend endpoint yet — show a "coming soon" toast if clicked),
  link to Register.
- Register fields: full name, email, password (min 8 chars — validate
  client-side), link to Login.

**API calls:**
| Action | Endpoint | Method | Body | Success |
|---|---|---|---|---|
| Login | `/auth/login` | POST | `{email, password}` | `{token, user}` → store token, redirect `/dashboard` |
| Register | `/auth/register` | POST | `{full_name, email, password}` | `{token, user}` → store token, redirect `/dashboard` |

**Validation/errors:** show the API's `message` field inline (e.g. "That
email is already registered.", "Invalid email or password.").

---

## 2. Dashboard / Home screen
**Route:** `/dashboard`

**Layout:** banner/hero area, search bar with Group by/Filter/Sort controls
(can be non-functional placeholders for v1), "Top Regional Selections" row
of 5 city cards, "Previous Trips" row of trip cards, prominent "+ Plan a
trip" button.

**API calls:**
| Action | Endpoint | Method |
|---|---|---|
| Recent trips | `/trips` | GET → show first 3, sorted by `start_date` |
| Popular cities | `/cities?sort=popularity&limit=5` | GET |

**Notes:** "Plan a trip" button routes to `/trips/new`. Each trip card
routes to `/trips/:id`. Each city card can route to `/cities?city_id=` for
discovery (see Screen 7).

---

## 3. Create Trip screen
**Route:** `/trips/new`

**Layout:** form — trip name, start date, end date, description, optional
cover photo upload, optional total budget field, Save button. Wireframe
also shows a "Suggestion for Places to Visit" grid below the form — populate
this from the cities catalog.

**API calls:**
| Action | Endpoint | Method | Body |
|---|---|---|---|
| Create trip | `/trips` | POST | `{trip_name, start_date, end_date, description, cover_photo_url, total_budget}` |
| Suggestions grid | `/cities?sort=popularity&limit=6` | GET |

**Validation:** `end_date >= start_date` (mirror server check client-side
for instant feedback); trip_name required.

**On success:** redirect to `/trips/:id/plan` (Itinerary Builder) so the
user immediately adds stops.

---

## 4. My Trips (Trip List) screen
**Route:** `/trips`

**Layout:** search/filter/sort bar, then trips grouped into sections —
mirror the "Ongoing / Upcoming / Completed" grouping shown in the wireframe
(User Trip Listing screen). Each trip card: name, date range, stop count,
edit/view/delete actions.

**Grouping logic (client-side, from `/trips` response):**
- Ongoing: `start_date <= today <= end_date`
- Upcoming: `start_date > today`
- Completed: `end_date < today`

**API calls:**
| Action | Endpoint | Method |
|---|---|---|
| List trips | `/trips` | GET |
| Delete trip | `/trips/:id` | DELETE (confirm dialog first) |

---

## 5. Itinerary Builder screen
**Route:** `/trips/:id/plan`

**Layout (per wireframe):** repeating "Section" cards — each section is one
**Stop** (a city + date range + budget context). Each section shows date
range, and a way to add activities. "+ Add another Section" button at
bottom adds a new stop. Support reordering stops (up/down).

**API calls:**
| Action | Endpoint | Method | Body |
|---|---|---|---|
| Load trip + stops | `/trips/:id` | GET | — |
| Add stop | `/trips/:id/stops` | POST | `{city_id, arrival_date, departure_date}` |
| Update stop dates | `/stops/:stop_id` | PUT | `{arrival_date, departure_date}` |
| Reorder stop | `/stops/:stop_id/reorder` | POST | `{direction: "up"\|"down"}` |
| Delete stop | `/stops/:stop_id` | DELETE | — |
| Add activity to stop | `/stops/:stop_id/activities` | POST | `{activity_id \| custom_title, scheduled_date, start_time, cost}` |
| Update activity | `/itinerary-activities/:id` | PUT | any of `{scheduled_date, start_time, cost, custom_title}` |
| Delete activity | `/itinerary-activities/:id` | DELETE | — |

**Notes:** "select city" for a new stop should open the City Search UI
(Screen 7) as a modal/drawer, and "assign activities" should open Activity
Search (Screen 8) scoped to that stop's city. `scheduled_date` for any
activity must fall within that stop's arrival/departure range — validate
client-side and surface the server's error if violated.

---

## 6. Itinerary View screen
**Route:** `/trips/:id` (read view, distinct from the builder)

**Layout:** day-wise layout grouped by city/stop, activity blocks showing
time + cost, a toggle between calendar and list view modes.

**API calls:**
| Action | Endpoint | Method |
|---|---|---|
| Load full trip | `/trips/:id` | GET |

**Notes:** this is read-oriented — link to `/trips/:id/plan` for an "Edit"
action, and to `/trips/:id/budget` for the cost view.

---

## 7. City Search screen
**Route:** `/cities` (also usable as an embedded modal from Screen 5)

**Layout:** search bar, filter by country/region, results list showing city
name, country, cost index, popularity, "Add to Trip" button per result.

**API calls:**
| Action | Endpoint | Method | Query params |
|---|---|---|---|
| Search cities | `/cities` | GET | `q, region, country, sort (popularity\|cost\|name), limit` |

**Notes:** when opened from the Itinerary Builder as an "add stop" flow,
"Add to Trip" should call `POST /trips/:id/stops` directly with the picked
`city_id` and prompt for dates inline rather than navigating away.

---

## 8. Activity Search screen
**Route:** `/activities?city_id=` (also usable as an embedded modal from
Screen 5)

**Layout:** filter controls (category, cost, duration — duration/cost range
filters can be client-side since the API doesn't support them server-side
yet), results list with quick-view description/image, add/remove buttons.

**API calls:**
| Action | Endpoint | Method | Query params |
|---|---|---|---|
| Search activities | `/activities` | GET | `city_id (required), q, category` |
| Add to itinerary | `/stops/:stop_id/activities` | POST | `{activity_id, scheduled_date, cost}` |

**Notes:** `city_id` is required by the API — this screen only makes sense
scoped to a specific stop's city, so always arrive here with that context
(from the builder) rather than as a freestanding global search.

---

## 9. Trip Budget & Cost Breakdown screen
**Route:** `/trips/:id/budget`

**Layout:** summary cards (total budget, total spent, remaining), a
pie or bar chart of the category breakdown, average cost/day, an
overbudget alert banner if applicable, and a simple expense log with
add/edit/delete.

**API calls:**
| Action | Endpoint | Method | Body |
|---|---|---|---|
| Load budget summary | `/trips/:id/budget` | GET | returns `{total_budget, total_spent, remaining, is_overbudget, breakdown_by_category, average_cost_per_day, expenses[]}` |
| Add expense | `/trips/:id/expenses` | POST | `{category: transport\|stay\|activity\|meals\|misc, amount, expense_date, notes}` |
| Update expense | `/expenses/:id` | PUT | any of the above fields |
| Delete expense | `/expenses/:id` | DELETE | — |

**Notes:** the `activity` category in `breakdown_by_category` is
auto-computed server-side from itinerary activity costs — don't let users
manually add an "activity"-category expense for something already logged
as an itinerary activity (would double count); reserve manual expense
entry for transport/stay/meals/misc. Show the overbudget banner in a
warning color when `is_overbudget` is true.

---

## 10. Community tab screen
**Route:** `/community`

**Layout:** list of shared trips/activities with avatar, description,
search/filter/sort controls.

**API status:** **no backend endpoint exists for this yet.** Build the UI
with realistic placeholder/empty states and a TODO comment; do not fake a
working feed. Flag this back to the team as a backend gap before wiring it
up for real.

---

## 11. Shared/Public Itinerary View screen
**Route:** `/shared/:token`

**Layout:** read-only itinerary summary, "Copy Trip" button, social share
buttons (can just copy the URL to clipboard for v1).

**API calls:**
| Action | Endpoint | Method | Auth |
|---|---|---|---|
| Load public trip | `/public/trips/:token` | GET | none — public route |
| Copy trip | `/public/trips/:token/copy` | POST | required — if not logged in, prompt login first, then retry |

**On the trip owner's side** (add this control to Screen 4 or 6, e.g. a
"Share" toggle on the trip card/detail):
| Action | Endpoint | Method |
|---|---|---|
| Enable sharing | `/trips/:id/share` | POST → returns `share_path` to show/copy |
| Disable sharing | `/trips/:id/share` | DELETE |

---

## 12. User Profile / Settings screen
**Route:** `/profile`

**Layout:** editable fields (name, photo, email), language preference
dropdown, "Preplanned Trips" and "Previous Trips" sections (reuse trip
cards from Screen 4), delete-account action (behind a confirm dialog).

**API calls:**
| Action | Endpoint | Method | Body |
|---|---|---|---|
| Load profile | `/auth/me` | GET | — |
| Update profile | `/auth/me` | PUT | any of `{full_name, email, profile_picture_url, language_preference, password}` |
| Delete account | `/auth/me` | DELETE | — (confirm, then clear token and redirect `/login`) |
| Trip sections | `/trips` | GET | split client-side same as Screen 4's grouping |

---

## 13. Admin / Analytics Dashboard (optional)
**Route:** `/admin` — only render nav link / allow access if `user.role === "admin"`

**Layout:** stat cards (total users, total trips, public trips), a pie
chart of top cities, a bar chart of top activities, a users table.

**API calls:**
| Action | Endpoint | Method |
|---|---|---|
| Stats | `/admin/stats` | GET → `{total_users, total_trips, public_trips, top_cities[], top_activities[]}` |
| User list | `/admin/users` | GET |

**Notes:** both routes return 403 for non-admin users — redirect to
`/dashboard` if the API call 403s, don't just rely on client-side role
checks for security.

---

## Build order suggestion
If generating incrementally rather than all at once, this order minimizes
rework since later screens depend on earlier ones being wired up:
1. Login/Register + auth state (Screen 1)
2. Dashboard + My Trips + Create Trip (Screens 2, 3, 4)
3. Itinerary Builder + City/Activity Search as modals (Screens 5, 7, 8)
4. Itinerary View + Budget (Screens 6, 9)
5. Profile, Sharing, Calendar view (Screens 12, 11)
6. Admin (Screen 13), Community placeholder (Screen 10)
