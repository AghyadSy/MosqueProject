import json
import os
import django

# 1. Set the environment variable to your project's settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_alrahmanmosque.settings')

# 2. Initialize Django (Do this BEFORE importing any models)
django.setup()

from core.models import Student, GroupSession, User, Page

pages = []

for i in range(1,31):
    data ={
        "section":i,
        "pages":[]
    }
    for page in Page.objects.filter(section=i).all():
        data["pages"].append(page.name)

    pages.append(data)

with open("pages.json", "w", encoding="utf-8") as json_file:
    json.dump(pages, json_file, indent=4)