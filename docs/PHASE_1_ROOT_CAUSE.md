# Phase 1 authentication root-cause report

## The original failure

The member login API returned a successful response, but the browser remained on `/login`. The frontend router had no authenticated `/login` destination in the old shell, so the wildcard route rendered the public Not Found page. This made a successful login look like a failed login.

The underlying access model also relied on a single legacy `users.role` value and a signed cookie. That combination could not support server-side session revocation, multi-role memberships, or immediate deactivation enforcement.

## Correction

Phase 1 now:

- redirects successful activation/login into `/app/dashboard`;
- calls `/api/v1/auth/me` to restore the session on refresh;
- stores only an opaque session-token hash in `sessions`;
- resolves access from school-scoped memberships and role assignments;
- enforces permissions on the server and mirrors them in the React route guards;
- revokes every active session when an account is deactivated;
- returns a structured error envelope with a request ID for diagnostics.

The legacy `/api/v1/me` route remains temporarily for compatibility with the existing vertical-slice tests, but new frontend code uses `/api/v1/auth/me`.

## Regression coverage

`backend/tests/test_phase1_auth.py` covers successful login and refresh, logout/revocation, invitation state transitions, generic credential errors, multi-role permissions, admin boundaries, deactivation, token-hash storage, and rate limiting. The frontend auth test suite continues to cover safe redirects and route behavior.
