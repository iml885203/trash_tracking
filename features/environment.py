"""Behave environment configuration"""

import requests


def before_all(context):
    """Setup before all scenarios"""
    context.base_url = "http://localhost:5000"


def before_scenario(context, scenario):
    """Setup before each scenario"""
    # Check if API is needed for this scenario
    if "API" in scenario.feature.name or "設定精靈" in scenario.feature.name:
        try:
            response = requests.get(f"{context.base_url}/health", timeout=5)
            if response.status_code != 200:
                scenario.skip("API server is not running")
        except requests.exceptions.RequestException:
            scenario.skip("API server is not running. Start with: python3 app.py")


def after_scenario(context, scenario):
    """Cleanup after each scenario"""
    pass
