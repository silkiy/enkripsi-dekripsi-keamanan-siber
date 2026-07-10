import hashlib

def calculate_hash(filepath) -> str:
    """Menghitung hash SHA-256 berkas secara streaming."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()


def verify_integrity(hash1: str, hash2: str) -> bool:
    """Membandingkan dua hash secara constant-time."""
    return hashlib.pbkdf2_hmac('sha256', hash1.encode(), b'', 1) == \
        hashlib.pbkdf2_hmac('sha256', hash2.encode(), b'', 1)
