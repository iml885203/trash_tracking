#!/usr/bin/with-contenv bashio
# ==============================================================================
# Home Assistant Add-on: Trash Tracking
# Runs the Trash Tracking service
# ==============================================================================

# shellcheck disable=SC1091

bashio::log.info "Starting Trash Tracking Add-on..."

# Create config directory if it doesn't exist
CONFIG_DIR="/config/trash_tracking"
mkdir -p "${CONFIG_DIR}"

# Generate config.yaml from add-on options
bashio::log.info "Generating configuration..."

cat > /app/config.yaml <<EOF
# Auto-generated configuration from Home Assistant Add-on options
system:
  log_level: $(bashio::config 'system.log_level')
  cache_enabled: false
  cache_ttl: 60

location:
  lat: $(bashio::config 'location.lat')
  lng: $(bashio::config 'location.lng')

tracking:
  target_lines:
$(bashio::config 'tracking.target_lines' | jq -r '.[] | "    - \"" + . + "\""')
  enter_point: "$(bashio::config 'tracking.enter_point')"
  exit_point: "$(bashio::config 'tracking.exit_point')"
  trigger_mode: "$(bashio::config 'tracking.trigger_mode')"
  approaching_threshold: $(bashio::config 'tracking.approaching_threshold')

api:
  ntpc:
    base_url: "https://crd-rubbish.epd.ntpc.gov.tw/WebAPI"
    timeout: $(bashio::config 'api.ntpc.timeout')
    retry_count: $(bashio::config 'api.ntpc.retry_count')
    retry_delay: $(bashio::config 'api.ntpc.retry_delay')

  server:
    host: "0.0.0.0"
    port: 5000
    debug: false

home_assistant:
  scan_interval: 90
  light_entity_id: "light.notification_bulb"
EOF

# Show configuration (for debugging)
if bashio::config.true 'system.log_level' 'DEBUG'; then
    bashio::log.debug "Configuration:"
    cat /app/config.yaml
fi

# Create logs directory
mkdir -p /app/logs

# Set timezone
export TZ=Asia/Taipei

# Start the Flask application
bashio::log.info "Starting Flask application..."
cd /app || exit 1

exec python3 app.py
