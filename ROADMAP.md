# smtpy Project Roadmap

This roadmap outlines major features to be implemented, inspired by ImprovMX and user feedback. Features are grouped by category and prioritized for development.

## 1. Alias Management
- [x] Multiple destination addresses per alias (forward to several emails)
- [ ] Alias expiration (temporary/expiring aliases)
- [ ] Bulk alias import/export (CSV or API)
- [ ] Alias groups or tags for organization
- [ ] Catch-all with exceptions (catch-all except for certain aliases)

## 2. SMTP & Deliverability
- [ ] Per-domain SMTP credentials (outbound relay)
- [ ] SMTP Auth for users (send mail through smtpy SMTP)
- [ ] Automatic DKIM key generation and rotation
- [ ] DMARC aggregate report viewing
- [ ] Spam/virus filtering (inbound mail scanning)

## 3. API & Automation
- [ ] Comprehensive REST API for all actions
- [ ] API key management (create, revoke, scope API keys)
- [ ] Webhooks for mail events

## 4. User & Team Management
- [ ] Multi-user/team support (invite teammates, assign roles per domain)
- [ ] Granular permissions (admin, billing, read-only, etc.)
- [ ] Audit log for all actions (not just mail events)

## 5. Mail Routing & Filtering
- [ ] Conditional forwarding rules (based on sender, subject, etc.)
- [ ] Block/allow lists (per alias or domain)

## 6. Monitoring & Analytics
- [ ] Detailed delivery analytics (open/click tracking, bounce reasons)
- [ ] Forwarding logs with search/filter/export
- [ ] Email delivery status notifications (alerts for bounces, failures)

## 7. User Experience & Support
- [ ] In-app guides and onboarding
- [ ] Live chat or support ticket integration
- [ ] White-labeling (custom branding for resellers)

## 8. Billing & Subscription
- [ ] Self-service billing portal
- [ ] Usage-based pricing, plan upgrades/downgrades
- [ ] Invoice history and download

## 9. Other Features
- [ ] Mobile-friendly admin panel (fully responsive, PWA)
- [ ] Custom domain for web admin (host your own branded panel)
- [ ] Premium routing (priority delivery) 