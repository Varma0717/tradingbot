# Template Usage Analysis

## Used Templates (from routes analysis)

### Core Templates

- `index.html` - Homepage
- `layout.html` - Base layout (main)

### Auth Templates

- `auth/login.html` - Login page
- `auth/register.html` - Registration page

### User Templates

- `user/dashboard.html` - Main dashboard (primary)
- `user/unified_dashboard.html` - Alternative dashboard
- `user/orders.html` - Orders page
- `user/strategies.html` - Strategies page
- `user/settings.html` - Settings page
- `user/automation.html` - Automation controls
- `user/analytics.html` - Analytics dashboard
- `user/billing.html` - Billing & subscriptions
- `user/risk_management.html` - Risk management
- `user/strategy_library.html` - Strategy library
- `user/watchlists.html` - Watchlists
- `user/market_calendar.html` - Market calendar
- `user/education.html` - Education center
- `user/community.html` - Community features
- `user/support.html` - Support center
- `user/account_statement.html` - Account statements
- `user/tax_reports.html` - Tax reports

### Pages Templates

- `pages/about.html` - About page
- `pages/services.html` - Services page
- `pages/contact.html` - Contact page
- `pages/privacy.html` - Privacy policy
- `pages/terms.html` - Terms of service

### Admin Templates

- `admin/audit_trail.html` - Audit trail (referenced)

### Test Templates

- `test_bot_api.html` - Bot API testing

## Unused Templates (candidates for removal)

### Duplicate Layout Templates

- `layout.html.backup` - Backup layout
- `layout_backup.html` - Another backup layout
- `layout_clean.html` - Clean layout version
- `layout_new.html` - New layout version
- `enhanced_dashboard.html` - Root level dashboard duplicate

### Missing Templates (referenced but not found)

- `user/market_research.html` - Referenced in routes but missing

## CSS Issues

- `grid_trading.css` is imported in layout.html but conflicts with TailwindCSS
- Should use only TailwindCSS for consistency
