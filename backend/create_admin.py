#!/usr/bin/env python
import os
import sys
import django
import warnings

# Suppress pydantic v1 deprecation warnings
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core._api.deprecation")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ETL_Project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from user.models import CustomUser

if not CustomUser.objects.filter(username='admin').exists():
    user = CustomUser.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin'
    )
    user.role = CustomUser.Role.ADMIN
    user.save()
    print('✓ Admin user created successfully!')
else:
    user = CustomUser.objects.get(username='admin')
    user.set_password('admin')
    user.role = CustomUser.Role.ADMIN
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print('✓ Admin user updated successfully!')

print('\n📝 Login credentials:')
print(f'  Username: admin')
print(f'  Password: admin')
print(f'  Email: {user.email}')
print(f'  Role: {user.role}')
