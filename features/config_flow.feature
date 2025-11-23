@real_api
Feature: Integration Config Flow
  As a Home Assistant user
  I want to set up the Trash Tracking integration
  So that I can receive notifications when the garbage truck is nearby

  Background:
    Given the trash_tracking_core modules are available

  Scenario: Successfully configure integration with valid address
    Given I have the address "新北市板橋區民生路二段80號"
    When I geocode the address
    Then the coordinates should be near latitude 25.018 and longitude 121.471
    When I fetch nearby routes for those coordinates
    Then I should get at least 1 route
    When I analyze the routes
    Then I should get route recommendations
    And each recommendation should have a truck
    And each recommendation should have an enter_point
    And each recommendation should have an exit_point
    And each recommendation should have a nearest_point

  Scenario: Geocoding fails with invalid address
    Given I have the address "InvalidAddress123XYZ"
    When I attempt to geocode the address
    Then geocoding should fail with an error

  Scenario: No routes found for remote location
    Given I have coordinates latitude 23.0 and longitude 120.0
    When I fetch nearby routes for those coordinates
    Then I should get 0 routes

  Scenario: Route recommendation includes collection points
    Given I have the address "新北市板橋區文化路一段188號"
    When I complete the full config flow
    Then the selected route should have collection points
    And the enter_point should be in the collection points list
    And the exit_point should be in the collection points list
