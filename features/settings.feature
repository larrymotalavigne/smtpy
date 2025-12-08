Feature: User Settings and Preferences

  As a user
  I want to configure my preferences and settings
  So that I can customize my SMTPy experience

  Background:
    Given I am logged in as a user
    And the SMTPy API server is running

  Scenario: View settings page
    Given I am on the settings page
    Then I should see settings categories:
      | category              | description                        |
      | Notifications         | Email and notification preferences |
      | Privacy               | Privacy and data settings          |
      | Security              | Security preferences               |
      | Email forwarding      | Default forwarding settings        |
      | API & Integrations    | API keys and webhooks              |

  Scenario: Configure email notification preferences
    Given I am on the settings page
    When I navigate to "Notifications"
    Then I should see notification options:
      | option                          | default |
      | New message received            | enabled |
      | Domain verification status      | enabled |
      | Failed message delivery         | enabled |
      | Weekly activity summary         | enabled |
      | Billing and subscription alerts | enabled |
      | Security alerts                 | enabled |

  Scenario: Disable specific notifications
    Given I am on the notifications settings
    When I disable "Weekly activity summary"
    And I click "Save preferences"
    Then the setting should be saved
    And I should no longer receive weekly summaries
    And I should see a success message

  Scenario: Enable all notifications
    Given some notifications are disabled
    When I click "Enable all notifications"
    And I save the settings
    Then all notification types should be enabled
    And I should receive all notification emails

  Scenario: Configure notification delivery method
    Given I am on the notifications settings
    When I select notification delivery preferences:
      | notification type        | email | in-app | push |
      | New message received     | yes   | yes    | no   |
      | Failed delivery          | yes   | yes    | yes  |
      | Weekly summary           | yes   | no     | no   |
    And I save the settings
    Then notifications should be delivered via selected methods

  Scenario: Set quiet hours for notifications
    Given I am on the notifications settings
    When I enable "Quiet hours"
    And I set quiet hours from "22:00" to "08:00"
    And I select timezone "America/New_York"
    And I save the settings
    Then I should not receive notifications during those hours
    And urgent alerts should still be delivered

  Scenario: Configure default alias settings
    Given I am on the settings page
    When I navigate to "Email forwarding"
    Then I should see default settings for new aliases:
      | setting                    | default    |
      | Auto-enable new aliases    | enabled    |
      | Spam filtering             | enabled    |
      | Attachment handling        | forward    |
      | Max attachment size        | 25 MB      |

  Scenario: Update default forwarding behavior
    Given I am on email forwarding settings
    When I change "Spam filtering" to "disabled"
    And I change "Max attachment size" to "50 MB"
    And I save the settings
    Then new aliases should use these defaults
    And existing aliases should remain unchanged
    And I should see a success message

  Scenario: Configure privacy settings
    Given I am on the privacy settings
    Then I should see privacy options:
      | option                          | default    |
      | Include original sender info    | enabled    |
      | Log message content             | disabled   |
      | Share usage analytics           | enabled    |
      | Message retention period        | 90 days    |

  Scenario: Update privacy preferences
    Given I am on the privacy settings
    When I change "Message retention period" to "30 days"
    And I disable "Share usage analytics"
    And I save the settings
    Then messages older than 30 days should be auto-deleted
    And my usage data should not be shared
    And I should see a confirmation

  Scenario: Enable GDPR data minimization
    Given I am on the privacy settings
    When I enable "Data minimization mode"
    Then I should see a warning about reduced functionality
    When I confirm the change
    Then only essential data should be stored
    And message content logging should be disabled
    And retention should be minimized

  Scenario: Configure security preferences
    Given I am on the security settings
    Then I should see security options:
      | option                       | current   |
      | Two-factor authentication    | disabled  |
      | Login notifications          | enabled   |
      | Session timeout              | 7 days    |
      | IP address whitelist         | disabled  |

  Scenario: Enable IP whitelisting
    Given I am on the security settings
    When I enable "IP address whitelist"
    And I add my IP addresses:
      | IP address      | description    |
      | 192.168.1.100   | Home           |
      | 10.0.0.50       | Office         |
    And I save the settings
    Then only whitelisted IPs should be able to login
    And I should see a warning about lockout risk

  Scenario: Configure session timeout
    Given I am on the security settings
    When I change "Session timeout" to "24 hours"
    And I save the settings
    Then new sessions should expire after 24 hours
    And I should be logged out after inactivity
    And I should see a success message

  Scenario: View API configuration
    Given I am on the API & Integrations settings
    Then I should see API endpoint information
    And I should see my API keys
    And I should see API usage statistics

  Scenario: Configure webhook endpoints
    Given I am on the API & Integrations settings
    When I click "Add webhook"
    And I enter:
      | field        | value                              |
      | Name         | Production webhook                 |
      | URL          | https://myapp.com/smtpy-webhook   |
      | Events       | message.received, message.failed   |
    And I save the webhook
    Then the webhook should be created
    And events should be sent to that URL
    And I should see the webhook in my list

  Scenario: Test webhook endpoint
    Given I have configured a webhook
    When I click "Test webhook"
    Then a test payload should be sent
    And I should see the response status
    And I should see the response body

  Scenario: Disable webhook
    Given I have an active webhook
    When I disable the webhook
    Then events should no longer be sent
    And the webhook should show as inactive

  Scenario: Delete webhook
    Given I have a configured webhook
    When I click "Delete" on the webhook
    Then I should see a confirmation dialog
    When I confirm deletion
    Then the webhook should be removed
    And I should see a success message

  Scenario: Configure language preference
    Given I am on the settings page
    When I change language to "Français"
    And I save the settings
    Then the interface should switch to French
    And I should see "Paramètres" instead of "Settings"

  Scenario: Configure date and time format
    Given I am on the settings page
    When I set preferences:
      | setting        | value          |
      | Date format    | DD/MM/YYYY     |
      | Time format    | 24-hour        |
      | Timezone       | Europe/Paris   |
    And I save the settings
    Then dates should display as "15/01/2024"
    And times should display as "14:30"
    And timestamps should use Paris timezone

  Scenario: Reset settings to defaults
    Given I have customized many settings
    When I click "Reset to defaults"
    Then I should see a confirmation warning
    When I confirm the reset
    Then all settings should revert to defaults
    And I should see a success message

  Scenario: Export settings configuration
    Given I have configured my preferences
    When I click "Export settings"
    Then I should download a JSON file
    And the file should contain all my settings

  Scenario: Import settings configuration
    Given I have an exported settings file
    When I click "Import settings"
    And I select my settings file
    Then I should see a preview of changes
    When I confirm the import
    Then my settings should be updated
    And I should see a success message
