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

if not CustomUser.objects.filter(username='wael').exists():
    user = CustomUser.objects.create_superuser(
        username='wael',
        email='wael@example.com',
        password='wael'
    )
    user.role = CustomUser.Role.ADMIN
    user.save()
    print('✓ Wael user created successfully!')
else:
    user = CustomUser.objects.get(username='wael')
    user.set_password('wael')
    user.role = CustomUser.Role.ADMIN
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print('✓ Wael user updated successfully!')

print('\n📝 Login credentials:')
print(f'  Username: wael')
print(f'  Password: wael')
print(f'  Email: {user.email}')
print(f'  Role: {user.role}')
