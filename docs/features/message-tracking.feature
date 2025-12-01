Feature: Message Tracking and Management

  As a user
  I want to track and manage forwarded emails
  So that I can monitor email delivery and troubleshoot issues

  Background:
    Given I am logged in as a user
    And I have verified domains and active aliases
    And the SMTPy API server is running

  Scenario: View message list
    Given I have received and forwarded several emails
    When I navigate to the messages page
    Then I should see a list of all messages
    And each message should display:
      | field          | example                    |
      | sender         | sender@external.com        |
      | recipient      | myalias@example.com        |
      | subject        | Email subject              |
      | status         | delivered/failed/pending   |
      | timestamp      | 2024-01-15 10:30 AM       |

  Scenario: View message details
    Given I have a message in my inbox
    When I click on the message
    Then I should see the full message details including:
      | field              | description                    |
      | From               | Original sender address        |
      | To                 | Alias address                  |
      | Forwarded to       | Destination address            |
      | Subject            | Email subject                  |
      | Received at        | Timestamp                      |
      | Forwarded at       | Timestamp                      |
      | Status             | Delivery status                |
      | Size               | Message size                   |
      | Attachments        | List of attachments            |

  Scenario: Filter messages by status - Delivered
    Given I have messages with different statuses
    When I filter by status "delivered"
    Then I should see only successfully delivered messages
    And failed or pending messages should not be shown

  Scenario: Filter messages by status - Failed
    Given I have messages with different statuses
    When I filter by status "failed"
    Then I should see only failed messages
    And each failed message should show the error reason

  Scenario: Filter messages by date range
    Given I have messages from the past 30 days
    When I filter messages from "2024-01-01" to "2024-01-15"
    Then I should see only messages within that date range
    And messages outside the range should be hidden

  Scenario: Filter messages by sender email
    Given I have messages from multiple senders
    When I filter by sender "newsletter@company.com"
    Then I should see only messages from that sender
    And messages from other senders should be filtered out

  Scenario: Filter messages by recipient alias
    Given I have multiple aliases receiving emails
    When I filter by recipient "contact@example.com"
    Then I should see only messages sent to that alias
    And messages to other aliases should not be shown

  Scenario: Filter messages with attachments
    Given I have messages with and without attachments
    When I filter to show only messages with attachments
    Then I should see only messages that have attachments
    And messages without attachments should be hidden

  Scenario: Search messages by subject
    Given I have multiple messages
    When I search for "Invoice" in the subject
    Then I should see only messages with "Invoice" in the subject line
    And other messages should be filtered out

  Scenario: Pagination of message list
    Given I have 100 messages
    When I view the messages page with page size 25
    Then I should see 25 messages on the first page
    And I should see pagination controls
    When I navigate to page 2
    Then I should see the next 25 messages

  Scenario: Sort messages by date - newest first
    Given I have messages from different dates
    When I sort by date descending
    Then the newest messages should appear first
    And the oldest messages should appear last

  Scenario: Sort messages by date - oldest first
    Given I have messages from different dates
    When I sort by date ascending
    Then the oldest messages should appear first
    And the newest messages should appear last

  Scenario: Retry failed message delivery
    Given I have a message with status "failed"
    And the failure was due to a temporary error
    When I click "Retry" on the failed message
    Then the system should attempt to forward the message again
    And the status should update to "pending"
    And upon successful delivery, the status should change to "delivered"

  Scenario: View failure reason for failed messages
    Given I have a message with status "failed"
    When I view the message details
    Then I should see the failure reason
    And I should see the error code
    And I should see suggestions for resolution

  Scenario: Delete a message
    Given I have a message in my list
    When I select the message and click delete
    Then I should see a confirmation dialog
    When I confirm the deletion
    Then the message should be removed from the list
    And I should see a success message

  Scenario: Bulk delete messages
    Given I have multiple messages
    When I select 5 messages
    And I click "Delete selected"
    Then I should see a confirmation dialog
    When I confirm the bulk deletion
    Then all selected messages should be removed
    And I should see a success message

  Scenario: View message statistics
    Given I am on the messages page
    When I view the statistics panel
    Then I should see:
      | metric                | example |
      | Total messages        | 150     |
      | Delivered             | 145     |
      | Failed                | 5       |
      | Success rate          | 96.7%   |

  Scenario: Export messages to CSV
    Given I have messages in my list
    When I click "Export to CSV"
    Then I should download a CSV file
    And the file should contain all message data with headers

  Scenario: Real-time message updates
    Given I am viewing the messages page
    When a new email is received and forwarded
    Then the new message should appear in my list automatically
    And I should see a notification of the new message

  Scenario: View message headers
    Given I have a message
    When I view the message details
    And I click "View headers"
    Then I should see the complete email headers
    And I should see DKIM and SPF verification results

  Scenario: Filter messages by multiple criteria
    Given I have many messages
    When I apply filters:
      | filter           | value                  |
      | status           | delivered              |
      | sender           | newsletter@company.com |
      | date_from        | 2024-01-01            |
      | has_attachments  | true                   |
    Then I should see only messages matching all criteria
