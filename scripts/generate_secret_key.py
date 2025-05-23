import secrets
import os
from pathlib import Path

def generate_secret_key(length=64):
    """Generate a secure random string suitable for SECRET_KEY."""
    return secrets.token_hex(length)

def update_env_file(secret_key):
    """Update or create .env file with the SECRET_KEY."""
    env_path = Path(__file__).parent.parent / '.env'
    
    # Check if .env file exists
    if env_path.exists():
        # Read existing content
        with open(env_path, 'r') as file:
            lines = file.readlines()
        
        # Check if SECRET_KEY already exists
        secret_key_exists = False
        for i, line in enumerate(lines):
            if line.startswith('SECRET_KEY='):
                lines[i] = f'SECRET_KEY={secret_key}\n'
                secret_key_exists = True
                break
        
        # Add SECRET_KEY if it doesn't exist
        if not secret_key_exists:
            lines.append(f'\nSECRET_KEY={secret_key}\n')
        
        # Write back to file
        with open(env_path, 'w') as file:
            file.writelines(lines)
    else:
        # Create new .env file
        with open(env_path, 'w') as file:
            file.write(f'SECRET_KEY={secret_key}\n')
    
    print(f"SECRET_KEY has been added to {env_path}")

if __name__ == "__main__":
    secret_key = generate_secret_key()
    update_env_file(secret_key)
    print("A new SECRET_KEY has been generated and saved to .env file")
    print("Make sure to keep this key secure and never commit it to version control")