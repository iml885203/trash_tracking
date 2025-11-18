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

# Copy application files
COPY src/ /app/src/
COPY app.py /app/
COPY cli.py /app/
COPY requirements.txt /app/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy run script
COPY trash_tracking_addon/run.sh /
RUN chmod a+x /run.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run
CMD [ "/run.sh" ]
