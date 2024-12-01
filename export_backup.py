import sys
from django.core.management import call_command

with open("backup.json", "w", encoding="utf-8") as f:
    call_command("dumpdata", stdout=f)
