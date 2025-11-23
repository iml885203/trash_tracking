@requires_homeassistant
Feature: Home Assistant Integration Imports
  As a developer
  I want to ensure all imports in the integration are correct
  So that the integration can load successfully in Home Assistant

  Scenario: Import trash_tracking_core package
    Given the custom_components directory exists
    When I import the trash_tracking_core package
    Then no import errors should occur

  Scenario: Import all client modules
    Given the custom_components directory exists
    When I import "custom_components.trash_tracking.trash_tracking_core.clients.ntpc_api"
    Then no import errors should occur

  Scenario: Import all model modules
    Given the custom_components directory exists
    When I import "custom_components.trash_tracking.trash_tracking_core.models.point"
    And I import "custom_components.trash_tracking.trash_tracking_core.models.truck"
    Then no import errors should occur

  Scenario: Import all core modules
    Given the custom_components directory exists
    When I import "custom_components.trash_tracking.trash_tracking_core.core.point_matcher"
    And I import "custom_components.trash_tracking.trash_tracking_core.core.state_manager"
    And I import "custom_components.trash_tracking.trash_tracking_core.core.tracker"
    Then no import errors should occur

  Scenario: Import all utility modules
    Given the custom_components directory exists
    When I import "custom_components.trash_tracking.trash_tracking_core.utils.config"
    And I import "custom_components.trash_tracking.trash_tracking_core.utils.geocoding"
    And I import "custom_components.trash_tracking.trash_tracking_core.utils.logger"
    And I import "custom_components.trash_tracking.trash_tracking_core.utils.route_analyzer"
    Then no import errors should occur

  Scenario: Import integration config_flow
    Given the custom_components directory exists
    When I import "custom_components.trash_tracking.config_flow"
    Then no import errors should occur
