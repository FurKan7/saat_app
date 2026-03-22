-- Admins are normal users; grant access via users.is_admin (or env bootstrap on API).
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN users.is_admin IS 'When true, user may access /admin APIs and dashboard.';
