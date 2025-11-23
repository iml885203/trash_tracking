# Home Assistant Add-on Dockerfile
ARG BUILD_FROM
FROM $BUILD_FROM

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install Python and dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    curl \
    && pip3 install --no-cache-dir --upgrade pip

# Set working directory
WORKDIR /app

# Install core package first
COPY packages/core /tmp/core
RUN cd /tmp/core && pip3 install --no-cache-dir .

# Copy addon application files
COPY apps/addon/addon/ /app/addon/
COPY apps/addon/app.py /app/
COPY apps/addon/pyproject.toml /app/

# Install addon package and its dependencies
RUN pip3 install --no-cache-dir .

# Create run script
RUN echo '#!/usr/bin/env bashio' > /app/run && \
    echo 'cd /app' >> /app/run && \
    echo 'python3 app.py' >> /app/run && \
    chmod a+x /app/run

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Taipei

# Default command - use run script for Home Assistant Add-on
CMD ["/app/run"]
