# Version Management

This project uses **Calendar Versioning (CalVer)** with the format: `YYYY.MM.PATCH`

## Version Format

- **YYYY**: 4-digit year (e.g., 2025)
- **MM**: Month without leading zero (e.g., 1-12)
- **PATCH**: Incremental patch number within the same year-month

### Examples

- `2025.11.1` - First release in November 2025
- `2025.11.2` - Second release in November 2025
- `2025.12.1` - First release in December 2025
- `2026.1.1` - First release in January 2026

## How to Release a New Version

### Method 1: Automatic Version Bump (Recommended)

Use the provided script to automatically bump the version:

```bash
./scripts/bump-version.sh
```

This script will:
- Automatically determine the next version number
- Update the `VERSION` file
- Update the addon `config.yaml` (if homeassistant-addons repo is in parent directory)
- Show you the next steps to commit and tag

Then follow the instructions shown by the script.

### Method 2: Manual Version Bump

1. **Update VERSION file**
   ```bash
   echo "2025.11.1" > VERSION
   ```

2. **Commit the change**
   ```bash
   git add VERSION
   git commit -m "chore: bump version to 2025.11.1"
   ```

3. **Create and push a tag**
   ```bash
   git tag -a v2025.11.1 -m "Release version 2025.11.1"
   git push origin master
   git push origin v2025.11.1
   ```

4. **GitHub Actions will automatically**:
   - Run tests and security scans
   - Build Docker images for all architectures
   - Tag images with the version number (e.g., `2025.11.1`) and `latest`
   - Update the addon config.yaml in homeassistant-addons repository
   - Push images to GitHub Container Registry

## Version Sources

The CI/CD pipeline determines the version in the following priority:

1. **Git tag** (highest priority): If you push a tag like `v2025.11.1`, it uses `2025.11.1`
2. **VERSION file**: If no tag, reads from the `VERSION` file
3. **Auto-generated** (fallback): Creates a dev version like `dev-2025.11.18`

## Docker Image Tags

When you release version `2025.11.1`, the following images are created:

```
ghcr.io/iml885203/amd64-trash-tracking:2025.11.1
ghcr.io/iml885203/amd64-trash-tracking:latest

ghcr.io/iml885203/aarch64-trash-tracking:2025.11.1
ghcr.io/iml885203/aarch64-trash-tracking:latest

... (and for armv7, armhf, i386)
```

## Home Assistant Add-on Version

The version in `homeassistant-addons/trash-tracking/config.yaml` is automatically updated by GitHub Actions when you push to master or create a tag.

Users will see this version in the Home Assistant Add-on Store.

## Best Practices

1. **Bump version before making releases**: Update VERSION file before you're ready to release
2. **Use semantic commits**: Follow conventional commit format
   - `feat:` - New features (bump patch)
   - `fix:` - Bug fixes (bump patch)
   - `chore:` - Maintenance tasks
3. **Tag releases**: Always tag your releases with `v` prefix
4. **Keep CHANGELOG.md updated**: Document changes in each version

## Changelog

Update `CHANGELOG.md` when releasing:

```markdown
## [2025.11.1] - 2025-11-18

### Added
- New feature description

### Fixed
- Bug fix description

### Changed
- Changes description
```
