"""Setup Wizard Routes"""

import os
from pathlib import Path

import yaml
from flask import Blueprint, Response, jsonify, render_template_string, request

from trash_tracking_core.clients.ntpc_api import NTPCApiClient
from addon.use_cases.auto_suggest_config import AutoSuggestConfigUseCase
from addon.use_cases.exceptions import NoRoutesFoundError, RouteAnalysisError
from trash_tracking_core.utils.geocoding import Geocoder, GeocodingError
from trash_tracking_core.utils.logger import logger

from .template import SETUP_WIZARD_HTML

# Create Blueprint
setup_bp = Blueprint("setup", __name__)


def register_setup_routes(app):
    """Register setup wizard routes to Flask app"""
    app.register_blueprint(setup_bp)


@setup_bp.route("/", methods=["GET"])
@setup_bp.route("/setup", methods=["GET"])
def setup_wizard() -> Response:
    """
    Setup wizard UI (Home Assistant Ingress entry point)

    Returns:
        Response: HTML page
    """
    return render_template_string(SETUP_WIZARD_HTML)  # type: ignore[return-value]


@setup_bp.route("/api/setup/suggest", methods=["POST"])
def api_suggest_config() -> tuple:
    """
    API endpoint: Auto-suggest configuration based on address

    Request body:
        {
            "address": "新北市板橋區中山路一段161號"
        }

    Returns:
        tuple: (JSON response, HTTP status code)
    """
    try:
        data = request.get_json()
        address = data.get("address")

        if not address:
            return jsonify({"error": "Address is required"}), 400

        logger.info(f"Auto-suggest request for address: {address}")

        # Execute Use Case
        use_case = AutoSuggestConfigUseCase(geocoder=Geocoder(), api_client=NTPCApiClient())

        recommendation = use_case.execute(address)

        # Convert to response format
        response_data = {
            "success": True,
            "recommendation": {
                "latitude": recommendation.latitude,
                "longitude": recommendation.longitude,
                "route_selection": {
                    "vehicle_number": recommendation.route_selection.vehicle_number,
                    "route_names": recommendation.route_selection.route_names,
                    "best_route": {
                        "line_name": recommendation.route_selection.best_route.truck.line_name,
                        "car_no": recommendation.route_selection.best_route.truck.car_no,
                        "enter_point": {
                            "point_name": recommendation.route_selection.best_route.enter_point.point_name,
                            "rank": recommendation.route_selection.best_route.enter_point.rank,
                        },
                        "exit_point": {
                            "point_name": recommendation.route_selection.best_route.exit_point.point_name,
                            "rank": recommendation.route_selection.best_route.exit_point.rank,
                        },
                        "nearest_distance_meters": round(
                            recommendation.route_selection.best_route.nearest_point.distance_meters, 2
                        ),
                    },
                },
                "threshold": recommendation.threshold,
                "trigger_mode": recommendation.trigger_mode,
            },
            "config": recommendation.to_dict(),
        }

        logger.info(f"Auto-suggest completed: {recommendation.route_selection.route_names}")
        return jsonify(response_data), 200

    except GeocodingError as e:
        logger.warning(f"Geocoding error: {e}")
        return jsonify({"error": f"地址解析失敗: {str(e)}"}), 400

    except NoRoutesFoundError as e:
        logger.warning(f"No routes found: {e}")
        return jsonify({"error": str(e)}), 404

    except RouteAnalysisError as e:
        logger.error(f"Route analysis error: {e}")
        return jsonify({"error": f"路線分析失敗: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"Auto-suggest failed: {e}", exc_info=True)
        return jsonify({"error": f"系統錯誤: {str(e)}"}), 500


@setup_bp.route("/api/setup/save", methods=["POST"])
def api_save_config() -> tuple:
    """
    API endpoint: Save configuration to config.yaml

    Request body:
        {
            "config": { ... }  # Full configuration object
        }

    Returns:
        tuple: (JSON response, HTTP status code)
    """
    try:
        data = request.get_json()
        new_config = data.get("config")

        if not new_config:
            return jsonify({"error": "Configuration is required"}), 400

        # Determine config file path (Home Assistant Add-on uses /config/config.yaml)
        config_path: str = os.getenv("CONFIG_PATH", "config.yaml")
        if os.path.exists("/config"):
            # Running in Home Assistant Add-on
            config_path = "/config/trash_tracking_config.yaml"
        else:
            # Running standalone
            config_path = str(Path("config.yaml"))

        logger.info(f"Saving configuration to: {config_path}")

        # Save configuration
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(new_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        logger.info("Configuration saved successfully")

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Configuration saved successfully",
                    "config_path": str(config_path),
                    "note": "Please restart the add-on to apply changes",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to save configuration: {e}", exc_info=True)
        return jsonify({"error": f"儲存設定失敗: {str(e)}"}), 500
