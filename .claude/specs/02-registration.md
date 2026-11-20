# Spec: Registration

## Overview
Turn the static registration page into a working sign-up flow. A visitor submits name, email and password; the server validates the input, hashes the password, creates a row in `users`, and redirects to the login page. This is the first step that writes real user data and is required before login/logout (Step 3) can exist.

## Depends on
- Step 1 — Database setup (`users` table, `get_db()`, `init_db()`)

## Routes
- `GET /register` — render the registration form (already exists, unchanged) — public
- `POST /register` — validate form, create the user, redirect to `/login` on success; re-render the form with an error message on failure — public

Same URL, so `app.py` changes the existing `register` view to `methods=["GET", "POST"]`.

## Database changes
No database changes. The existing `users` table (`name`, `email UNIQUE`, `password_hash`, `created_at`) is sufficient. Duplicate emails are enforced by the existing UNIQUE constraint.

Add one helper to `database/db.py`:
- `create_user(name, email, password)` — hashes the password with werkzeug, inserts the row with a parameterised query, returns the new user id. Raises `sqlite3.IntegrityError` on a duplicate email.

## Templates
- **Create:** none
- **Modify:** `templates/register.html`
  - Keep the existing `{% if error %}` block
  - Re-populate `name` and `email` inputs with submitted values on error (`value="{{ name or '' }}"`); never re-populate the password
  - Form `action` stays `/register` (or `url_for('register')`)

## Files to change
- `app.py` — accept POST on `/register`, validation, call `create_user`, redirect
- `database/db.py` — add `create_user`
- `templates/register.html` — repopulate fields

## Files to create
- `tests/test_registration.py` — pytest tests for the registration flow (pytest and pytest-flask are already in `requirements.txt`)

## New dependencies
No new dependencies.

## Validation rules
Applied server-side in the POST handler (the HTML `required` attributes are not sufficient):
- `name`: required, trimmed, non-empty
- `email`: required, trimmed, lowercased, must contain `@` with text on both sides and a `.` in the domain part
- `password`: required, minimum 8 characters (matches the form placeholder)
- Email already registered → error "An account with this email already exists."
- Each failure re-renders `register.html` with status 200 and a single clear `error` message

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never use string formatting in SQL
- Passwords hashed with werkzeug (`generate_password_hash`); never store or log plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Catch `sqlite3.IntegrityError` for duplicate emails rather than only pre-checking, to avoid races
- Always close the DB connection (`try/finally`)
- Do not log the user in on registration; sessions arrive in Step 3. Redirect to `url_for("login")`
- Do not add a `secret_key` or flash messages in this step

## Definition of done
- [ ] `GET /register` still renders the form
- [ ] Submitting a valid name, email and 8+ character password creates a row in `users` and redirects (302) to `/login`
- [ ] The stored `password_hash` is not the plaintext password and verifies with `check_password_hash`
- [ ] Registering the same email again (including different letter case) shows "An account with this email already exists." and creates no second row
- [ ] Empty name, invalid email, or password shorter than 8 characters each show an error and create no row
- [ ] On error, the name and email fields keep their submitted values and the password field is empty
- [ ] The seeded demo user (`demo@spendly.com`) still exists and is unaffected
- [ ] `pytest tests/test_registration.py` passes
- [ ] The app starts without errors and no SQL is built with string formatting
