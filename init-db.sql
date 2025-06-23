-- Initialize Therapy Assistant Database
-- This script sets up the initial database structure

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Create initial schema (tables will be created by Alembic migrations)
-- This file ensures the database is properly initialized