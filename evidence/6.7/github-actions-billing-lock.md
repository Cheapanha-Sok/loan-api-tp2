# Incident: GitHub Actions blocked by an account billing lock

**Date:** 2026-11-12 · **Repository:** `Cheapanha-Sok/loan-api-tp2` (public)

## What happened

Lesson 6.2 (CI) and 6.3 (GHCR publish) were implemented in `.github/workflows/ci.yml` and
`.github/workflows/publish.yml` and pushed in pull request #1. The `test` job never started:

> The job was not started because your account is locked due to a billing issue.

- Run: https://github.com/Cheapanha-Sok/loan-api-tp2/actions/runs/43249948837
- 6 attempts (the original run plus 5 re-runs), the last at 16:15 UTC; every attempt failed the same way in under 10 seconds,
  before any step ran (no log output, the runner was never assigned).
- Screenshot: `screenshots/00-actions-billing-lock.jpg`

## What we checked

| Page | Finding |
|---|---|
| Billing overview | Plan **GitHub Free**, $0.00/month, current metered usage $0, nothing due |
| Actions usage | $0 of $12.00 included compute used; 0 GB of 0.5 GB storage |
| Payment information | No payment method on file |
| Payment history | "You have not made any payments." |
| Budgets and alerts | Five account budgets at **$0.00** (Actions, Packages, Codespaces, Git LFS, AI credits), each shown as "100% · Usage blocked" (`screenshots/00-billing-budgets.jpg`) |
| Repository visibility | Public (`"private": false` from the GitHub API), so Actions minutes should be free |

There is no unpaid invoice or failed card. The lock is an account-level flag on GitHub's side; the
$0 "Usage blocked" budgets on Actions/Packages are the most likely trigger. CI had worked on this
account earlier in the course, so the flag is recent.

## Impact on the capstone

GitHub Actions and GitHub Container Registry (which is pushed from Actions) are unavailable, so the
course pipeline (`test -> build-and-push -> deploy -> verify`) cannot run.

## Workaround used

The same stages run on **Render's own Git-backed build pipeline** (free plan, no card):

| Course stage (GitHub Actions) | Replacement |
|---|---|
| `test` job (pytest on a clean runner) | `test` stage inside `Dockerfile.prod`: `python train.py && pytest` runs on Render's clean builder; a failing test fails the build and nothing is deployed |
| `build-and-push` to GHCR | Render builds `Dockerfile.prod` from the repository on every push to `main` |
| `deploy` via deploy hook | Render auto-deploy on every commit to `main` (never deployed by hand) |
| `verify` (`/health` shows the SHA) | Render's health check on `/health` gates the release; `/health` reports `git_sha` from `RENDER_GIT_COMMIT`; `scripts/verify.sh` polls until the live SHA equals the merged commit and prints the merge-to-live time |
| Branch protection requiring `test` | **Not possible** without a CI status check. Changes still go through pull requests. |

`ci.yml` and `publish.yml` are kept in the repository unchanged, so the course pipeline works again
as soon as GitHub lifts the lock.

## Follow-up

- Contact GitHub Support (Billing): "Actions jobs not starting: account is locked due to a billing issue", with the run link above.
- Once unlocked: re-run PR #1, enable branch protection on `main` requiring `test`, add `pipeline.yml` (Lesson 6.5).
