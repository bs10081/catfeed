import secrets

def generate_secret_key(length=32):
    """Generate a secure secret key."""
    return secrets.token_hex(length)

if __name__ == '__main__':
    secret_key = generate_secret_key()
    print("\nGenerated SECRET_KEY:")
    print(f"{secret_key}\n")
    print("Copy this value and add it to your .env file as:")
    print(f"FLASK_SECRET_KEY={secret_key}\n")
