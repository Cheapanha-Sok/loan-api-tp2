# Loan Application Service (loan-api)

FastAPI service that scores loan default risk, deployed on every merge to `main`.

- **Live:** https://loan-api-cheapanha.onrender.com ([/docs](https://loan-api-cheapanha.onrender.com/docs), [/health](https://loan-api-cheapanha.onrender.com/health)); `/api/*` routes need an `X-API-Key` header
- **Pipeline:** merge to `main` → Render builds `Dockerfile.prod` (stage 2 runs `pytest`; a red test fails the build) → health check on `/health` → live. `scripts/verify.sh` waits until `/health` reports the merged commit's `git_sha`.
- GitHub Actions workflows (`.github/workflows/`) are kept but cannot run while the account is under a GitHub billing lock: see [evidence/6.7/github-actions-billing-lock.md](evidence/6.7/github-actions-billing-lock.md)
- Development: `pip install -r requirements-dev.txt && python train.py && pytest -v`
- Evidence: Task 4.7 [CHECKLIST.md](CHECKLIST.md) · Task 5.7 [report/](report/) · Task 6.7 [report/6.7/](report/6.7/) and [evidence/6.7/](evidence/6.7/)
