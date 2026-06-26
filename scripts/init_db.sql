-- ============================================================
-- DATABASE INITIALIZATION SCRIPT
-- Runs automatically on first PostgreSQL startup
-- ============================================================

-- Enable UUID extension (useful for future features)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for faster text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Log that init script ran
DO $$
BEGIN
    RAISE NOTICE 'LegalTech database initialized successfully.';
END $$;