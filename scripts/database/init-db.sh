#!/bin/bash
# Database initialization script for WakeDock

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Default values
FORCE=false
SKIP_BACKUP=false
RESET=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --reset)
            RESET=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --force         Force initialization even if database exists"
            echo "  --skip-backup   Skip database backup before reset"
            echo "  --reset         Reset database (drop all tables and recreate)"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

log "Initializing WakeDock database..."

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    log "Loading environment variables from .env file..."
    set -a
    source .env
    set +a
fi

# Validate required environment variables
if [ -z "$DATABASE_URL" ]; then
    error "DATABASE_URL environment variable is not set"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

# Function to check if database exists and has tables
check_database_exists() {
    python -c "
import sys
import asyncio
from wakedock.database.database import check_database_exists

async def check():
    try:
        exists = await check_database_exists()
        sys.exit(0 if exists else 1)
    except Exception as e:
        print(f'Error checking database: {e}')
        sys.exit(2)

asyncio.run(check())
"
    return $?
}

# Function to backup database
backup_database() {
    if [ "$SKIP_BACKUP" = true ]; then
        log "Skipping database backup"
        return 0
    fi
    
    log "Creating database backup..."
    mkdir -p backups
    
    BACKUP_FILE="backups/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    if [[ "$DATABASE_URL" == postgresql* ]]; then
        # PostgreSQL backup
        pg_dump "$DATABASE_URL" > "$BACKUP_FILE"
        if [ $? -eq 0 ]; then
            success "Database backup created: $BACKUP_FILE"
            return 0
        else
            error "Failed to create database backup"
            return 1
        fi
    elif [[ "$DATABASE_URL" == sqlite* ]]; then
        # SQLite backup
        DB_FILE=$(echo "$DATABASE_URL" | sed 's|sqlite:///||')
        if [ -f "$DB_FILE" ]; then
            cp "$DB_FILE" "$BACKUP_FILE"
            success "Database backup created: $BACKUP_FILE"
            return 0
        else
            warn "SQLite database file not found: $DB_FILE"
            return 0
        fi
    else
        warn "Unsupported database type for backup. Skipping backup."
        return 0
    fi
}

# Function to reset database
reset_database() {
    log "Resetting database..."
    
    # Create backup before reset
    if ! backup_database; then
        error "Failed to create backup before reset"
        if [ "$FORCE" = false ]; then
            exit 1
        fi
    fi
    
    # Drop all tables using Alembic
    python -c "
import asyncio
from wakedock.database.database import drop_all_tables

async def reset():
    try:
        await drop_all_tables()
        print('Database reset successfully')
        return True
    except Exception as e:
        print(f'Database reset failed: {e}')
        return False

result = asyncio.run(reset())
exit(0 if result else 1)
"
    
    if [ $? -eq 0 ]; then
        success "Database reset successfully"
    else
        error "Database reset failed"
        exit 1
    fi
}

# Function to create initial admin user
create_admin_user() {
    log "Creating initial admin user..."
    
    python -c "
import asyncio
from wakedock.database.models import User
from wakedock.api.auth.password import hash_password
import os

async def create_admin():
    try:
        username = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
        password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin')
        email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@wakedock.local')
        
        # Check if admin user already exists
        existing_user = await User.get_by_username(username)
        if existing_user:
            print(f'Admin user {username} already exists')
            return True
        
        # Create admin user
        hashed_password = hash_password(password)
        admin_user = await User.create(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_admin=True,
            is_active=True
        )
        
        print(f'Admin user created: {username}')
        print(f'Default password: {password}')
        print('IMPORTANT: Change the default password after first login!')
        return True
        
    except Exception as e:
        print(f'Failed to create admin user: {e}')
        return False

result = asyncio.run(create_admin())
exit(0 if result else 1)
"
    
    if [ $? -eq 0 ]; then
        success "Admin user creation completed"
    else
        warn "Admin user creation failed (this may be normal if user already exists)"
    fi
}

# Function to seed initial data
seed_initial_data() {
    log "Seeding initial data..."
    
    python -c "
import asyncio
from wakedock.database.seed import seed_initial_data

async def seed():
    try:
        await seed_initial_data()
        print('Initial data seeded successfully')
        return True
    except Exception as e:
        print(f'Initial data seeding failed: {e}')
        return False

result = asyncio.run(seed())
exit(0 if result else 1)
"
    
    if [ $? -eq 0 ]; then
        success "Initial data seeded successfully"
    else
        warn "Initial data seeding failed (this may be normal)"
    fi
}

# Main execution
log "Starting database initialization process..."

# Check if reset is requested
if [ "$RESET" = true ]; then
    reset_database
fi

# Check if database already exists
if check_database_exists; then
    if [ "$FORCE" = false ] && [ "$RESET" = false ]; then
        log "Database already exists and is initialized"
        success "Database initialization completed (already exists)"
        exit 0
    fi
    
    if [ "$FORCE" = true ]; then
        warn "Forcing database initialization (existing data may be modified)"
    fi
fi

# Run Alembic migrations
log "Running database migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    success "Database migrations completed successfully"
else
    error "Database migrations failed"
    exit 1
fi

# Create admin user
create_admin_user

# Seed initial data
seed_initial_data

# Verify database state
log "Verifying database state..."
if check_database_exists; then
    success "Database initialization completed successfully"
    
    # Display summary
    echo ""
    log "Database initialization summary:"
    echo "  - Database schema: Created/Updated"
    echo "  - Admin user: Created (if not exists)"
    echo "  - Initial data: Seeded"
    echo ""
    log "Next steps:"
    echo "  1. Start the application: ./scripts/start.sh"
    echo "  2. Access the web interface at http://localhost:8000"
    echo "  3. Login with admin credentials"
    echo "  4. Change the default admin password"
    echo ""
else
    error "Database verification failed"
    exit 1
fi
