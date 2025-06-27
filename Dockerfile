# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir -r requirements-prod.txt

# Production stage
FROM python:3.11-slim as production

# Security: Create non-root user and docker group
RUN groupadd -r wakedock && useradd -r -g wakedock -d /app -s /bin/bash wakedock \
    && groupadd -g 999 docker && usermod -aG docker wakedock

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    gosu \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

# Install Docker CLI (security: specific version and verification)
ARG DOCKER_VERSION=24.0.7
RUN curl -fsSL "https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VERSION}.tgz" -o docker.tgz \
    && tar -xzf docker.tgz --strip-components=1 -C /usr/local/bin docker/docker \
    && rm docker.tgz \
    && chmod +x /usr/local/bin/docker

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code with proper ownership
COPY --chown=wakedock:wakedock src/ ./src/
COPY --chown=wakedock:wakedock config/ ./config/
COPY --chown=wakedock:wakedock test_config.py ./test_config.py
COPY --chown=wakedock:wakedock health_check.py ./health_check.py
COPY --chown=root:root docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# Make entrypoint script executable
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/logs && \
    chown -R wakedock:wakedock /app/data /app/logs && \
    chmod 755 /app/data /app/logs

# Security: Set environment variables
ENV PYTHONPATH=/app/src \
    WAKEDOCK_CONFIG_PATH=/app/config/config.yml \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Security: Drop privileges
USER wakedock

# Expose port
EXPOSE 8000

# Health check with improved security
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Security labels
LABEL \
    org.opencontainers.image.title="WakeDock" \
    org.opencontainers.image.description="Docker service wake-up and management system" \
    org.opencontainers.image.vendor="WakeDock" \
    org.opencontainers.image.version="1.0.0" \
    security.non-root="true" \
    security.dockerfile.hardened="true"

# Run the application
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "-m", "wakedock.main"]
