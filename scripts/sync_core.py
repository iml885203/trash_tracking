#!/usr/bin/env python3
"""
Sync core package from packages/core/ to custom_components/trash_tracking/

This script:
1. Copies all files from packages/core/trash_tracking_core/ to custom_components/trash_tracking/trash_tracking_core/
2. Converts absolute imports to relative imports for Home Assistant compatibility
3. Preserves directory structure and maintains code consistency
"""

import re
import shutil
from pathlib import Path


def convert_imports(content: str) -> str:
    """
    Convert absolute imports to relative imports

    Examples:
        from trash_tracking_core.clients import X → from .clients import X
        from trash_tracking_core.models.truck import X → from ..models.truck import X
    """
    # Pattern 1: from trash_tracking_core.xxx import yyy
    # Calculate relative depth based on import path
    def replace_import(match):
        import_path = match.group(1)
        imported_items = match.group(2)

        # Count dots needed (submodule depth)
        parts = import_path.split('.')
        if len(parts) == 1:
            # from trash_tracking_core.clients → from .clients
            return f"from .{parts[0]} import {imported_items}"
        else:
            # from trash_tracking_core.models.truck → from ..models.truck (if called from clients/)
            # This is simplified - assumes one level deep
            relative_path = '.'.join(parts)
            return f"from ..{relative_path} import {imported_items}"

    # Replace imports
    content = re.sub(
        r'from trash_tracking_core\.([a-z_\.]+) import (.+)',
        replace_import,
        content
    )

    return content


def sync_directory(src_dir: Path, dst_dir: Path):
    """Sync source directory to destination with import conversion"""

    print(f"🔄 Syncing {src_dir} → {dst_dir}")

    # Remove destination if exists (clean slate)
    if dst_dir.exists():
        print(f"   Removing existing {dst_dir}")
        shutil.rmtree(dst_dir)

    # Copy entire directory
    shutil.copytree(src_dir, dst_dir, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo'))

    # Convert all Python files
    python_files = list(dst_dir.rglob('*.py'))
    print(f"   Converting {len(python_files)} Python files...")

    for py_file in python_files:
        # Read content
        content = py_file.read_text(encoding='utf-8')

        # Convert imports
        converted_content = convert_imports(content)

        # Write back if changed
        if converted_content != content:
            py_file.write_text(converted_content, encoding='utf-8')
            rel_path = py_file.relative_to(dst_dir)
            print(f"   ✓ Converted imports in {rel_path}")


def main():
    """Main sync process"""
    project_root = Path(__file__).parent.parent

    src = project_root / "packages" / "core" / "trash_tracking_core"
    dst = project_root / "custom_components" / "trash_tracking" / "trash_tracking_core"

    if not src.exists():
        print(f"❌ Source directory not found: {src}")
        return 1

    if not dst.parent.exists():
        print(f"❌ Destination parent directory not found: {dst.parent}")
        return 1

    print("=" * 60)
    print("📦 Trash Tracking Core - Sync Script")
    print("=" * 60)

    try:
        sync_directory(src, dst)
        print("\n✅ Sync completed successfully!")
        print("\nNext steps:")
        print("1. Review the changes: git diff custom_components/trash_tracking/trash_tracking_core/")
        print("2. Test Home Assistant integration")
        print("3. Commit the changes")
        return 0

    except Exception as e:
        print(f"\n❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
