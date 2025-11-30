Feature: Domain Management

  As a user
  I want to manage my email domains
  So that I can receive and forward emails through my custom domains

  Background:
    Given I am logged in as a user
    And the SMTPy API server is running

  Scenario: Add a new domain
    Given I have no domains configured
    When I add a domain "example.com"
    Then the domain should be created successfully
    And DNS configuration records should be generated
    And the domain should appear in my domains list
    And the domain verification status should be "pending"

  Scenario: Add duplicate domain
    Given I already have domain "example.com" configured
    When I try to add the same domain "example.com"
    Then the operation should fail
    And I should see an error "Domain already exists"

  Scenario: View domain list
    Given I have the following domains configured:
      | domain        | status   |
      | example.com   | verified |
      | test.org      | pending  |
      | mymail.net    | failed   |
    When I view my domains list
    Then I should see 3 domains
    And each domain should display its verification status

  Scenario: View domain details
    Given I have domain "example.com" configured
    When I view the details of "example.com"
    Then I should see the domain name
    And I should see DNS configuration records including:
      | record_type | purpose |
      | MX          | Mail exchange |
      | SPF         | Sender authentication |
      | DKIM        | Email signing |
      | DMARC       | Policy enforcement |
    And I should see the verification status
    And I should see domain statistics

  Scenario: Verify domain DNS configuration
    Given I have domain "example.com" with status "pending"
    And I have configured all required DNS records correctly
    When I trigger DNS verification
    Then the verification should succeed
    And the domain status should change to "verified"
    And I should see a success message

  Scenario: Failed DNS verification - Missing MX record
    Given I have domain "example.com" with status "pending"
    And the MX record is not configured
    When I trigger DNS verification
    Then the verification should fail
    And I should see an error "MX record not found"
    And the domain status should remain "pending"

  Scenario: Failed DNS verification - Incorrect SPF record
    Given I have domain "example.com" with status "pending"
    And the SPF record is incorrectly configured
    When I trigger DNS verification
    Then the verification should fail
    And I should see an error explaining the SPF issue
    And I should see the expected SPF record value

  Scenario: Update domain settings
    Given I have domain "example.com" configured
    When I update the domain settings:
      | catch_all | enabled |
      | enabled   | true    |
    Then the domain settings should be updated
    And I should see a success message

  Scenario: Enable catch-all for domain
    Given I have domain "example.com" with catch-all disabled
    When I enable catch-all forwarding
    Then all emails to any address @example.com should be forwarded
    And the catch-all status should show as "enabled"

  Scenario: Disable domain
    Given I have an active domain "example.com"
    When I disable the domain
    Then the domain status should change to "disabled"
    And emails to this domain should not be processed
    And I should see a confirmation message

  Scenario: Delete domain
    Given I have domain "example.com" configured
    When I request to delete "example.com"
    Then I should see a confirmation dialog
    When I confirm the deletion
    Then the domain should be removed
    And all associated aliases should be deleted
    And I should see a success message

  Scenario: Delete domain with active aliases
    Given I have domain "example.com" with 5 active aliases
    When I try to delete "example.com"
    Then I should see a warning about losing aliases
    And I should be asked to confirm
    When I confirm the deletion
    Then the domain and all aliases should be deleted

  Scenario: Pagination of domains list
    Given I have 25 domains configured
    When I view my domains list with page size 10
    Then I should see 10 domains on the first page
    And I should see pagination controls
    When I navigate to page 2
    Then I should see 10 more domains
    When I navigate to page 3
    Then I should see 5 domains

  Scenario: Search domains
    Given I have multiple domains configured
    When I search for "example"
    Then I should see only domains containing "example"
    And other domains should be filtered out

  Scenario: Filter domains by verification status
    Given I have domains with different verification statuses
    When I filter by status "verified"
    Then I should see only verified domains
    And pending or failed domains should not be shown
