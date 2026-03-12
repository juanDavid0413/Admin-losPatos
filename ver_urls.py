import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.urls import reverse, NoReverseMatch
from django.urls.resolvers import get_resolver

resolver = get_resolver()

print("=== URLs de table_sessions ===")
for key, val in resolver.reverse_dict.items():
    if isinstance(key, str) and 'session' in key.lower():
        print(f"  {key}")

print()
print("=== URLs de machines ===")
for key, val in resolver.reverse_dict.items():
    if isinstance(key, str) and ('maquin' in key.lower() or 'machine' in key.lower() or 'payment' in key.lower()):
        print(f"  {key}")

print()
print("=== Todas las URL names registradas ===")
names = sorted([k for k in resolver.reverse_dict.keys() if isinstance(k, str)])
for n in names:
    print(f"  {n}")
