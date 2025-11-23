"""Step implementations for integration imports testing"""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock

from behave import given, then, when


def mock_homeassistant():
    """Create mock homeassistant modules"""
    sys.modules["homeassistant"] = MagicMock()
    sys.modules["homeassistant.const"] = MagicMock()
    sys.modules["homeassistant.config_entries"] = MagicMock()
    sys.modules["homeassistant.core"] = MagicMock()
    sys.modules["homeassistant.helpers"] = MagicMock()
    sys.modules["homeassistant.helpers.config_validation"] = MagicMock()
    sys.modules["voluptuous"] = MagicMock()

    # Install pytz if not available
    try:
        import pytz  # noqa: F401
    except ImportError:
        sys.modules["pytz"] = MagicMock()


@given("the custom_components directory exists")
def step_custom_components_exists(context):
    """Ensure custom_components is in Python path"""
    # Mock homeassistant modules first
    mock_homeassistant()

    project_root = Path(__file__).parent.parent.parent
    custom_components_parent = project_root

    # Add to sys.path if not already there
    path_str = str(custom_components_parent)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

    # Verify directory exists
    custom_components_dir = custom_components_parent / "custom_components"
    assert custom_components_dir.exists(), f"custom_components directory not found at {custom_components_dir}"

    # Initialize context
    context.import_errors = []


@when('I import "{module_name}"')
def step_import_module(context, module_name):
    """Import a module and track any errors"""
    try:
        # Remove module from cache if it exists to force reimport
        if module_name in sys.modules:
            del sys.modules[module_name]

        # Also remove any submodules
        modules_to_remove = [name for name in sys.modules.keys() if name.startswith(module_name + ".")]
        for mod_name in modules_to_remove:
            del sys.modules[mod_name]

        # Try to import
        importlib.import_module(module_name)
        print(f"✓ Successfully imported {module_name}")

    except Exception as e:
        error_msg = f"Failed to import {module_name}: {type(e).__name__}: {str(e)}"
        print(f"✗ {error_msg}")
        context.import_errors.append(error_msg)


@when("I import the trash_tracking_core package")
def step_import_core_package(context):
    """Import the main trash_tracking_core package"""
    step_import_module(context, "custom_components.trash_tracking.trash_tracking_core")


@then("no import errors should occur")
def step_no_import_errors(context):
    """Verify no import errors occurred"""
    if context.import_errors:
        error_summary = "\n".join(f"  - {err}" for err in context.import_errors)
        raise AssertionError(f"Import errors occurred:\n{error_summary}")
