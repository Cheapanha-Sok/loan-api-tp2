# Task 4.7 – Production-ready loan API image: evidence checklist

- **GitHub:** https://github.com/Cheapanha-Sok/loan-api-tp2
- **Docker Hub:** https://hub.docker.com/r/sokcheapanha/loan-api
- **Image:** `sokcheapanha/loan-api:1.0.0` (same image as `:latest`)
- Environment: Linux, Docker 29.8.1, Docker Compose v5.5.1, Trivy 0.69.3 (pinned, see Lesson 4.6 advisory)

All commands below were run from the repository root. Outputs are copied verbatim.

Baseline (Lesson 4.1 / 4.6 Hands-on 1) – tests pass with the dev requirements:

```
$ pip install -r requirements-dev.txt && python train.py && pytest -v
Saved model 1.0.0 to model.joblib (test AUC 0.923)
tests/test_api.py::test_health_reports_model_version PASSED              [ 20%]
tests/test_api.py::test_prediction_is_a_probability PASSED               [ 40%]
tests/test_api.py::test_amount_above_limit_is_rejected PASSED            [ 60%]
tests/test_api.py::test_create_and_read_application PASSED               [ 80%]
tests/test_api.py::test_missing_application_is_404 PASSED                [100%]
============================== 5 passed in 1.37s ===============================
```

---

## 1. Multi-stage `Dockerfile.prod`: slim base, non-root user, HEALTHCHECK

**File review** – [`Dockerfile.prod`](Dockerfile.prod):

- Two stages: `FROM python:3.12-slim AS builder` (venv in `/opt/venv`, `pip install -r requirements.txt`, `python train.py`) and a fresh `FROM python:3.12-slim` runtime stage.
- Runtime copies **only** `/opt/venv`, `model.joblib`, `main.py`, `schemas.py` – no `train.py`, no tests, no pytest.
- `RUN useradd ... appuser` + `USER appuser`.
- `HEALTHCHECK --interval=30s ...` calling `/health` with Python's built-in `urllib` (no curl needed).

**Proof:**

```
$ docker build -t loan-api:prod -f Dockerfile.prod .
$ docker run -d --name prod -p 8000:8000 loan-api:prod
738bd5630dcf977327b23b8b2a779dfcf9cf6813c63a561d36d9cdbb5c7fe7ee
$ docker exec prod whoami
appuser
$ sleep 35 && docker ps --filter name=prod
NAMES     IMAGE           STATUS                    PORTS
prod      loan-api:prod   Up 35 seconds (healthy)   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
$ docker run --rm loan-api:slim whoami   # comparison: the single-stage image runs as root
root
```

✅ `whoami` prints `appuser`; status shows `(healthy)`.

## 2. `.dockerignore` excludes Git, caches, local models and dev config

**File review** – [`.dockerignore`](.dockerignore):

```
# Git history and settings
.git
.gitignore
# Virtual environments and Python caches
.venv
venv
__pycache__
*.pyc
.pytest_cache
# Editor / dev-container config
.vscode
.devcontainer
# Models trained on the host (the image trains its own)
model.joblib
models/
# Secrets
.env
*.env
```

✅ Git (`.git`), caches (`__pycache__`, `*.pyc`, `.pytest_cache`), local models (`model.joblib`, `models/`), dev config (`.vscode`, `.devcontainer`, `.venv`) and secrets (`.env`) are all excluded. The build log's `transferring context` lines are tiny (321 B / 122 B on the rebuild) – see [`evidence/build-prod.log`](evidence/build-prod.log).

## 3. Model path configurable with `MODEL_PATH`

`main.py` reads `MODEL_PATH = os.getenv("MODEL_PATH", "model.joblib")` and the lifespan loads `joblib.load(MODEL_PATH)`.

```
$ python train.py --version 1.1.0 --out models/model.joblib
Saved model 1.1.0 to models/model.joblib (test AUC 0.923)
$ docker run -d --name prod11 -p 8000:8000 -v "$(pwd)/models:/models:ro" -e MODEL_PATH=/models/model.joblib loan-api:prod
b0d373ddd69e2ad8c5a9024b3649a2e4c71123a682e05a1baf41c0844d639ee4
$ curl -s http://localhost:8000/health
{"status":"ok","model_version":"1.1.0"}

$ docker run -d --name prod10 -p 8000:8000 loan-api:prod   # no override -> baked-in model
$ curl -s http://localhost:8000/health
{"status":"ok","model_version":"1.0.0"}
```

✅ The same image serves the mounted 1.1.0 model when `MODEL_PATH` points to it.

## 4. `compose.yaml` runs API + PostgreSQL + Adminer, API built from `Dockerfile.prod`

[`compose.yaml`](compose.yaml) – the `api` service uses:

```yaml
    build:
      context: .
      dockerfile: Dockerfile.prod
```

```
$ docker compose up -d --build
$ docker compose ps
SERVICE   IMAGE              STATUS                    PORTS
adminer   adminer:5          Up 45 seconds             0.0.0.0:8080->8080/tcp, [::]:8080->8080/tcp
api       loan-api-tp2-api   Up 40 seconds (healthy)   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
db        postgres:17        Up 45 seconds (healthy)   5432/tcp
$ curl -s http://localhost:8000/health
{"status":"ok","model_version":"1.0.0"}
$ curl -s -X POST http://localhost:8000/api/v1/predictions -H "Content-Type: application/json" \
    -d '{"amount_usd":1500,"term_months":12,"monthly_income_usd":350,"previous_loans":1,"late_payments":0}'
{"default_probability":0.095,"risk_band":"low","model_version":"1.0.0"}
HTTP 200
$ docker compose exec db psql -U loans -d loans -c "SELECT a.id, b.full_name, a.amount_usd, a.status FROM loan_applications a JOIN borrowers b ON b.id = a.borrower_id ORDER BY a.id;"
 id  |  full_name  | amount_usd |  status
-----+-------------+------------+----------
 101 | Sok Dara    |       1500 | pending
 102 | Chan Sophea |        800 | approved
 103 | Kim Vuthy   |       3000 | rejected
 104 | Sok Dara    |        500 | approved
 105 | Chan Sophea |       2000 | pending
 106 | Heng Malis  |       1200 | pending
(6 rows)
```

✅ All three services up; `db` **and** `api` are `(healthy)` (the API's health check comes from the image). `init.sql` seeded the six rows.

## 5. Image at least 40 % smaller than the full-Python variant

```
$ sed 's/^FROM python:3.12-slim$/FROM python:3.12/' Dockerfile > Dockerfile.full
$ docker build -t loan-api:slim -f Dockerfile .
$ docker build -t loan-api:prod -f Dockerfile.prod .
$ docker build -t loan-api:full -f Dockerfile.full .
$ docker images loan-api
IMAGE           ID             DISK USAGE   CONTENT SIZE   EXTRA
loan-api:full   dc6336f8be34        2.2GB          543MB
loan-api:prod   b5ff7b09b9d6        775MB          175MB
loan-api:slim   b16f2cb45041        772MB          175MB
```

Exact sizes (`docker image inspect --format '{{.Size}}'`): prod = 775,240,656 B, full = 2,197,182,742 B.

**Reduction: 1 − 775 / 2197 = 64.7 % smaller** (compressed content: 1 − 175 / 543 = 67.8 %).

✅ Well above the 40 % requirement.

## 6. No HIGH or CRITICAL findings without a note

```
$ docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.69.3 image --severity HIGH,CRITICAL loan-api:prod
loan-api:prod (debian 13.7)
===========================
Total: 47 (HIGH: 47, CRITICAL: 0)
```

Python packages: **0** findings in all 71 packages in `/opt/venv`. Secrets: none detected.
Full report: [`evidence/trivy-report.txt`](evidence/trivy-report.txt).

### What I fixed

| Finding | Action |
|---|---|
| `zlib1g` CVE-2026-85091 (heap overflow in `gz_vacate()`), CVE-2026-76844 – HIGH, fixed in `1:1.3.dfsg+really1.3.1-1+deb13u1` | **Rebuilt and fixed.** First scan reported 49 findings. `docker build --pull` was already on the newest `python:3.12-slim`, so I added `apt-get update && apt-get upgrade -y` to the runtime stage of `Dockerfile.prod`. Rescan: zlib1g gone, 49 → 47. |

### Remaining findings (no fix available yet)

Every remaining finding has Trivy status `affected` or `fix_deferred` and **no Fixed Version** in Debian 13 – they cannot be fixed by rebuilding or upgrading today. Each is a package from the Debian base image that the API never calls.

| Package(s) | CVE | Why it is acceptable for now |
|---|---|---|
| util-linux family: `util-linux`, `mount`, `bsdutils`, `login`, `libmount1`, `libblkid1`, `libuuid1`, `libsmartcols1`, `liblastlog2-2` (36 findings) | CVE-2026-76642, CVE-2026-78408, CVE-2026-78409, CVE-2026-78410 | All four are about `mount` / `nsenter` privilege handling. The container runs as non-root `appuser`, has no mount capability (Docker's default seccomp/capabilities) and the app never runs `mount` or `nsenter`. No Debian fix yet. |
| `libacl1` | CVE-2026-54369 | Symlink-traversal privilege escalation in ACL tools; needs a privileged caller. The app runs as `appuser` and never manipulates ACLs. No Debian fix yet. |
| `libncursesw6`, `libtinfo6`, `ncurses-base`, `ncurses-bin` (4) | CVE-2025-69720 | Buffer overflow when parsing terminal data. The API is a headless HTTP server with no terminal UI and never processes untrusted terminfo. No Debian fix yet. |
| `libsqlite3-0` (3) | CVE-2026-119373, CVE-2026-119374, CVE-2026-119379 | Need a crafted FTS5 index or session changeset. The API does not use SQLite at all (in-memory dict; PostgreSQL in its own container). No Debian fix yet. |
| `libsystemd0`, `libudev1` (2) | CVE-2026-16742 | Local privilege escalation in `systemd-homed`, which is not installed or running in the container. No Debian fix yet. |
| `perl-base` | CVE-2026-9538 | DoS in Perl's `Archive::Tar` on crafted tar files. The app never runs Perl or opens tar files. Debian status `fix_deferred`. |

**Plan:** rescan regularly and rebuild with `docker build --pull` as soon as Debian ships fixes, then publish a new version tag.

## 7. Image published as `sokcheapanha/loan-api:1.0.0` and `:latest`

```
$ DOCKER_USER=sokcheapanha
$ docker tag loan-api:prod $DOCKER_USER/loan-api:1.0.0
$ docker tag loan-api:prod $DOCKER_USER/loan-api:latest
$ docker push $DOCKER_USER/loan-api:1.0.0
The push refers to repository [docker.io/sokcheapanha/loan-api]
02a25d4242cb: Pushed
05e0eee5572e: Pushed
...
de8307d3bbbb: Pushed
1.0.0: digest: sha256:b5ff7b09b9d694902f867aeb18738523b54171d3adb0c3349a39f564b42101ff size: 856
$ docker push $DOCKER_USER/loan-api:latest
The push refers to repository [docker.io/sokcheapanha/loan-api]
68bced9e0afa: Layer already exists
...
db6065057594: Layer already exists
latest: digest: sha256:b5ff7b09b9d694902f867aeb18738523b54171d3adb0c3349a39f564b42101ff size: 856

$ curl -s "https://hub.docker.com/v2/repositories/sokcheapanha/loan-api/tags"   # name, size, digest
latest 174723521 sha256:b5ff7b09b9d694902f867aeb18738523b54171d3adb0c3349a39f564b42101ff
1.0.0  174723521 sha256:b5ff7b09b9d694902f867aeb18738523b54171d3adb0c3349a39f564b42101ff
```

Docker Hub repository page: https://hub.docker.com/r/sokcheapanha/loan-api/tags – shows both `1.0.0` and `latest`, same digest and size.

---

## Pull and run from the registry (no local files)

```
$ docker compose down
$ docker rmi sokcheapanha/loan-api:1.0.0 sokcheapanha/loan-api:latest loan-api:prod loan-api:slim loan-api:full loan-api-tp2-api
Untagged: sokcheapanha/loan-api:1.0.0
Untagged: sokcheapanha/loan-api:latest
...
$ docker images sokcheapanha/loan-api
IMAGE   ID             DISK USAGE   CONTENT SIZE   EXTRA
$ cd /tmp   # a folder with no project files
$ docker run --rm -p 8000:8000 sokcheapanha/loan-api:1.0.0
Unable to find image 'sokcheapanha/loan-api:1.0.0' locally
1.0.0: Pulling from sokcheapanha/loan-api
...
Digest: sha256:b5ff7b09b9d694902f867aeb18738523b54171d3adb0c3349a39f564b42101ff
Status: Downloaded newer image for sokcheapanha/loan-api:1.0.0
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)

$ curl -s -X POST http://localhost:8000/api/v1/predictions -H "Content-Type: application/json" \
    -d '{"amount_usd":1500,"term_months":12,"monthly_income_usd":350,"previous_loans":1,"late_payments":0}'
{"default_probability":0.095,"risk_band":"low","model_version":"1.0.0"}
HTTP 200
```

(Layers shared with the `python:3.12-slim` base were still cached and show "Already exists"; the application layers were downloaded from Docker Hub.)

Screenshot of `/docs` with the 200 response: [`screenshots/step4-docs-200.jpg`](screenshots/step4-docs-200.jpg)

---

## No secrets in the image or repository

- No `ENV`/`COPY` of passwords or tokens in either Dockerfile; Trivy secret scan found nothing in the image.
- `.env` files are listed in `.dockerignore`.
- Docker Hub login used a personal access token at the terminal; it is not stored in the repository.
- The only password in the repository is the **development-only** PostgreSQL password `loans_dev_only` in `compose.yaml` (the allowed exception).
