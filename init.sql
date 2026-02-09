-- PostgreSQL initialization script for welding system
-- This script runs when the container starts for the first time

-- Enable UUID extension (useful for future features)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create additional indexes for better performance
-- These will be created after tables are created by SQLAlchemy

-- Set timezone to match the application
SET timezone = 'Asia/Shanghai';

-- Create default roles and permissions data will be handled by the application
-- The database schema will be created by SQLAlchemy Alembic migrations