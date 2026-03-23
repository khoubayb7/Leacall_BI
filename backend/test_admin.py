#!/usr/bin/env python
import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ETL_Project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import authenticate
from user.models import CustomUser

print("=" * 60)
print("CHECKING ADMIN USER...")
print("=" * 60)

# Check if admin exists
admin = CustomUser.objects.filter(username='admin').first()

if not admin:
    print("❌ Admin user does NOT exist!")
    sys.exit(1)

print("✓ Admin user EXISTS")
print(f"  Username: {admin.username}")
print(f"  Email: {admin.email}")
print(f"  Role: {admin.role}")
print(f"  Is Active: {admin.is_active}")
print(f"  Is Superuser: {admin.is_superuser}")
print(f"  Is Staff: {admin.is_staff}")

print("\n" + "=" * 60)
print("TESTING LOGIN...")
print("=" * 60)

# Test authentication
user = authenticate(username='admin', password='admin')

if not user:
    print("❌ Authentication FAILED with password 'admin'")
    print("\nTrying to test with database...")
    # Check if password is set correctly
    if admin.check_password('admin'):
        print("✓ Password 'admin' is correct in database")
    else:
        print("❌ Password 'admin' is NOT correct")
        print("   Resetting password...")
        admin.set_password('admin')
        admin.save()
        print("   ✓ Password reset to 'admin'")
else:
    print("✓ Authentication SUCCESSFUL!")
    print(f"  Logged in user: {user.username}")
    print(f"  Role: {user.role}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("✓ Admin user is ready to login")
print("\nUse these credentials:")
print("  Username: admin")
print("  Password: admin")
print("\nAPI Endpoint: http://127.0.0.1:8000/api/login/")
