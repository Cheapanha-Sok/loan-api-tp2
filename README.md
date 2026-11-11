# Loan Application Service (loan-api)

FastAPI service that scores loan default risk, packaged as a production Docker image.

- Production image: `docker run --rm -p 8000:8000 sokcheapanha/loan-api:1.0.0` → open http://localhost:8000/docs
- Full stack (API + PostgreSQL + Adminer): `docker compose up -d --build`
- Development: `pip install -r requirements-dev.txt && python train.py && pytest -v`
- Evidence for Task 4.7: [CHECKLIST.md](CHECKLIST.md)
