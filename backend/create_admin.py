#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ETL_Project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('✓ Admin user created successfully!')
else:
    u = User.objects.get(username='admin')
    u.set_password('admin')
    u.save()
    print('✓ Admin user password updated successfully!')
