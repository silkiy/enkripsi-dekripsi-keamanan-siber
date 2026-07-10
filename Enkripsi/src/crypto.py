import os
import struct
import base64
from cryptography.hazmat.primitives.asymmetric import x25519, rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives import hmac

def generate_key(key_dir="keys", key_type="X25519"):
    """Membuat pasangan kunci (X25519 atau RSA) dan menyimpannya ke folder dalam format PEM."""
    os.makedirs(key_dir, exist_ok=True)
    
    if key_type == "X25519":
        priv_key = x25519.X25519PrivateKey.generate()
        pub_key = priv_key.public_key()
        
        pem_priv = priv_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        pem_pub = pub_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    elif key_type.startswith("RSA"):
        key_size = 2048
        if "-" in key_type:
            try:
                key_size = int(key_type.split("-")[1])
            except ValueError:
                pass
                
        priv_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        pub_key = priv_key.public_key()
        
        pem_priv = priv_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        pem_pub = pub_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    else:
        raise ValueError(f"Jenis kunci tidak didukung: {key_type}")
        
    with open(os.path.join(key_dir, "private_key.pem"), "wb") as f:
        f.write(pem_priv)
        
    with open(os.path.join(key_dir, "public_key.pem"), "wb") as f:
        f.write(pem_pub)
        
    return priv_key, pub_key


def load_private_key(filepath):
    """Memuat kunci privat (RSA atau X25519) dari file PEM."""
    with open(filepath, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def load_public_key(filepath):
    """Memuat kunci publik (RSA atau X25519) dari file PEM."""
    with open(filepath, "rb") as f:
        return serialization.load_pem_public_key(f.read())


def encrypt_message(message: str, bob_pub_key, method: int = 1) -> str:
    """Mengenkripsi pesan menggunakan salah satu dari 4 metode enkripsi."""
    if method == 1:
        # X25519 + AES-256-GCM
        if not isinstance(bob_pub_key, x25519.X25519PublicKey):
            raise ValueError("Metode 1 membutuhkan Kunci Publik X25519.")
            
        ephemeral_priv = x25519.X25519PrivateKey.generate()
        ephemeral_pub = ephemeral_priv.public_key()
        
        shared_secret = ephemeral_priv.exchange(bob_pub_key)
        session_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"e2ee-message-session"
        ).derive(shared_secret)
        
        nonce = os.urandom(12)
        aesgcm = AESGCM(session_key)
        ciphertext_with_tag = aesgcm.encrypt(nonce, message.encode('utf-8'), None)
        
        tag = ciphertext_with_tag[-16:]
        ct = ciphertext_with_tag[:-16]
        
        ephemeral_pub_bytes = ephemeral_pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        packet = b'\x01' + ephemeral_pub_bytes + nonce + tag + ct
        
    elif method == 2:
        # X25519 + ChaCha20-Poly1305
        if not isinstance(bob_pub_key, x25519.X25519PublicKey):
            raise ValueError("Metode 2 membutuhkan Kunci Publik X25519.")
            
        ephemeral_priv = x25519.X25519PrivateKey.generate()
        ephemeral_pub = ephemeral_priv.public_key()
        
        shared_secret = ephemeral_priv.exchange(bob_pub_key)
        session_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"e2ee-message-session"
        ).derive(shared_secret)
        
        nonce = os.urandom(12)
        chacha = ChaCha20Poly1305(session_key)
        ciphertext_with_tag = chacha.encrypt(nonce, message.encode('utf-8'), None)
        
        tag = ciphertext_with_tag[-16:]
        ct = ciphertext_with_tag[:-16]
        
        ephemeral_pub_bytes = ephemeral_pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        packet = b'\x02' + ephemeral_pub_bytes + nonce + tag + ct
        
    elif method == 3:
        # RSA + AES-256-GCM
        if not isinstance(bob_pub_key, rsa.RSAPublicKey):
            raise ValueError("Metode 3 membutuhkan Kunci Publik RSA.")
            
        session_key = os.urandom(32)
        enc_session_key = bob_pub_key.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        nonce = os.urandom(12)
        aesgcm = AESGCM(session_key)
        ciphertext_with_tag = aesgcm.encrypt(nonce, message.encode('utf-8'), None)
        
        tag = ciphertext_with_tag[-16:]
        ct = ciphertext_with_tag[:-16]
        
        packet = b'\x03' + struct.pack(">I", len(enc_session_key)) + enc_session_key + nonce + tag + ct
        
    elif method == 4:
        # RSA + AES-256-CBC + HMAC-SHA256
        if not isinstance(bob_pub_key, rsa.RSAPublicKey):
            raise ValueError("Metode 4 membutuhkan Kunci Publik RSA.")
            
        aes_key = os.urandom(32)
        hmac_key = os.urandom(32)
        combined_keys = aes_key + hmac_key
        
        enc_keys = bob_pub_key.encrypt(
            combined_keys,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        iv = os.urandom(16)
        
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(message.encode('utf-8')) + padder.finalize()
        
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        ct = encryptor.update(padded_data) + encryptor.finalize()
        
        header = b'\x04' + struct.pack(">I", len(enc_keys)) + enc_keys + iv
        
        h = hmac.HMAC(hmac_key, hashes.SHA256())
        h.update(header + ct)
        hmac_tag = h.finalize()
        
        packet = header + hmac_tag + ct
        
    else:
        raise ValueError("Metode enkripsi tidak dikenal.")
        
    return base64.b64encode(packet).decode('utf-8')


def decrypt_message(encrypted_msg_b64: str, bob_priv_key) -> str:
    """Mendekripsi pesan terenkripsi secara otomatis mendeteksi metodenya."""
    packet = base64.b64decode(encrypted_msg_b64.encode('utf-8'))
    if len(packet) < 1:
        raise ValueError("Ukuran data terenkripsi kosong.")
        
    first_byte = packet[0:1]
    if first_byte in (b'\x01', b'\x02', b'\x03', b'\x04'):
        method = packet[0]
    else:
        # Legacy format (tidak diawali identifier, selalu diasumsikan X25519 + AES-GCM)
        method = 1
        # Sisipkan b'\x01' di awal agar pemrosesan parsing sama dengan Method 1 baru
        packet = b'\x01' + packet
        
    if method == 1:
        if not isinstance(bob_priv_key, x25519.X25519PrivateKey):
            raise ValueError("Kunci privat Anda bukan tipe X25519 yang dibutuhkan Metode 1.")
            
        if len(packet) < 61:
            raise ValueError("Data terenkripsi Metode 1 terlalu pendek.")
            
        ephemeral_pub_bytes = packet[1:33]
        nonce = packet[33:45]
        tag = packet[45:61]
        ct = packet[61:]
        
        ephemeral_pub = x25519.X25519PublicKey.from_public_bytes(ephemeral_pub_bytes)
        shared_secret = bob_priv_key.exchange(ephemeral_pub)
        session_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"e2ee-message-session"
        ).derive(shared_secret)
        
        aesgcm = AESGCM(session_key)
        plaintext_bytes = aesgcm.decrypt(nonce, ct + tag, None)
        
    elif method == 2:
        if not isinstance(bob_priv_key, x25519.X25519PrivateKey):
            raise ValueError("Kunci privat Anda bukan tipe X25519 yang dibutuhkan Metode 2.")
            
        if len(packet) < 61:
            raise ValueError("Data terenkripsi Metode 2 terlalu pendek.")
            
        ephemeral_pub_bytes = packet[1:33]
        nonce = packet[33:45]
        tag = packet[45:61]
        ct = packet[61:]
        
        ephemeral_pub = x25519.X25519PublicKey.from_public_bytes(ephemeral_pub_bytes)
        shared_secret = bob_priv_key.exchange(ephemeral_pub)
        session_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"e2ee-message-session"
        ).derive(shared_secret)
        
        chacha = ChaCha20Poly1305(session_key)
        plaintext_bytes = chacha.decrypt(nonce, ct + tag, None)
        
    elif method == 3:
        if not isinstance(bob_priv_key, rsa.RSAPrivateKey):
            raise ValueError("Kunci privat Anda bukan tipe RSA yang dibutuhkan Metode 3.")
            
        if len(packet) < 33: # Minimal: method(1) + len(4) + enc_session_key(minimal) + nonce(12) + tag(16)
            raise ValueError("Data terenkripsi Metode 3 terlalu pendek.")
            
        enc_session_key_len = struct.unpack(">I", packet[1:5])[0]
        if len(packet) < 5 + enc_session_key_len + 28:
            raise ValueError("Data terenkripsi Metode 3 tidak lengkap.")
            
        enc_session_key = packet[5 : 5+enc_session_key_len]
        nonce = packet[5+enc_session_key_len : 5+enc_session_key_len+12]
        tag = packet[5+enc_session_key_len+12 : 5+enc_session_key_len+28]
        ct = packet[5+enc_session_key_len+28:]
        
        session_key = bob_priv_key.decrypt(
            enc_session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        aesgcm = AESGCM(session_key)
        plaintext_bytes = aesgcm.decrypt(nonce, ct + tag, None)
        
    elif method == 4:
        if not isinstance(bob_priv_key, rsa.RSAPrivateKey):
            raise ValueError("Kunci privat Anda bukan tipe RSA yang dibutuhkan Metode 4.")
            
        if len(packet) < 53: # method(1) + len(4) + enc_keys(min) + IV(16) + HMAC(32)
            raise ValueError("Data terenkripsi Metode 4 terlalu pendek.")
            
        enc_keys_len = struct.unpack(">I", packet[1:5])[0]
        if len(packet) < 5 + enc_keys_len + 48:
            raise ValueError("Data terenkripsi Metode 4 tidak lengkap.")
            
        enc_keys = packet[5 : 5+enc_keys_len]
        iv = packet[5+enc_keys_len : 5+enc_keys_len+16]
        hmac_tag = packet[5+enc_keys_len+16 : 5+enc_keys_len+48]
        ct = packet[5+enc_keys_len+48:]
        
        combined_keys = bob_priv_key.decrypt(
            enc_keys,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        aes_key = combined_keys[:32]
        hmac_key = combined_keys[32:]
        
        header = packet[: 5+enc_keys_len+16]
        h = hmac.HMAC(hmac_key, hashes.SHA256())
        h.update(header + ct)
        h.verify(hmac_tag)
        
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ct) + decryptor.finalize()
        
        unpadder = sym_padding.PKCS7(128).unpadder()
        plaintext_bytes = unpadder.update(padded_data) + unpadder.finalize()
        
    else:
        raise ValueError("Metode enkripsi tidak dikenal.")
        
    return plaintext_bytes.decode('utf-8')


def encrypt_file(input_path, output_path, bob_pub_key, method: int = 1, chunk_size=65536):
    """Mengenkripsi file secara chunk-by-chunk menggunakan salah satu dari 4 metode enkripsi."""
    file_size = os.path.getsize(input_path)
    
    if method in (1, 2):
        if not isinstance(bob_pub_key, x25519.X25519PublicKey):
            raise ValueError("Metode membutuhkan Kunci Publik X25519.")
            
        ephemeral_priv = x25519.X25519PrivateKey.generate()
        ephemeral_pub = ephemeral_priv.public_key()
        
        shared_secret = ephemeral_priv.exchange(bob_pub_key)
        session_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"e2ee-file-session"
        ).derive(shared_secret)
        
        ephemeral_pub_bytes = ephemeral_pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        base_nonce = os.urandom(12)
        header = bytes([method]) + ephemeral_pub_bytes + base_nonce
        
    elif method == 3:
        if not isinstance(bob_pub_key, rsa.RSAPublicKey):
            raise ValueError("Metode 3 membutuhkan Kunci Publik RSA.")
            
        session_key = os.urandom(32)
        enc_session_key = bob_pub_key.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        base_nonce = os.urandom(12)
        header = b'\x03' + struct.pack(">I", len(enc_session_key)) + enc_session_key + base_nonce
        
    elif method == 4:
        if not isinstance(bob_pub_key, rsa.RSAPublicKey):
            raise ValueError("Metode 4 membutuhkan Kunci Publik RSA.")
            
        aes_key = os.urandom(32)
        hmac_key = os.urandom(32)
        combined_keys = aes_key + hmac_key
        
        enc_keys = bob_pub_key.encrypt(
            combined_keys,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        base_iv = os.urandom(16)
        header = b'\x04' + struct.pack(">I", len(enc_keys)) + enc_keys + base_iv
        
    else:
        raise ValueError("Metode enkripsi tidak valid.")
        
    with open(input_path, "rb") as fin, open(output_path, "wb") as fout:
        fout.write(header)
        
        chunk_idx = 0
        bytes_read = 0
        
        if file_size == 0:
            if method in (1, 3):
                aesgcm = AESGCM(session_key)
                nonce = base_nonce[:8] + struct.pack(">I", 0)
                ad = struct.pack(">QI", 0, 1)
                fout.write(aesgcm.encrypt(nonce, b"", ad))
            elif method == 2:
                chacha = ChaCha20Poly1305(session_key)
                nonce = base_nonce[:8] + struct.pack(">I", 0)
                fout.write(chacha.encrypt(nonce, b"", None))
            elif method == 4:
                padder = sym_padding.PKCS7(128).padder()
                padded_data = padder.update(b"") + padder.finalize()
                iv = base_iv[:12] + struct.pack(">I", 0)
                cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
                encryptor = cipher.encryptor()
                ct = encryptor.update(padded_data) + encryptor.finalize()
                
                h = hmac.HMAC(hmac_key, hashes.SHA256())
                h.update(iv + ct + struct.pack(">QI", 0, 1))
                hmac_tag = h.finalize()
                
                fout.write(struct.pack(">I", len(ct)) + iv + hmac_tag + ct)
            return
            
        while bytes_read < file_size:
            chunk = fin.read(chunk_size)
            if not chunk:
                break
                
            bytes_read += len(chunk)
            is_last = 1 if bytes_read >= file_size else 0
            
            if method in (1, 3):
                aesgcm = AESGCM(session_key)
                nonce = base_nonce[:8] + struct.pack(">I", chunk_idx)
                ad = struct.pack(">QI", chunk_idx, is_last)
                enc_chunk = aesgcm.encrypt(nonce, chunk, ad)
                tag = enc_chunk[-16:]
                ct = enc_chunk[:-16]
                fout.write(tag + ct)
                
            elif method == 2:
                chacha = ChaCha20Poly1305(session_key)
                nonce = base_nonce[:8] + struct.pack(">I", chunk_idx)
                enc_chunk = chacha.encrypt(nonce, chunk, None)
                tag = enc_chunk[-16:]
                ct = enc_chunk[:-16]
                fout.write(tag + ct)
                
            elif method == 4:
                padder = sym_padding.PKCS7(128).padder()
                padded_data = padder.update(chunk) + padder.finalize()
                
                iv = base_iv[:12] + struct.pack(">I", chunk_idx)
                cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
                encryptor = cipher.encryptor()
                ct = encryptor.update(padded_data) + encryptor.finalize()
                
                h = hmac.HMAC(hmac_key, hashes.SHA256())
                h.update(iv + ct + struct.pack(">QI", chunk_idx, is_last))
                hmac_tag = h.finalize()
                
                fout.write(struct.pack(">I", len(ct)) + iv + hmac_tag + ct)
                
            chunk_idx += 1


def decrypt_file(encrypted_path, output_path, bob_priv_key, chunk_size=65536):
    """Mendekripsi file terenkripsi secara otomatis mendeteksi metodenya."""
    try:
        with open(encrypted_path, "rb") as fin:
            first_byte = fin.read(1)
            if not first_byte:
                raise ValueError("File kosong.")
                
            method = first_byte[0]
            
            if method not in (1, 2, 3, 4):
                method = 1
                fin.seek(0)
                is_legacy = True
            else:
                is_legacy = False
                
            if method in (1, 2):
                if not isinstance(bob_priv_key, x25519.X25519PrivateKey):
                    raise ValueError("Metode membutuhkan Kunci Privat X25519.")
                    
                ephemeral_pub_bytes = fin.read(32)
                base_nonce = fin.read(12)
                    
                if len(ephemeral_pub_bytes) < 32 or len(base_nonce) < 12:
                    raise ValueError("Header file terenkripsi tidak lengkap.")
                    
                ephemeral_pub = x25519.X25519PublicKey.from_public_bytes(ephemeral_pub_bytes)
                shared_secret = bob_priv_key.exchange(ephemeral_pub)
                session_key = HKDF(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=None,
                    info=b"e2ee-file-session"
                ).derive(shared_secret)
                
            elif method == 3:
                if not isinstance(bob_priv_key, rsa.RSAPrivateKey):
                    raise ValueError("Metode membutuhkan Kunci Privat RSA.")
                    
                len_bytes = fin.read(4)
                if len(len_bytes) < 4:
                    raise ValueError("Header file terenkripsi tidak lengkap.")
                enc_session_key_len = struct.unpack(">I", len_bytes)[0]
                
                enc_session_key = fin.read(enc_session_key_len)
                base_nonce = fin.read(12)
                if len(enc_session_key) < enc_session_key_len or len(base_nonce) < 12:
                    raise ValueError("Header file terenkripsi tidak lengkap.")
                    
                session_key = bob_priv_key.decrypt(
                    enc_session_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                
            elif method == 4:
                if not isinstance(bob_priv_key, rsa.RSAPrivateKey):
                    raise ValueError("Metode membutuhkan Kunci Privat RSA.")
                    
                len_bytes = fin.read(4)
                if len(len_bytes) < 4:
                    raise ValueError("Header file terenkripsi tidak lengkap.")
                enc_keys_len = struct.unpack(">I", len_bytes)[0]
                
                enc_keys = fin.read(enc_keys_len)
                base_iv = fin.read(16)
                if len(enc_keys) < enc_keys_len or len(base_iv) < 16:
                    raise ValueError("Header file terenkripsi tidak lengkap.")
                    
                combined_keys = bob_priv_key.decrypt(
                    enc_keys,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                aes_key = combined_keys[:32]
                hmac_key = combined_keys[32:]
                
            with open(output_path, "wb") as fout:
                chunk_idx = 0
                
                if method in (1, 2, 3):
                    read_size = chunk_size + 16
                    curr_chunk = fin.read(read_size)
                    
                    while curr_chunk:
                        next_chunk = fin.read(read_size)
                        is_last = 1 if not next_chunk else 0
                        
                        if len(curr_chunk) < 16:
                            raise ValueError("Data chunk rusak atau terlalu pendek.")
                            
                        tag = curr_chunk[:16]
                        ct = curr_chunk[16:]
                        
                        nonce = base_nonce[:8] + struct.pack(">I", chunk_idx)
                        
                        if method in (1, 3):
                            aesgcm = AESGCM(session_key)
                            ad = struct.pack(">QI", chunk_idx, is_last)
                            plaintext = aesgcm.decrypt(nonce, ct + tag, ad)
                        elif method == 2:
                            chacha = ChaCha20Poly1305(session_key)
                            plaintext = chacha.decrypt(nonce, ct + tag, None)
                            
                        fout.write(plaintext)
                        curr_chunk = next_chunk
                        chunk_idx += 1
                        
                elif method == 4:
                    len_bytes = fin.read(4)
                    while len_bytes:
                        if len(len_bytes) < 4:
                            raise ValueError("Data chunk rusak atau tidak lengkap.")
                        ct_len = struct.unpack(">I", len_bytes)[0]
                        
                        iv = fin.read(16)
                        hmac_tag = fin.read(32)
                        ct = fin.read(ct_len)
                        
                        if len(iv) < 16 or len(hmac_tag) < 32 or len(ct) < ct_len:
                            raise ValueError("Data chunk terpotong.")
                            
                        next_len_bytes = fin.read(4)
                        is_last = 1 if not next_len_bytes else 0
                        
                        # Verifikasi HMAC
                        h = hmac.HMAC(hmac_key, hashes.SHA256())
                        h.update(iv + ct + struct.pack(">QI", chunk_idx, is_last))
                        h.verify(hmac_tag)
                        
                        # Dekripsi CBC
                        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
                        decryptor = cipher.decryptor()
                        padded_data = decryptor.update(ct) + decryptor.finalize()
                        
                        unpadder = sym_padding.PKCS7(128).unpadder()
                        plaintext = unpadder.update(padded_data) + unpadder.finalize()
                        
                        fout.write(plaintext)
                        len_bytes = next_len_bytes
                        chunk_idx += 1
                        
    except Exception as e:
        if os.path.exists(output_path):
            os.remove(output_path)
        raise e
