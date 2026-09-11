# ══════════════════════════════════════════════════════════════════
# Container image for the Fargate deploy path (docs/05-deploy-fargate.md)
# ══════════════════════════════════════════════════════════════════
# Build:  docker build -t book-store-api .
# Run:    docker run -p 8000:8000 -e STORAGE=json book-store-api
# Check:  curl http://localhost:8000/health
#
# The Lambda path does NOT use this file — it ships a zip instead.
# ══════════════════════════════════════════════════════════════════

# `-slim` not `-alpine`. Alpine uses musl instead of glibc, which forces
# many Python packages to compile from source instead of using prebuilt
# wheels — slower builds and occasional runtime surprises.
FROM python:3.11-slim

# Fail fast and log immediately:
#   DONTWRITEBYTECODE — no .pyc clutter in the image
#   UNBUFFERED        — print() reaches CloudWatch right away instead of
#                       sitting in a buffer (critical when debugging)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── Dependencies FIRST, application code second ─────────────────────
# Docker caches each layer. Copying only pyproject.toml here means the
# slow `pip install` layer is reused on every rebuild where you changed
# app code but not dependencies. Copy everything at once and you
# reinstall all packages on every one-line edit.
COPY pyproject.toml ./

# --no-cache-dir keeps pip's download cache out of the final image.
# Installing the deps explicitly (rather than `pip install .`) keeps this
# simple and avoids needing a build backend in the image.
RUN pip install --no-cache-dir \
        "fastapi==0.115.0" \
        "uvicorn==0.30.6" \
        "pydantic==2.9.2" \
        "pydantic-settings==2.5.2" \
        "boto3==1.35.36"

# ── Application code ────────────────────────────────────────────────
COPY models.py config.py repository.py repo_json.py repo_dynamo.py main.py ./

# Run as a NON-ROOT user. If the app is ever compromised, the attacker
# lands as an unprivileged user instead of root inside the container.
# Container security scanners flag root-run images, and rightly so.
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER appuser

# Documentation only — EXPOSE does not publish the port. The actual
# mapping comes from `docker run -p` locally, and from the container
# port in the ECS task definition (infra-fargate.yaml) when deployed.
EXPOSE 8000

# --host 0.0.0.0 is REQUIRED and the single most common mistake here.
# The default (127.0.0.1) only accepts connections from inside the
# container, so the ALB health check gets connection-refused, the task
# is marked unhealthy, and ECS kills and restarts it forever.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
