"""User model using Apex quick_user factory"""
from apex import quick_user

# Create User model with Apex's quick_user factory
User = quick_user(
    __tablename__="users",
    full_name=True,      # Adds full_name: str field
    username=True,       # Adds username: str field  
    is_active=True,      # Adds is_active: bool field (default True)
    is_superuser=True,   # Adds is_superuser: bool field (default False)
)

