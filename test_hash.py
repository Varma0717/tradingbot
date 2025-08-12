from werkzeug.security import generate_password_hash, check_password_hash

# Test direct password hashing
password = "password123"
hash_value = generate_password_hash(password)
print(f"Hash: {hash_value}")
print(f"Check: {check_password_hash(hash_value, password)}")

# Test with different methods
print(f'Hash with pbkdf2: {generate_password_hash(password, method="pbkdf2")}')
pbkdf2_hash = generate_password_hash(password, method="pbkdf2")
print(f"Check pbkdf2: {check_password_hash(pbkdf2_hash, password)}")
