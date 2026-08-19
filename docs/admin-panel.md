[Back to README](../README.md)

# Admin Panel

- URL: `/admin`
- Admin login authenticates against real app users: only active superusers may sign in (sessions expire after `ADMIN_SESSION_HOURS`, default 12h). In non-production environments the legacy `ADMIN_USERNAME`/`ADMIN_PASSWORD` credentials still work, to bootstrap the first admin account.
- To promote your first user to superuser in production: `UPDATE users SET is_superuser = 1 WHERE email = '...'` (or promote via the admin UI once another superuser exists)
- Includes a custom reports dashboard page at `/admin/reports`
- Guided workflow wizards at `/admin/workflows`: Restock, Invoicing, Close Drawer, and Refund
- Review Queue at `/admin/workflows/review`: resolve purchase invoices and supplier
  payments stuck in `pending_review` with inline approve/reject (superuser path,
  bypasses the self-approval guard)

See [Features → Admin Dashboard](features.md#admin-dashboard) for the full list of admin views and behaviors.
