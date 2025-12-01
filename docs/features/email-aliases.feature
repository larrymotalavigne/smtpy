Feature: Email Alias Management

  As a user
  I want to create and manage email aliases
  So that I can control email forwarding and protect my privacy

  Background:
    Given I am logged in as a user
    And I have a verified domain "example.com"
    And the SMTPy API server is running

  Scenario: Create a new email alias
    Given I am on the aliases page
    When I create an alias with:
      | alias_address    | contact@example.com     |
      | forward_to       | myreal@email.com        |
      | description      | Contact form emails     |
    Then the alias should be created successfully
    And I should see it in my aliases list
    And the alias should be enabled by default

  Scenario: Create alias with custom name
    Given I want to create an alias for a specific service
    When I create an alias "netflix@example.com" forwarding to "myreal@email.com"
    Then the alias should be created
    And emails to "netflix@example.com" should forward to "myreal@email.com"

  Scenario: Create alias with invalid format
    Given I am on the aliases page
    When I try to create an alias with invalid email format "not-an-email"
    Then the creation should fail
    And I should see an error "Invalid email address format"

  Scenario: Create duplicate alias
    Given I already have alias "contact@example.com"
    When I try to create another alias "contact@example.com"
    Then the creation should fail
    And I should see an error "Alias already exists"

  Scenario: View all aliases
    Given I have the following aliases:
      | alias                 | forward_to        | status  |
      | contact@example.com   | myreal@email.com  | enabled |
      | sales@example.com     | sales@team.com    | enabled |
      | old@example.com       | archive@test.com  | disabled|
    When I view my aliases list
    Then I should see 3 aliases
    And each alias should display its forwarding address and status

  Scenario: View alias details and statistics
    Given I have alias "contact@example.com"
    When I view the alias details
    Then I should see the forwarding address
    And I should see creation date
    And I should see number of emails received
    And I should see number of emails forwarded
    And I should see last activity timestamp

  Scenario: Update alias forwarding address
    Given I have alias "contact@example.com" forwarding to "old@email.com"
    When I update the forwarding address to "new@email.com"
    Then the alias should be updated
    And new emails should forward to "new@email.com"
    And I should see a success message

  Scenario: Update alias description
    Given I have alias "contact@example.com"
    When I update the description to "Updated contact form"
    Then the description should be saved
    And I should see the updated description in the alias list

  Scenario: Disable an active alias
    Given I have an enabled alias "spam@example.com"
    When I disable the alias
    Then the alias status should change to "disabled"
    And emails to "spam@example.com" should not be forwarded
    And I should see a confirmation message

  Scenario: Enable a disabled alias
    Given I have a disabled alias "contact@example.com"
    When I enable the alias
    Then the alias status should change to "enabled"
    And emails to "contact@example.com" should be forwarded again
    And I should see a success message

  Scenario: Delete an alias
    Given I have alias "temp@example.com"
    When I request to delete the alias
    Then I should see a confirmation dialog
    When I confirm the deletion
    Then the alias should be removed
    And emails to "temp@example.com" should bounce
    And I should see a success message

  Scenario: Search aliases
    Given I have multiple aliases configured
    When I search for "contact"
    Then I should see only aliases containing "contact"
    And other aliases should be filtered out

  Scenario: Filter aliases by status
    Given I have both enabled and disabled aliases
    When I filter by status "enabled"
    Then I should see only enabled aliases
    And disabled aliases should not be shown

  Scenario: Filter aliases by domain
    Given I have aliases on multiple domains:
      | alias               | domain      |
      | test@example.com    | example.com |
      | test@test.org       | test.org    |
    When I filter by domain "example.com"
    Then I should see only aliases for "example.com"

  Scenario: Pagination of aliases list
    Given I have 35 aliases configured
    When I view my aliases list with page size 20
    Then I should see 20 aliases on the first page
    And I should see pagination controls
    When I navigate to page 2
    Then I should see 15 aliases

  Scenario: Bulk disable aliases
    Given I have 5 enabled aliases selected
    When I perform bulk disable action
    Then all selected aliases should be disabled
    And I should see a confirmation message

  Scenario: Bulk delete aliases
    Given I have 3 aliases selected for deletion
    When I request bulk delete
    Then I should see a confirmation dialog
    When I confirm the bulk deletion
    Then all selected aliases should be removed
    And I should see a success message

  Scenario: Create alias for unverified domain
    Given I have an unverified domain "pending.com"
    When I try to create an alias "test@pending.com"
    Then the creation should fail
    And I should see an error "Domain must be verified first"
