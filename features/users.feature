xFeature: Users basic interactions with SMTPy
  As a user of SMTPy
  I want to access the service and see it is healthy
  So that I can trust the platform is running

  Background:
    Given the SMTPy API server is running

  Scenario: Landing page (API docs) is available
    When I visit the root URL
    Then I receive a successful response
    And I can see the API documentation

  Scenario: Health check endpoint reports healthy
    When I request the health endpoint
    Then I receive a successful response
    And the health payload indicates the service is healthy

  Scenario: Unknown route returns not found
    When I visit an unknown URL
    Then I receive a not found response