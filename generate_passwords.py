"""
generate_passwords.py
---------------------
Run this ONCE to generate hashed passwords for your config.yaml.

Usage:
    python generate_passwords.py

Then copy the hashed values into config.yaml.
NEVER store plain passwords in config.yaml.
"""

import bcrypt

def hash_password(plain_password: str) -> str:
    """
    Converts a plain text password into a safe hashed version.
    bcrypt is a one-way hash — it cannot be reversed back to the original.
    """
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt(12))
    return hashed.decode("utf-8")

print("=" * 55)
print("  SPLIT_WISE — Password Hash Generator")
print("=" * 55)

# ── Enter your chosen passwords here ──────────────────────
NEENA_PASSWORD  = "your_password_here"   # ← change this to your password
SHOBIN_PASSWORD = "your_password_here"  # ← change this to your password
# ──────────────────────────────────────────────────────────

neena_hash  = hash_password(NEENA_PASSWORD)
shobin_hash = hash_password(SHOBIN_PASSWORD)

print(f"\nNeena's hash:\n  {neena_hash}")
print(f"\nShobin's hash:\n  {shobin_hash}")

print("\n" + "=" * 55)
print("Copy these hashes into config.yaml under 'password:'")
print("=" * 55)
