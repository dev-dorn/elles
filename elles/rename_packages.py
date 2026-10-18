# ~/projects/elles/elles/rename_packages.py
import os
import re

# Define your services here.
# Format: "path_to_service_folder": "new_package_name"
SERVICES = {
    "backend/identity-service": "identity_app",
    "backend/catalog-service": "catalog_app",
    "backend/order-service": "order_app",
    "backend/payment-service": "payment_app",
    # Add future services here
}

def rename_service_app(service_path, new_name):
    old_dir = os.path.join(service_path, "app")
    new_dir = os.path.join(service_path, new_name)

    if not os.path.exists(old_dir):
        print(f"⚠️  Skipping {service_path}: 'app' directory not found.")
        return

    # 1. Rename the physical directory
    os.rename(old_dir, new_dir)
    print(f"📁 Renamed directory: {old_dir} -> {new_dir}")

    # 2. Update all internal Python imports
    for root, _, files in os.walk(new_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Strictly replace 'from app.' and 'import app.'
                new_content = re.sub(r'\bfrom app\.', f'from {new_name}.', content)
                new_content = re.sub(r'\bimport app\.', f'import {new_name}.', new_content)

                if new_content != content:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"  🔄 Updated imports in {filepath}")

if __name__ == "__main__":
    print(" Starting package rename process...\n")
    for path, new_name in SERVICES.items():
        rename_service_app(path, new_name)
    print("\n✅ Done! Don't forget to update your uvicorn entrypoints and Dockerfiles.")