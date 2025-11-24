#!/usr/bin/env python3
"""
Better patch for edupage-api bug where rating can be None
This fixes the TypeError: cannot unpack non-iterable NoneType object
"""

import os

# Path to the lunches.py file in the venv
lunches_file = "backend/venv/lib/python3.13/site-packages/edupage_api/lunches.py"

print(f"Patching {lunches_file}...")

# Read the file
with open(lunches_file, 'r') as f:
    content = f.read()

# Define the buggy code section and the fixed version
buggy_section = """                if rating is not None and rating:
                    rating = rating.get(number)

                    [quality, quantity] = rating

                    quality_average = quality.get("priemer")
                    quality_ratings = quality.get("pocet")

                    quantity_average = quantity.get("priemer")
                    quantity_ratings = quantity.get("pocet")"""

fixed_section = """                if rating is not None and rating:
                    rating = rating.get(number)

                    if rating is not None:
                        [quality, quantity] = rating
                        
                        quality_average = quality.get("priemer") if quality else None
                        quality_ratings = quality.get("pocet") if quality else None

                        quantity_average = quantity.get("priemer") if quantity else None
                        quantity_ratings = quantity.get("pocet") if quantity else None
                    else:
                        quality_average = None
                        quality_ratings = None
                        quantity_average = None
                        quantity_ratings = None"""

if buggy_section in content:
    content = content.replace(buggy_section, fixed_section)
    with open(lunches_file, 'w') as f:
        f.write(content)
    print("✅ Patch applied successfully!")
    print("The app should now be able to load past lunches and show ordered status.")
else:
    print("❌ Could not find the exact section to patch.")
    print("The library might have been updated or already patched.")
