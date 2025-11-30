Feature: User Authentication

  As a user
  I want to register and authenticate securely
  So that I can access my email forwarding account

  Background:
    Given the SMTPy API server is running
    And the database is initialized

  Scenario: User registration with valid credentials
    Given I am not authenticated
    When I submit a registration form with:
      | username | john_doe           |
      | email    | john@example.com   |
      | password | SecurePass123!     |
    Then my account should be created successfully
    And I should receive a verification email
    And I should see a success message

  Scenario: User registration with weak password
    Given I am not authenticated
    When I submit a registration form with a weak password "password123"
    Then registration should fail
    And I should see an error "Password must contain at least one uppercase letter"

  Scenario: User registration with existing username
    Given a user already exists with username "john_doe"
    When I try to register with the same username "john_doe"
    Then registration should fail
    And I should see an error indicating the username is already taken

  Scenario: Successful login with valid credentials
    Given I have a registered account with username "john_doe" and password "SecurePass123!"
    When I submit login credentials:
      | username | john_doe       |
      | password | SecurePass123! |
    Then I should be authenticated successfully
    And a session cookie should be set
    And I should be redirected to the dashboard

  Scenario: Failed login with incorrect password
    Given I have a registered account with username "john_doe"
    When I submit login credentials with an incorrect password
    Then authentication should fail
    And I should see an error "Invalid credentials"
    And no session cookie should be set

  Scenario: Failed login with non-existent user
    Given no user exists with username "nonexistent"
    When I attempt to login as "nonexistent"
    Then authentication should fail
    And I should see an error "Invalid credentials"

  Scenario: User logout
    Given I am logged in as "john_doe"
    When I click the logout button
    Then my session should be terminated
    And the session cookie should be cleared
    And I should be redirected to the login page

  Scenario: Password reset request
    Given I have a registered account with email "john@example.com"
    When I request a password reset for "john@example.com"
    Then I should receive a password reset email
    And the email should contain a secure reset token
    And I should see a confirmation message

  Scenario: Password reset with valid token
    Given I have requested a password reset
    And I have received a valid reset token
    When I submit a new password "NewSecure456!" with the reset token
    Then my password should be updated
    And I should see a success message
    And I should be able to login with the new password

  Scenario: Password reset with expired token
    Given I have an expired password reset token
    When I attempt to reset my password with the expired token
    Then the password reset should fail
    And I should see an error "Reset token has expired"

  Scenario: Email verification
    Given I have registered but not verified my email
    And I have received a verification email
    When I click the verification link
    Then my email should be marked as verified
    And I should see a success message
    And I should be able to access all features

  Scenario: Access protected resource without authentication
    Given I am not authenticated
    When I try to access the dashboard
    Then I should be denied access
    And I should be redirected to the login page

  Scenario: Session expiration
    Given I am logged in with a session
    When my session expires after 7 days
    Then I should be automatically logged out
    And I should need to login again to access protected resources
