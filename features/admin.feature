Feature: Admin Operations

  As an administrator
  I want to manage users and system settings
  So that I can maintain the platform and support users

  Background:
    Given I am logged in as an admin user
    And the SMTPy API server is running

  Scenario: View all users
    Given there are multiple users in the system
    When I navigate to the admin users page
    Then I should see a list of all users
    And each user entry should display:
      | field          | description                    |
      | Username       | User's username                |
      | Email          | User's email address           |
      | Role           | admin/user                     |
      | Status         | active/disabled/pending        |
      | Created        | Registration date              |
      | Last login     | Last login timestamp           |

  Scenario: Search users
    Given there are many users in the system
    When I search for "john"
    Then I should see only users matching "john"
    And the results should include matches in username and email

  Scenario: Filter users by role
    Given there are users with different roles
    When I filter by role "admin"
    Then I should see only admin users
    And regular users should not be shown

  Scenario: Filter users by status
    Given there are users with different statuses
    When I filter by status "active"
    Then I should see only active users
    And disabled or pending users should be hidden

  Scenario: View user details
    Given I am on the admin users page
    When I click on a specific user
    Then I should see detailed user information including:
      | field                  | description                        |
      | Account info           | Username, email, role, status      |
      | Statistics             | Domains, aliases, messages         |
      | Subscription           | Plan and billing status            |
      | Activity               | Recent actions and logins          |
      | Domains                | List of user's domains             |
      | Aliases                | List of user's aliases             |

  Scenario: Create user invitation
    Given I am on the admin users page
    When I click "Invite user"
    And I enter email "newuser@example.com"
    And I select role "user"
    Then an invitation email should be sent
    And the invitation should appear in pending invitations
    And I should see a success message

  Scenario: Disable user account
    Given there is an active user "john_doe"
    When I click "Disable" on the user
    Then I should see a confirmation dialog
    When I confirm the action
    Then the user account should be disabled
    And the user should be logged out
    And the user should not be able to login
    And I should see a success message

  Scenario: Enable disabled user account
    Given there is a disabled user "john_doe"
    When I click "Enable" on the user
    Then the user account should be activated
    And the user should be able to login again
    And I should see a success message

  Scenario: Promote user to admin
    Given there is a regular user "john_doe"
    When I click "Change role"
    And I select "admin"
    Then I should see a confirmation dialog
    When I confirm the promotion
    Then the user's role should change to admin
    And the user should have admin permissions
    And I should see a success message

  Scenario: Demote admin to regular user
    Given there is an admin user "john_admin"
    When I change their role to "user"
    Then I should see a confirmation warning
    When I confirm the demotion
    Then the user's role should change to user
    And they should lose admin permissions

  Scenario: Delete user account
    Given there is a user "john_doe"
    When I click "Delete" on the user
    Then I should see a serious warning about data deletion
    And I should see the impact:
      | resource | count |
      | Domains  | 3     |
      | Aliases  | 15    |
      | Messages | 450   |
    When I confirm the deletion
    Then the user account should be deleted
    And all user data should be removed
    And I should see a success message

  Scenario: Reset user password
    Given there is a user who forgot their password
    When I click "Reset password" on the user
    Then a password reset email should be sent to the user
    And I should see a confirmation message
    And the user should receive reset instructions

  Scenario: View system statistics
    Given I am on the admin dashboard
    Then I should see system-wide statistics:
      | metric                  | description                    |
      | Total users             | Number of registered users     |
      | Active users            | Users active in last 30 days   |
      | Total domains           | All domains in system          |
      | Total aliases           | All aliases in system          |
      | Messages today          | Messages processed today       |
      | Messages this month     | Messages this month            |
      | Storage used            | Total data storage             |
      | System uptime           | Server uptime                  |

  Scenario: View domain statistics by user
    Given I am on the admin dashboard
    When I view the domain distribution
    Then I should see:
      | metric                        | value |
      | Users with no domains         | 45    |
      | Users with 1-5 domains        | 150   |
      | Users with 6-10 domains       | 30    |
      | Users with 10+ domains        | 5     |

  Scenario: View user activity logs
    Given I am viewing a specific user
    When I navigate to their activity log
    Then I should see a chronological list of actions:
      | timestamp           | action               | details           |
      | 2024-01-15 10:30   | Login                | IP: 192.168.1.1   |
      | 2024-01-15 10:32   | Created domain       | example.com       |
      | 2024-01-15 10:35   | Created alias        | test@example.com  |

  Scenario: View failed login attempts
    Given I am on the admin security page
    When I view failed login attempts
    Then I should see recent failed logins:
      | timestamp           | username  | IP address    | reason              |
      | 2024-01-15 09:30   | john_doe  | 192.168.1.1  | Wrong password      |
      | 2024-01-15 09:31   | john_doe  | 192.168.1.1  | Wrong password      |
    And I should be able to block suspicious IPs

  Scenario: Configure system settings
    Given I am on the admin settings page
    When I update system settings:
      | setting                    | value    |
      | Max domains per user       | 10       |
      | Max aliases per user       | 100      |
      | Message retention days     | 90       |
      | Allow user registration    | true     |
    And I click "Save settings"
    Then the settings should be updated
    And I should see a success message
    And new limits should apply to all users

  Scenario: View system health
    Given I am on the admin dashboard
    When I view the system health panel
    Then I should see service statuses:
      | service         | status    | details              |
      | API             | Healthy   | 2ms avg response     |
      | SMTP Server     | Running   | 25 connections       |
      | Database        | Healthy   | 50% connections used |
      | Redis           | Running   | 10MB used            |
    And any issues should be highlighted in red

  Scenario: View and manage subscriptions
    Given I am on the admin subscriptions page
    Then I should see all user subscriptions
    And I should see subscription statistics:
      | plan       | count | revenue/month |
      | Free       | 850   | $0            |
      | Pro        | 120   | $1,200        |
      | Business   | 30    | $1,500        |

  Scenario: Grant temporary admin access
    Given there is a user who needs temporary admin access
    When I promote them to admin
    And I set an expiration date "2024-02-01"
    Then they should have admin access until that date
    And on "2024-02-01" they should automatically be demoted
    And they should receive a notification

  Scenario: Export user data for support
    Given a user has requested their data
    When I click "Export user data" on their profile
    Then I should download a JSON file
    And the file should contain all user data
    And the action should be logged for compliance

  Scenario: Impersonate user for support
    Given a user is experiencing issues
    When I click "Login as user" on their profile
    Then I should be logged in as that user
    And I should see their dashboard
    And I should see a banner indicating I'm impersonating
    When I click "Exit impersonation"
    Then I should return to my admin account
