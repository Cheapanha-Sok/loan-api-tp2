# Step 1: Live `/openapi.json` vs the Module 2 contract

- Contract: `lab_2/2.7/loan-api.yaml` (Task 2.7, OpenAPI 3.0.3, server `https://loans.example.com/api/v1`)
- Live: `https://loan-api-cheapanha.onrender.com/openapi.json` (saved as `live-openapi.json`)

| Contract (Module 2) | Live service | Result |
|---|---|---|
| `POST /applications`: 201 + `Application` + `Location` header, 422 on a business rule | `POST /api/v1/applications`: 201 + `Application`, 422 when `amount_usd` > 5000; `Location` header added in PR #2 | **Match** (after PR #2) |
| `GET /applications` (paged, `ApplicationList` with `next_cursor`) | `GET /api/v1/applications` returns a plain list | **Changed on purpose**: in-memory store from Module 3, no pagination yet |
| `GET /applications/{application_id}`: 200 / 404 | `GET /api/v1/applications/{application_id}`: 200 / 404 | **Match** |
| `PATCH /applications/{application_id}` (approve/reject, 409 if decided) | not implemented | **Deferred**: manager dashboard is out of scope for the course build |
| `GET /borrowers/{borrower_id}/applications` | not implemented | **Deferred**: needs the PostgreSQL store (stretch goal) |
| `POST /applications/{application_id}/predictions`: run the model on a stored application | `POST /api/v1/predictions` scores features directly; every created application also embeds its `prediction` | **Changed on purpose**: Module 3 design, so the model can be called without storing an application |
| `ApplicationCreate` requires `borrower_id`, `amount_usd`, `term_months` | also requires `monthly_income_usd`, `previous_loans`, `late_payments` | **Changed on purpose**: the risk model (Module 3/5) needs all five features to score an application |
| — | `GET /health` (`status`, `model_version`, `git_sha`) | **Added**: required by Render's health check and the verify stage |
| Security: Bearer token in `Authorization` on every endpoint | `X-API-Key` header on every `/api/` route when `API_KEY` is set (Lesson 6.6); `/health` and `/docs` stay open | **Changed on purpose**: one shared service key, not per-user tokens |
| Base path `/api/v1` (in `servers`) | Routes carry `/api/v1` in the path | **Match** (same URLs) |

**Summary:** the three endpoints the course implemented (create, list, get one) match the contract's paths, methods, status codes and schemas (`LoanFeatures` limits `amount_usd` 100 to 5000, `term_months` in {3, 6, 12, 18, 24}). The differences are deliberate scope decisions: pagination, approve/reject and the borrower view are not built yet, prediction is a standalone endpoint, and authentication is an API key instead of Bearer tokens.
