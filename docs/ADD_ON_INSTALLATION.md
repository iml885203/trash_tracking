# Home Assistant Add-on Installation and Publishing Guide

This guide explains how to install, test, and publish the Trash Tracking Home Assistant Add-on.

## 📋 Table of Contents

- [Local Development Testing](#local-development-testing)
- [Publishing to GitHub](#publishing-to-github)
- [User Installation](#user-installation)
- [Troubleshooting](#troubleshooting)

---

## Local Development Testing

### Method 1: Direct Copy to Home Assistant

If you have Home Assistant OS or Supervised installation:

1. **Copy Add-on folder to `/addons/` directory**

   ```bash
   # On your development machine
   cd /path/to/trash_tracking

   # Copy entire addon folder to HA
   scp -r trash_tracking_addon/ root@homeassistant.local:/addons/trash_tracking
   ```

   Or manually copy the `trash_tracking_addon/` folder using Samba/SFTP.

2. **Reload Add-on Store**

   - Go to Home Assistant UI
   - **Supervisor** → **Add-on Store** → Top right ⋮ → **Reload**

3. **Install Add-on**

   - Find "Garbage Truck Tracking System" in the **Local add-ons** section
   - Click to enter → **Install**

4. **Configure and Start**

   - Go to **Configuration** tab
   - Fill in your configuration (coordinates, collection points, etc.)
   - Click **Save**
   - Go to **Info** tab
   - Click **Start**

5. **Check Logs**

   - Go to **Log** tab
   - Confirm there are no error messages
   - You should see:
     ```
     [INFO] Starting Trash Tracking Add-on...
     [INFO] Starting Flask application...
     * Running on http://0.0.0.0:5000
     ```

### Method 2: Docker Compose Local Testing

Test with Docker Compose before publishing:

1. **Create test environment**

   ```bash
   cd trash_tracking

   # Create test configuration
   cp config.example.yaml config.yaml
   # Edit config.yaml to fill in your settings

   # Start with Docker Compose
   docker-compose up --build
   ```

2. **Test API**

   ```bash
   # Health check
   curl http://localhost:5000/health

   # Status query
   curl http://localhost:5000/api/trash/status
   ```

3. **Stop testing**

   ```bash
   docker-compose down
   ```

---

## Publishing to GitHub

### Step 1: Prepare GitHub Repository

1. **Verify project structure**

   ```
   trash_tracking/
   ├── trash_tracking_addon/
   │   ├── config.yaml
   │   ├── Dockerfile
   │   ├── build.yaml
   │   ├── run.sh
   │   ├── README.md
   │   ├── DOCS.md
   │   ├── CHANGELOG.md
   │   ├── icon.png
   │   ├── logo.png
   │   ├── repository.json
   │   └── translations/
   │       ├── en.yaml
   │       └── zh-Hant.yaml
   ├── src/
   ├── app.py
   ├── cli.py
   ├── requirements.txt
   └── README.md
   ```

2. **Commit to GitHub**

   ```bash
   git add trash_tracking_addon/
   git commit -m "feat: add Home Assistant Add-on package"
   git push origin master
   ```

### Step 2: Create GitHub Release

1. **Create version tag**

   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

2. **Create Release on GitHub**

   - Go to `https://github.com/iml885203/trash_tracking/releases`
   - Click **Create a new release**
   - Select tag `v1.0.0`
   - Title: `v1.0.0 - Initial Release`
   - Description: Copy content from `CHANGELOG.md`
   - Click **Publish release**

### Step 3: Set up GitHub Container Registry (Optional)

To automatically build Docker images:

1. **Create GitHub Actions Workflow**

   Create `.github/workflows/addon-build.yml`:

   ```yaml
   name: Build Add-on

   on:
     push:
       tags:
         - 'v*'
     workflow_dispatch:

   jobs:
     build:
       name: Build add-on
       runs-on: ubuntu-latest
       strategy:
         matrix:
           arch: [aarch64, amd64, armhf, armv7, i386]
       steps:
         - name: Checkout repository
           uses: actions/checkout@v4

         - name: Get version
           id: version
           run: |
             version=$(cat trash_tracking_addon/config.yaml | grep "^version:" | cut -d'"' -f2)
             echo "version=$version" >> $GITHUB_OUTPUT

         - name: Login to GitHub Container Registry
           uses: docker/login-action@v3
           with:
             registry: ghcr.io
             username: ${{ github.repository_owner }}
             password: ${{ secrets.GITHUB_TOKEN }}

         - name: Build and push
           uses: home-assistant/builder@master
           with:
             args: |
               --${{ matrix.arch }} \
               --target trash_tracking_addon \
               --docker-hub ghcr.io/${{ github.repository_owner }}
   ```

2. **Enable GitHub Actions**

   - Commit workflow file
   - Go to **Settings** → **Actions** → **General**
   - Confirm Actions are enabled

---

## User Installation

### Installation Steps

Users can install your add-on through the following steps:

#### 1. Add Repository

1. Go to Home Assistant
2. **Supervisor** → **Add-on Store** → Top right ⋮ → **Repositories**
3. Add:
   ```
   https://github.com/iml885203/trash_tracking
   ```
4. Click **Add**

#### 2. Install Add-on

1. Return to **Add-on Store**
2. Refresh the page
3. Find "Garbage Truck Tracking System"
4. Click to enter → **Install**

#### 3. Configuration

Configure in the **Configuration** tab:

```yaml
location:
  lat: 25.018269
  lng: 121.471703
tracking:
  target_lines: []
  enter_point: "Shuiyuan St Lane 36 Entrance"
  exit_point: "Shuiyuan St No.28"
  trigger_mode: "arriving"
  approaching_threshold: 2
system:
  log_level: "INFO"
```

#### 4. Start

- Go to **Info** tab
- Click **Start**
- Confirm no errors in **Log** tab

#### 5. Home Assistant Integration

Add to `configuration.yaml`:

```yaml
sensor:
  - platform: rest
    name: "Garbage Truck Monitor"
    resource: "http://localhost:5000/api/trash/status"
    scan_interval: 90
    json_attributes:
      - reason
      - truck
      - timestamp
    value_template: "{{ value_json.status }}"

binary_sensor:
  - platform: template
    sensors:
      garbage_truck_nearby:
        friendly_name: "Garbage Truck Nearby"
        value_template: "{{ is_state('sensor.garbage_truck_monitor', 'nearby') }}"
        device_class: presence
```

Reload: **Developer Tools** → **YAML** → **Reload All YAML**

---

## Troubleshooting

### Issue 1: Add-on not showing in Add-on Store

**Solution**:

1. Confirm repository URL is correct
2. Check if `repository.json` is in project root
3. Try manual reload: **Add-on Store** → ⋮ → **Reload**
4. Check Supervisor logs:
   ```bash
   docker logs hassio_supervisor
   ```

### Issue 2: Add-on fails to start

**Checking steps**:

1. **Check Add-on Log**
   - View error messages in **Log** tab

2. **Common errors**:

   ```
   Error: Invalid configuration
   ```
   → Check YAML format in Configuration tab

   ```
   Error: Port 5000 already in use
   ```
   → Stop other services using port 5000

   ```
   ModuleNotFoundError: No module named 'xxx'
   ```
   → Missing dependency in Dockerfile, need to update `requirements.txt`

3. **Manual container testing**

   ```bash
   # SSH into Home Assistant OS
   ssh root@homeassistant.local

   # Check container status
   docker ps -a | grep trash_tracking

   # View container logs
   docker logs addon_trash_tracking

   # Enter container
   docker exec -it addon_trash_tracking /bin/bash

   # Check files
   ls -la /app
   cat /app/config.yaml
   ```

### Issue 3: Configuration file generation error

**Check run.sh**:

```bash
# Enter container
docker exec -it addon_trash_tracking /bin/bash

# Check generated configuration
cat /app/config.yaml

# Manually test bashio
bashio::config 'location.lat'
```

### Issue 4: API connection failure

**Testing steps**:

1. **Confirm Add-on is running**
   ```bash
   docker ps | grep trash_tracking
   ```

2. **Test API connection**
   ```bash
   # In HA OS Terminal or SSH
   curl http://localhost:5000/health
   curl http://localhost:5000/api/trash/status
   ```

3. **Check firewall rules**
   - Ensure port 5000 is not blocked by firewall

### Issue 5: Multi-architecture build failure

**Solution**:

1. **Verify build.yaml is correct**
   ```yaml
   build_from:
     aarch64: "ghcr.io/home-assistant/aarch64-base-python:3.11-alpine3.19"
     # ... other architectures
   ```

2. **Test specific architecture locally**
   ```bash
   docker buildx build \
     --platform linux/amd64 \
     -f trash_tracking_addon/Dockerfile \
     -t trash_tracking:test .
   ```

3. **Check Home Assistant Builder logs**
   ```bash
   docker logs hassio_builder
   ```

---

## Updating Add-on

### Publishing New Version

1. **Update version number**

   Edit `trash_tracking_addon/config.yaml`:
   ```yaml
   version: "1.0.1"
   ```

2. **Update CHANGELOG**

   Add new version description in `trash_tracking_addon/CHANGELOG.md`

3. **Commit and tag**
   ```bash
   git add .
   git commit -m "chore: bump version to 1.0.1"
   git tag -a v1.0.1 -m "Release version 1.0.1"
   git push origin master
   git push origin v1.0.1
   ```

4. **Create GitHub Release**
   - Create new Release on GitHub
   - Select tag `v1.0.1`

5. **User update**
   - Users will see an "Update" button on the add-on page
   - Click to update

---

## Best Practices

### 1. Version Control

- Follow [Semantic Versioning](https://semver.org/)
  - `MAJOR.MINOR.PATCH`
  - MAJOR: Breaking changes
  - MINOR: New features (backward compatible)
  - PATCH: Bug fixes

### 2. Documentation Maintenance

- Update `CHANGELOG.md` before each release
- Keep README up to date
- Provide detailed examples in DOCS

### 3. Testing

- Test all changes locally
- Test on different architectures (if possible)
- Test upgrade paths

### 4. Security

- Regularly update dependencies
- Use `safety` to scan vulnerabilities
- Follow principle of least privilege

### 5. Support

- Monitor GitHub Issues
- Respond to user questions promptly
- Maintain FAQ documentation

---

## Related Resources

- [Home Assistant Add-on Development Documentation](https://developers.home-assistant.io/docs/add-ons)
- [Home Assistant Builder](https://github.com/home-assistant/builder)
- [Bashio Documentation](https://github.com/hassio-addons/bashio)
- [Add-on Examples](https://github.com/home-assistant/addons-example)

---

## Support

If you have questions:
- Check [GitHub Issues](https://github.com/iml885203/trash_tracking/issues)
- Create new Issue to report problems
- Refer to complete documentation: [DOCS.md](../trash_tracking_addon/DOCS.md)
