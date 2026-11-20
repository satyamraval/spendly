# Spec: Login and Logout

## Overview
Make the sign-in page work and add session handling. A registered user submits email and password; the server verifies them against the stored werkzeug hash, stores the user id in the Flask session, and redirects to the profile page. Logout clears the session. This is the step that introduces authentication state, which the profile page (Step 4) and all expense routes (Steps 7–9) will rely on. Registration (Step 2) currently redirects to `/login` without signing the user in; that behaviour stays unchanged.

## Depends on
- Step 1 — Database setup (`users` table, `get_db()`)
- Step 2 — Registration (users can be created with hashed passwords)

## Routes
- `GET /login` — render the sign-in form (exists); if already logged in, redirect to `/profile` — public
- `POST /login` — verify credentials, set `session["user_id"]`, redirect to `/profile`; on failure re-render the form with an error — public
- `GET /logout` — clear the session and redirect to `/` (landing) — public (safe to call when not logged in). Replaces the current placeholder.

`/profile` stays the existing placeholder ("coming in Step 4") and is the post-login destination. No other routes change.

## Database changes
No database changes. The existing `users` table (`id`, `name`, `email UNIQUE`, `password_hash`) is sufficient.

Add one helper to `database/db.py`:
- `get_user_by_email(email)` — returns the matching `sqlite3.Row` or `None`, using a parameterised query.

## Templates
- **Create:** none
- **Modify:**
  - `templates/login.html` — repopulate the email input with the submitted value on error (`value="{{ email or '' }}"`); never repopulate the password
  - `templates/base.html` — navbar shows "Sign in" / "Get started" when logged out, and "Sign out" (linking to `url_for('logout')`) when `session.user_id` is set

## Files to change
- `app.py` — `secret_key`, `session` import, `POST /login`, `/logout`, redirect-if-logged-in
- `database/db.py` — add `get_user_by_email`
- `templates/login.html` — repopulate email
- `templates/base.html` — conditional navbar links

## Files to create
- `tests/test_login_logout.py` — pytest tests for login and logout

## New dependencies
No new dependencies. Flask's built-in signed-cookie `session` is used.

## Session and security
- `app.secret_key` read from the `SECRET_KEY` environment variable, with a clearly marked development fallback so the app still runs locally with no setup
- Store only `user_id` in the session
- Use `check_password_hash` to verify; never compare plaintext
- Use one generic error for both an unknown email and a wrong password: "Invalid email or password." (no account enumeration)
- Normalise the email (trim, lowercase) before lookup, matching registration
- Call `session.clear()` before setting `user_id` on login
- Redirect after login goes only to the fixed `/profile` route; do not honour a user-supplied `next` parameter (avoids open redirects)
- Logout via `GET` is acceptable at this stage because the placeholder route already exists as `GET`; switching to POST + CSRF is out of scope

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (verify with `check_password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Always close DB connections (`try/finally`)
- Keep Step 2 behaviour: registration still redirects to `/login` and does not log the user in
- Do not implement the profile page itself (Step 4)

## Definition of done
- [ ] `GET /login` renders the form; `/register` still works as before
- [ ] Logging in as the demo user (`demo@spendly.com` / `demo123`) redirects (302) to `/profile`
- [ ] After login, the session contains the user's id and the navbar shows "Sign out" instead of "Sign in" / "Get started"
- [ ] A wrong password and an unknown email both show exactly "Invalid email or password." and do not log in
- [ ] Email lookup is case-insensitive (`DEMO@Spendly.com` logs in)
- [ ] On error the email field keeps its value and the password field is empty
- [ ] Visiting `/login` while logged in redirects to `/profile`
- [ ] `GET /logout` clears the session, redirects to `/`, and the navbar shows "Sign in" again; calling it while logged out does not error
- [ ] A user registered through `/register` can then log in with the same credentials
- [ ] `pytest tests/test_login_logout.py` and `pytest tests/test_registration.py` both pass
- [ ] The app starts without errors and no SQL is built with string formatting
