    # check_site.py
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoMVP.settings') 
django.setup()

from django.contrib.sites.models import Site
from django.conf import settings

print(f"Checking Site configuration for SITE_ID={settings.SITE_ID}...")

try:
        site = Site.objects.get(id=settings.SITE_ID)
        print(f"-- Found Site: Domain='{site.domain}', Name='{site.name}'")
        
        # --- IMPORTANT: Update if domain is wrong ---
        expected_domain = 'localhost:8000' # Or '127.0.0.1:8000' depending on how you access runserver
        if site.domain != expected_domain:
            print(f"-- Updating domain from '{site.domain}' to '{expected_domain}'...")
            site.domain = expected_domain
            site.name = expected_domain # Often good to update name too
            site.save()
            print("-- Site updated.")
        else:
            print("-- Site domain looks correct.")
            
except Site.DoesNotExist:
        print(f"-- Site ID {settings.SITE_ID} does not exist. Creating it...")
        expected_domain = 'localhost:8000' # Or '127.0.0.1:8000'
        site = Site.objects.create(id=settings.SITE_ID, domain=expected_domain, name=expected_domain)
        print(f"-- Created Site ID {settings.SITE_ID} with domain '{site.domain}'.")

print("Site check complete.")