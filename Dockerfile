# STAGE 1: Build Stage (Sehemu ya kuandaa mazingira na kusakinisha mahitaji)
FROM python:3.11-slim-bookworm AS build

WORKDIR /opt/CTFd

# Zuia utengenezaji wa .pyc files na ruhusu log zitokee mara moja (Real-time logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Sakinisha build tools zinazohitajika ku-compile baadhi ya Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libssl-dev \
        git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

# 1. Nakili requirements pekee kwanza ili kutumia Docker Cache (Inaokoa muda wa kudownload upya)
COPY requirements.txt /opt/CTFd/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 2. Nakili kodi nzima ya CTFd baada ya kusakinisha core requirements
COPY . /opt/CTFd

# 3. Sakinisha requirements za Plugins zote zilizopo
RUN for d in CTFd/plugins/*; do \
        if [ -f "$d/requirements.txt" ]; then \
            pip install --no-cache-dir -r "$d/requirements.txt"; \
        fi; \
    done;


# STAGE 2: Release Stage (Hii ndiyo image ndogo na salama itakayokuwa live)
FROM python:3.11-slim-bookworm AS release

WORKDIR /opt/CTFd

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Sakinisha tu libraries za lazima wakati wa kuendesha app (Runtime dependencies)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libffi8 \
        libssl3 \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Tengeneza user wa CTFd mapema na kuanisha folder za log/uploads
RUN useradd -u 1001 -m ctfd \
    && mkdir -p /var/log/CTFd /var/uploads \
    && chown -R 1001:1001 /var/log/CTFd /var/uploads /opt/CTFd

# Nakili mazingira ya Python (venv) kutoka kwenye Build Stage
COPY --from=build --chown=1001:1001 /opt/venv /opt/venv

# Nakili kodi ya app
COPY --chown=1001:1001 . /opt/CTFd

# Hakikisha entrypoint script inaweza kufanya kazi
RUN chmod +x /opt/CTFd/docker-entrypoint.sh

# Tumia user asiye na uwezo wa root (Security best practice)
USER 1001
EXPOSE 8000

ENTRYPOINT ["/opt/CTFd/docker-entrypoint.sh"]