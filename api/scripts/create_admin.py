import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.security.password import hash_password
from core.config import settings
from db.pool import init_pool, execute, fetch_one
from datetime import datetime, timezone

def create_admin_user(email: str, password: str, name: str):
    init_pool()

    password_hash = hash_password(password)
    created_at = datetime.now(timezone.utc)

    existing = fetch_one("SELECT id, email FROM users WHERE email = %s", (email,))

    if existing:
        print(f"User with email '{email}' already exists.")
        return True
    
    query = """
    INSERT INTO users (email, password_hash, name, role, active, created_at)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    try:
        result = execute(query, (email, password_hash, name, 'ADMIN', 1, created_at))

        if result:
            created_user = fetch_one("SELECT id, name, email, role, active, created_at FROM users WHERE email = %s", (email,))

            if created_user:
                print("Admin user created successfully:")
                print(f"    ID: {created_user['id']}")
                print(f"    Email: {created_user['email']}")
                print(f"    Name: {created_user['name']}")
                print(f"    Role: {created_user['role']}")
                return True
            else:
                print("User created but could not retrieve user details.")
                return False
        return False
    except Exception as e:
        print(f"An error occurred while creating the admin user: {e}")
        return False
    
if __name__ == "__main__":
    print(f"Creating admin user...")

    admin_data = {
        "email": settings.ADMIN_EMAIL.strip(),
        "password": settings.ADMIN_PASSWORD,
        "name": settings.ADMIN_USERNAME.strip(),
    }

    env_var_map = {
        "email": "ADMIN_EMAIL",
        "password": "ADMIN_PASSWORD",
        "name": "ADMIN_USERNAME",
    }
    missing_fields = [
        env_var_map[field_name]
        for field_name, value in admin_data.items()
        if not value
    ]
    if missing_fields:
        print("Missing required admin environment variables:")
        for field in missing_fields:
            print(f"  - {field}")
        sys.exit(1)

    print(f"Admin email: {admin_data['email']}")
    print(f"Admin username: {admin_data['name']}")

    success = create_admin_user(**admin_data)

    if success:
        print("Admin user creation completed successfully.")
    
    sys.exit(0 if success else 1)
