#!/bin/bash
# Version bumping script for CalVer (YYYY.MM.PATCH)

set -e

CURRENT_VERSION=$(cat VERSION)
YEAR=$(date +%Y)
MONTH=$(date +%m | sed 's/^0*//')  # Remove leading zero

# Parse current version
IFS='.' read -r CURR_YEAR CURR_MONTH CURR_PATCH <<< "$CURRENT_VERSION"

# Determine new version
if [[ "$CURR_YEAR" == "$YEAR" ]] && [[ "$CURR_MONTH" == "$MONTH" ]]; then
    # Same year and month, increment patch
    NEW_PATCH=$((CURR_PATCH + 1))
    NEW_VERSION="${YEAR}.${MONTH}.${NEW_PATCH}"
else
    # New year or month, reset patch to 1
    NEW_VERSION="${YEAR}.${MONTH}.1"
fi

echo "Current version: $CURRENT_VERSION"
echo "New version: $NEW_VERSION"

# Update VERSION file
echo "$NEW_VERSION" > VERSION

# Update manifest.json
MANIFEST="custom_components/trash_tracking/manifest.json"
if [[ -f "$MANIFEST" ]]; then
    sed -i.bak "s/\"version\": \"[^\"]*\"/\"version\": \"$NEW_VERSION\"/" "$MANIFEST"
    rm -f "$MANIFEST.bak"
    echo "Updated manifest.json to version $NEW_VERSION"
fi

echo ""
echo "✅ Version bumped to $NEW_VERSION"
echo ""
echo "Next steps:"
echo "1. Review changes:"
echo "   git diff VERSION custom_components/trash_tracking/manifest.json"
echo ""
echo "2. Commit changes:"
echo "   git add VERSION custom_components/trash_tracking/manifest.json"
echo "   git commit -m \"chore: bump version to $NEW_VERSION\""
echo ""
echo "3. Create and push tag:"
echo "   git tag -a v$NEW_VERSION -m \"Release version $NEW_VERSION\""
echo "   git push origin master"
echo "   git push origin v$NEW_VERSION"
echo ""
echo "4. GitHub Actions will automatically run tests and create release"
