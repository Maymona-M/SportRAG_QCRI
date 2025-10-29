FROM python:3.11-slim

# Production-friendly API image. Uses repository root as build context so we
# can install project requirements.

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /api

# Install system deps needed for some Python packages (opencv/mediapipe may
# require additional OS packages on some systems; add as needed).
RUN apt-get update \
	&& apt-get install -y --no-install-recommends gcc build-essential pkg-config libgl1 libgthread-2.0-0 \
	&& rm -rf /var/lib/apt/lists/*

# Copy requirements from repository root and try to install them. If the full
# install fails (heavy packages like torch), fallback to a minimal set so the
# container can at least start for development.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt || \
	pip install --no-cache-dir flask flask-cors python-dotenv

# Ensure small but critical runtime-only packages are present even if the
# full requirements install failed (heavy packages like torch can cause
# long build times or failures in constrained environments).
RUN pip install --no-cache-dir langdetect || true
RUN pip install --no-cache-dir langchain || true
RUN pip install --no-cache-dir langchain-core || true
RUN pip install --no-cache-dir langchain langchain-community langchain-huggingface || true

# Copy source files (api/ directory) into the image. Note: compose mounts the
# host `./api` over /api at runtime in development, so keep the dev script in
# the repository to be visible to the container.
COPY api /api
# Copy sibling modules (scripts/) into a separate path so they are available
# even when the host mounts ./api over /api at runtime.
COPY scripts /opt/app/scripts
ENV PYTHONPATH=/opt/app:${PYTHONPATH:-}

EXPOSE 8000

CMD ["sleep", "infinity"]
