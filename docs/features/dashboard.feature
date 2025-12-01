Feature: Dashboard and Statistics

  As a user
  I want to view comprehensive analytics and metrics
  So that I can monitor my email forwarding activity and performance

  Background:
    Given I am logged in as a user
    And I have active domains and aliases
    And the SMTPy API server is running

  Scenario: View dashboard overview
    Given I am on the dashboard page
    Then I should see key metrics including:
      | metric                  | description                          |
      | Total domains           | Number of configured domains         |
      | Active aliases          | Number of enabled aliases            |
      | Messages today          | Messages received today              |
      | Messages this month     | Messages received this month         |
      | Success rate            | Percentage of successfully delivered |

  Scenario: View 7-day activity chart
    Given I am on the dashboard
    When I view the activity chart
    Then I should see a line chart showing the last 7 days
    And the chart should display:
      | metric           | visualization  |
      | Messages sent    | Line graph     |
      | Daily totals     | Data points    |
      | Success rate     | Trend line     |
    And I should be able to hover over points to see exact values

  Scenario: View monthly statistics
    Given I am on the dashboard
    When I select the monthly view
    Then I should see statistics for the current month
    And I should see:
      | metric                    | example |
      | Total messages            | 1,234   |
      | Successfully delivered    | 1,200   |
      | Failed deliveries         | 34      |
      | Average per day           | 41      |
      | Success rate              | 97.2%   |

  Scenario: View domain breakdown
    Given I have multiple domains with different activity levels
    When I view the domain breakdown section
    Then I should see a list of my domains sorted by activity
    And each domain should show:
      | field              | description                    |
      | Domain name        | example.com                    |
      | Message count      | Number of messages received    |
      | Percentage         | % of total messages            |
      | Active aliases     | Number of aliases              |
    And I should see a visual representation (pie chart or bars)

  Scenario: View top aliases by activity
    Given I have multiple aliases
    When I view the top aliases section
    Then I should see my most active aliases
    And each alias should display:
      | field           | description                  |
      | Alias address   | contact@example.com          |
      | Message count   | Number received              |
      | Last activity   | Timestamp of last message    |
    And the list should be sorted by message count descending

  Scenario: View recent activity feed
    Given I am on the dashboard
    When I view the recent activity section
    Then I should see the latest 10 messages
    And each activity entry should show:
      | field        | description                    |
      | Timestamp    | When the message was received  |
      | Alias        | Receiving alias                |
      | Sender       | Who sent the message           |
      | Status       | Delivery status                |
    And I should be able to click to view full message details

  Scenario: Filter statistics by date range
    Given I am on the dashboard
    When I select a custom date range from "2024-01-01" to "2024-01-31"
    Then all statistics should update to reflect that period
    And the activity chart should show data for that range
    And the domain breakdown should show counts for that period

  Scenario: View quick stats comparison
    Given I am on the dashboard
    When I view the comparison metrics
    Then I should see comparisons like:
      | metric                | current | previous | change  |
      | Messages this week    | 287     | 245      | +17%    |
      | Success rate          | 98.5%   | 97.2%    | +1.3%   |
      | Active aliases        | 45      | 42       | +3      |
    And positive changes should be highlighted in green
    And negative changes should be highlighted in red

  Scenario: View delivery success rate over time
    Given I have historical data
    When I view the success rate chart
    Then I should see a line chart showing success rate percentage
    And the chart should show trends over the selected period
    And I should be able to identify periods with delivery issues

  Scenario: Empty state for new users
    Given I am a new user with no activity
    When I view the dashboard
    Then I should see an empty state message
    And I should see guidance on getting started
    And I should see buttons to:
      | action          | destination                |
      | Add domain      | Domain management page     |
      | Create alias    | Alias creation page        |
      | View docs       | Documentation              |

  Scenario: Real-time updates on dashboard
    Given I am viewing the dashboard
    When a new message is received and forwarded
    Then the message count should update automatically
    And the recent activity feed should show the new message
    And the success rate should recalculate
    And I should see a notification or visual indicator

  Scenario: Export dashboard statistics
    Given I am on the dashboard
    When I click "Export statistics"
    Then I should be able to choose export format (CSV/PDF)
    When I select CSV
    Then I should download a CSV file
    And the file should contain all current statistics

  Scenario: View statistics for specific domain
    Given I have multiple domains
    When I click on a specific domain in the dashboard
    Then I should see filtered statistics for that domain only
    And I should see:
      | metric                     | description                          |
      | Domain-specific messages   | Count for this domain only           |
      | Active aliases on domain   | Aliases using this domain            |
      | Top aliases for domain     | Most active aliases on this domain   |
      | Recent messages            | Latest messages for this domain      |

  Scenario: View system health indicators
    Given I am on the dashboard
    When I view the system health section
    Then I should see indicators for:
      | indicator              | status        |
      | API status             | Healthy       |
      | SMTP server status     | Running       |
      | Database connection    | Connected     |
      | Last sync              | 2 mins ago    |
    And critical issues should be highlighted in red
    And I should see alerts for any problems

  Scenario: Mobile responsive dashboard
    Given I am accessing the dashboard on a mobile device
    Then the dashboard layout should adapt to mobile screen size
    And all charts should be readable on small screens
    And navigation should be touch-friendly
    And key metrics should remain visible
