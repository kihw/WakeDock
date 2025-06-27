-- WakeDock Database Initialization Script
-- This script sets up the basic database structure for WakeDock

-- Create database if it doesn't exist (though PostgreSQL container usually handles this)
-- CREATE DATABASE IF NOT EXISTS wakedock;

-- Set up extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create basic tables structure (this will be handled by migrations in production)
-- The actual schema is managed by Alembic migrations in the application

-- Basic logging table for database operations
CREATE TABLE IF NOT EXISTS db_operations_log (
    id SERIAL PRIMARY KEY,
    operation VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT
);

-- Insert initial log entry
INSERT INTO db_operations_log (operation, details) 
VALUES ('database_initialized', 'WakeDock database initialized successfully');

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE wakedock TO wakedock;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO wakedock;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO wakedock;

-- Log completion
INSERT INTO db_operations_log (operation, details) 
VALUES ('permissions_granted', 'Database permissions configured for wakedock user');
