import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ETL_Project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import authenticate
from user.models import CustomUser

print("\n" + "="*60)
print("ADMIN USER TEST")
print("="*60)

# Get admin user
admin = CustomUser.objects.get(username='admin')
print(f"✓ User found: {admin.username}")
print(f"  Is Active: {admin.is_active}")
print(f"  Role: {admin.role}")
print(f"  Password hash exists: {bool(admin.password)}")

# Test authenticate
print("\nTesting authenticate('admin', 'admin')...")
auth_user = authenticate(username='admin', password='admin')

if auth_user:
    print(f"✓ Authentication SUCCESS!")
    print(f"  Authenticated user: {auth_user.username}")
else:
    print(f"✗ Authentication FAILED")
    print("\n  Resetting password to 'admin'...")
    admin.set_password('admin')
    admin.save()
    print(f"  ✓ Password reset")
    
    # Test again
    auth_user = authenticate(username='admin', password='admin')
    if auth_user:
        print(f"  ✓ Authentication now works!")
    else:
        print(f"  ✗ Still failing")

print("\n" + "="*60)
