Feature: User Profile Management

  As a user
  I want to manage my profile and account settings
  So that I can keep my information up-to-date and secure

  Background:
    Given I am logged in as a user
    And the SMTPy API server is running

  Scenario: View my profile
    Given I am on the profile page
    Then I should see my account information:
      | field          | description                |
      | Username       | My username                |
      | Email          | My email address           |
      | Account created| Registration date          |
      | Last login     | Last login timestamp       |
      | Role           | User role (admin/user)     |
      | Organization   | Organization name          |

  Scenario: Update profile information
    Given I am on the profile page
    When I update my profile with:
      | field     | value              |
      | Full name | John Doe           |
      | Phone     | +1234567890        |
    And I click "Save changes"
    Then my profile should be updated
    And I should see a success message
    And the new information should be displayed

  Scenario: Change password successfully
    Given I am on the profile page
    When I navigate to the "Change Password" section
    And I enter:
      | field              | value           |
      | Current password   | OldPass123!     |
      | New password       | NewSecure456!   |
      | Confirm password   | NewSecure456!   |
    And I click "Change password"
    Then my password should be updated
    And I should see a success message
    And I should be able to login with the new password

  Scenario: Change password with incorrect current password
    Given I am on the profile page
    When I try to change my password
    And I enter an incorrect current password
    Then the password change should fail
    And I should see an error "Current password is incorrect"
    And my password should remain unchanged

  Scenario: Change password with weak new password
    Given I am on the profile page
    When I try to change my password to "weak"
    Then the password change should fail
    And I should see validation errors about password strength
    And my password should remain unchanged

  Scenario: Change password with mismatched confirmation
    Given I am on the profile page
    When I enter a new password "NewSecure456!"
    But I enter a different password in the confirmation field
    Then the password change should fail
    And I should see an error "Passwords do not match"

  Scenario: Update email address
    Given I am on the profile page
    When I change my email to "newemail@example.com"
    And I click "Save changes"
    Then a verification email should be sent to "newemail@example.com"
    And my email should be marked as "pending verification"
    And I should see a message to check my email

  Scenario: Verify new email address
    Given I have requested an email change to "newemail@example.com"
    And I have received a verification email
    When I click the verification link in the email
    Then my email should be updated to "newemail@example.com"
    And the email should be marked as verified
    And I should see a success message

  Scenario: View API keys
    Given I am on the profile page
    When I navigate to the "API Keys" section
    Then I should see my existing API keys
    And each key should show:
      | field        | description                    |
      | Key name     | Friendly name                  |
      | Created      | Creation date                  |
      | Last used    | Last usage timestamp           |
      | Status       | Active/Inactive                |

  Scenario: Generate new API key
    Given I am on the API keys section
    When I click "Generate new API key"
    And I enter a name "Production API"
    Then a new API key should be created
    And I should see the full key value once
    And I should see a warning to save the key
    And the key should be added to my keys list

  Scenario: Revoke API key
    Given I have an active API key
    When I click "Revoke" on the API key
    Then I should see a confirmation dialog
    When I confirm the revocation
    Then the API key should be deactivated
    And it should no longer work for API requests
    And I should see a success message

  Scenario: View account statistics
    Given I am on the profile page
    When I view the account statistics section
    Then I should see:
      | metric                | description                    |
      | Total domains         | Number of domains              |
      | Total aliases         | Number of aliases              |
      | Messages received     | Total message count            |
      | Account age           | Days since registration        |
      | Storage used          | Data storage usage             |

  Scenario: Enable two-factor authentication
    Given I am on the profile page
    And two-factor authentication is disabled
    When I click "Enable 2FA"
    Then I should see a QR code
    And I should scan the QR code with an authenticator app
    When I enter the verification code
    Then 2FA should be enabled
    And I should see backup codes
    And I should see a success message

  Scenario: Disable two-factor authentication
    Given I have 2FA enabled
    When I click "Disable 2FA"
    Then I should be prompted for my password
    And I should be prompted for a 2FA code
    When I provide correct credentials
    Then 2FA should be disabled
    And I should see a warning about reduced security

  Scenario: Download account data
    Given I am on the profile page
    When I click "Download my data"
    Then I should see a confirmation dialog
    When I confirm the request
    Then my data export should be queued
    And I should receive an email when it's ready
    And the email should contain a download link

  Scenario: Delete account request
    Given I am on the profile page
    When I click "Delete account"
    Then I should see a serious warning about data loss
    And I should be asked to type my username to confirm
    When I type my username correctly
    And I click "Permanently delete"
    Then my account deletion should be scheduled
    And I should receive a confirmation email
    And I should have 30 days to cancel the deletion

  Scenario: Cancel account deletion
    Given I have requested account deletion
    And the deletion is scheduled for 30 days from now
    When I login and view my profile
    Then I should see a warning banner about pending deletion
    When I click "Cancel deletion"
    Then the deletion should be cancelled
    And my account should be restored to normal status
    And I should see a confirmation message

  Scenario: View login history
    Given I am on the profile page
    When I navigate to "Security & Login History"
    Then I should see my recent logins:
      | field          | description                    |
      | Date/Time      | Login timestamp                |
      | IP Address     | Source IP                      |
      | Location       | Approximate location           |
      | Device         | Browser/device info            |
      | Status         | Success/Failed                 |

  Scenario: View active sessions
    Given I am logged in on multiple devices
    When I view the active sessions section
    Then I should see all current sessions
    And I should be able to revoke sessions
    When I click "Revoke" on a session
    Then that session should be terminated
    And the device should be logged out
