# WakeDock Admin User Management Documentation

## 🔐 Administration User Creation Process

### Overview
WakeDock automatically creates a default admin user during the first database initialization. This ensures that there's always an administrative account available for system management.

### Default Admin User Credentials

**Username:** `admin`  
**Email:** `admin@wakedock.com`  
**Password:** `admin123` (configurable via environment variables)  
**Role:** `ADMIN`  
**Status:** Active and verified by default

### 🚀 Automatic Admin User Creation

#### 1. Database Initialization Trigger
The admin user is automatically created during database initialization in the following scenarios:
- First application startup
- Database reset/migration
- Manual database initialization

#### 2. Creation Process Location
**File:** `src/wakedock/database/database.py`  
**Function:** `_seed_default_data()` (lines 180-212)

```python
def _seed_default_data(self, session: Session) -> None:
    """Seed the database with default data."""
    # Create default admin user if it doesn't exist
    admin_user = session.query(User).filter(User.username == "admin").first()
    if not admin_user:
        admin_user = User(
            username="admin",
            email="admin@wakedock.com",
            hashed_password=hash_password(self.settings.wakedock.admin_password),
            full_name="Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        session.add(admin_user)
        session.commit()
```

#### 3. Configuration Options
**Environment Variables:**
- `DEFAULT_ADMIN_USERNAME`: Default admin username (default: 'admin')
- `DEFAULT_ADMIN_PASSWORD`: Default admin password (default: 'admin123')  
- `DEFAULT_ADMIN_EMAIL`: Default admin email (default: 'admin@wakedock.com')

**Configuration File:** `src/wakedock/config.py`
```python
# Default admin password
admin_password: str = "admin123"
```

### 🔧 Manual Admin User Management

#### 1. Database CLI Commands
```bash
# Initialize database with admin user
docker-compose exec wakedock python -m wakedock.database.cli init

# Reset database (recreates admin user)
docker-compose exec wakedock python -m wakedock.database.cli reset
```

#### 2. Management Script
```bash
# Initialize database with admin user
docker-compose exec wakedock python manage.py init-db
```

#### 3. Shell Script Initialization
```bash
# Run the database initialization script
./scripts/init-db.sh
```

### 🛡️ Security Considerations

#### 1. Password Security
- Default password should be changed immediately after first login
- Password uses bcrypt hashing with secure salt
- Password validation enforces strong password requirements

#### 2. Access Control
- Admin users have full system access
- Role-based access control (RBAC) implementation
- JWT token-based authentication

#### 3. Production Deployment
**⚠️ IMPORTANT:** Always change default credentials in production!

```bash
# Set secure admin password via environment variable
export DEFAULT_ADMIN_PASSWORD="your-secure-password-here"
```

### 🔄 Database Schema

#### User Model Structure
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
```

#### User Roles
```python
class UserRole(Enum):
    ADMIN = "ADMIN"      # Full system access
    USER = "USER"        # Standard user access
    VIEWER = "VIEWER"    # Read-only access
```

### 📋 API Endpoints

#### Authentication Endpoints
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/me` - Current user info
- `PUT /auth/me` - Update current user

#### Admin-Only Endpoints
- `GET /auth/users` - List all users
- `GET /auth/users/{user_id}` - Get specific user
- `PUT /auth/users/{user_id}` - Update user
- `DELETE /auth/users/{user_id}` - Delete user

### 🧪 Testing Admin User Creation

#### 1. Verify Admin User Exists
```bash
docker-compose exec -T wakedock python -c "
from wakedock.database.database import DatabaseManager
from wakedock.database.models import User

db_manager = DatabaseManager()
db_manager.initialize()

with db_manager.get_session() as session:
    admin_user = session.query(User).filter(User.username == 'admin').first()
    if admin_user:
        print(f'Admin user exists: {admin_user.username} ({admin_user.email})')
        print(f'Role: {admin_user.role}')
        print(f'Active: {admin_user.is_active}')
        print(f'Verified: {admin_user.is_verified}')
    else:
        print('Admin user not found!')
"
```

#### 2. Test Admin Login
```bash
# Test login via API
curl -X POST "http://YOUR_IP:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 🔍 Troubleshooting

#### Issue: Admin User Not Created
**Cause:** Database initialization failed or was interrupted
**Solution:** 
```bash
# Reinitialize database
docker-compose exec wakedock python manage.py init-db
```

#### Issue: Cannot Login with Admin Credentials
**Cause:** Password mismatch or database corruption
**Solution:**
```bash
# Reset admin password
docker-compose exec wakedock python -c "
from wakedock.database.database import DatabaseManager
from wakedock.database.models import User
from wakedock.api.auth.password import hash_password

db_manager = DatabaseManager()
db_manager.initialize()

with db_manager.get_session() as session:
    admin_user = session.query(User).filter(User.username == 'admin').first()
    if admin_user:
        admin_user.hashed_password = hash_password('admin123')
        session.commit()
        print('Admin password reset successfully')
"
```

### 🎯 Best Practices

1. **Change Default Credentials:** Always change admin password on first login
2. **Use Environment Variables:** Configure admin credentials via environment variables
3. **Regular Backups:** Backup user database regularly
4. **Monitor Access:** Log and monitor admin access attempts
5. **Role Separation:** Create separate admin accounts for different administrators

### 📊 Admin User Status
- ✅ **Verified:** Admin user creation is automatic and verified
- ✅ **Tested:** Admin user creation tested during system restart
- ✅ **Secure:** Password hashing and validation implemented
- ✅ **Configurable:** Credentials configurable via environment variables

---

**Last Updated:** July 4, 2025  
**Version:** WakeDock v1.0.0  
**Status:** Production Ready 🚀