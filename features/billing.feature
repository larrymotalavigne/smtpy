Feature: Billing and Subscription Management

  As a user
  I want to manage my subscription and billing
  So that I can access premium features and maintain my service

  Background:
    Given I am logged in as a user
    And the SMTPy API server is running
    And Stripe integration is configured

  Scenario: View available subscription plans
    Given I am not subscribed to any plan
    When I navigate to the billing page
    Then I should see available subscription plans
    And each plan should display:
      | field           | description                    |
      | Plan name       | Free/Pro/Business              |
      | Monthly price   | Pricing amount                 |
      | Features        | List of included features      |
      | Limits          | Domain/alias/message limits    |

  Scenario: Subscribe to Pro plan
    Given I am on the Free plan
    When I click "Subscribe" on the Pro plan
    Then I should be redirected to Stripe checkout
    And the checkout should display the Pro plan details
    When I complete the payment successfully
    Then I should be redirected back to SMTPy
    And my plan should be upgraded to "Pro"
    And I should see a success message
    And I should receive a confirmation email

  Scenario: Failed subscription payment
    Given I am attempting to subscribe to Pro plan
    When I enter invalid payment details in Stripe checkout
    Then the payment should fail
    And I should see an error message
    And I should remain on the Free plan
    And no charge should be made

  Scenario: View current subscription details
    Given I am subscribed to the Pro plan
    When I view my billing page
    Then I should see my current plan as "Pro"
    And I should see my billing cycle
    And I should see the next billing date
    And I should see my payment method
    And I should see my current usage statistics

  Scenario: View billing history
    Given I have an active subscription
    When I view my billing page
    And I click "View billing history"
    Then I should see a list of past invoices
    And each invoice should show:
      | field        | description                |
      | Date         | Invoice date               |
      | Amount       | Charged amount             |
      | Status       | Paid/Pending/Failed        |
      | Download     | PDF download link          |

  Scenario: Download invoice
    Given I have a paid invoice
    When I click "Download" on the invoice
    Then I should receive a PDF file
    And the PDF should contain invoice details
    And the PDF should include payment information

  Scenario: Update payment method
    Given I have an active subscription
    When I click "Manage billing" on the billing page
    Then I should be redirected to Stripe Customer Portal
    And I should be able to update my payment method
    When I update my card details
    Then my new payment method should be saved
    And I should be redirected back to SMTPy
    And I should see a success message

  Scenario: Cancel subscription
    Given I am subscribed to the Pro plan
    When I click "Manage billing"
    And I navigate to the Customer Portal
    And I click "Cancel subscription"
    Then I should see a cancellation confirmation
    When I confirm the cancellation
    Then my subscription should be scheduled for cancellation
    And I should have access until the end of the billing period
    And I should see the cancellation date

  Scenario: Subscription cancellation at period end
    Given I have cancelled my subscription
    And my subscription is set to end on "2024-02-01"
    When the date reaches "2024-02-01"
    Then my subscription should be downgraded to Free plan
    And my features should be limited to Free plan limits
    And I should receive a cancellation confirmation email

  Scenario: Reactivate cancelled subscription
    Given I have cancelled my subscription
    And my subscription has not yet ended
    When I click "Reactivate subscription"
    Then my subscription should be reactivated
    And the cancellation should be cancelled
    And I should see a success message
    And my billing should continue as normal

  Scenario: Upgrade from Pro to Business plan
    Given I am on the Pro plan
    When I click "Upgrade" on the Business plan
    Then I should be redirected to Stripe checkout
    When I complete the upgrade
    Then my plan should be changed to "Business"
    And I should be charged the prorated amount
    And my limits should be updated to Business tier

  Scenario: Downgrade from Business to Pro plan
    Given I am on the Business plan
    When I request to downgrade to Pro plan
    Then I should see a confirmation dialog
    And I should be warned about reduced limits
    When I confirm the downgrade
    Then my plan should be scheduled to downgrade at period end
    And I should see the effective date
    And I should retain Business features until the end of the billing period

  Scenario: View usage against plan limits
    Given I am on the Pro plan with limits:
      | resource | limit |
      | Domains  | 5     |
      | Aliases  | 100   |
      | Messages | 10000 |
    When I view my billing page
    Then I should see my current usage:
      | resource | used | limit | percentage |
      | Domains  | 3    | 5     | 60%        |
      | Aliases  | 45   | 100   | 45%        |
      | Messages | 2500 | 10000 | 25%        |

  Scenario: Exceeding plan limits triggers upgrade prompt
    Given I am on the Pro plan
    And I have reached 100% of my alias limit
    When I try to create a new alias
    Then I should see a limit exceeded message
    And I should see a prompt to upgrade to Business plan
    When I click "Upgrade now"
    Then I should be directed to the upgrade flow

  Scenario: Webhook processing for successful payment
    Given I have an active subscription
    When Stripe sends a "payment_succeeded" webhook
    Then the system should process the webhook
    And the payment should be recorded
    And my subscription should be extended
    And I should receive a payment confirmation email

  Scenario: Webhook processing for failed payment
    Given I have an active subscription
    When Stripe sends a "payment_failed" webhook
    Then the system should process the webhook
    And I should receive a payment failed email
    And I should see a warning on my billing page
    And I should be prompted to update my payment method

  Scenario: Access customer portal
    Given I have an active subscription
    When I click "Manage billing"
    Then I should be redirected to Stripe Customer Portal
    And I should see my subscription details
    And I should be able to update payment method
    And I should be able to view invoices
    When I return to SMTPy
    Then I should be redirected back to the billing page
