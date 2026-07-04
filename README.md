# E2EE Cryptography Tool (X25519 / RSA + AES / ChaCha20)

Aplikasi desktop berbasis Python (Tkinter) untuk melakukan enkripsi dan dekripsi pesan teks serta berkas (file) secara aman menggunakan skema hibrida kriptografi modern dengan dukungan **multi-algoritma** dan **deteksi otomatis**.

---

## 🚀 Fitur Utama

1. **Pembuatan Pasangan Kunci (Key Generation)**:
   * Menghasilkan pasangan kunci Elliptic Curve **X25519** atau **RSA (2048-bit)** dalam format berkas PEM.
2. **Pilihan Metode Enkripsi (Multi-Algoritma)**:
   * **Method 1: X25519 + AES-256-GCM** (Default, Elliptic Curve + AES terotentikasi)
   * **Method 2: X25519 + ChaCha20-Poly1305** (Elliptic Curve + Stream cipher modern)
   * **Method 3: RSA + AES-256-GCM** (Klasik industri, RSA Key Wrap + AES terotentikasi)
   * **Method 4: RSA + AES-256-CBC (dengan HMAC-SHA256)** (Klasik industri, RSA Key Wrap + AES CBC + Verifikasi HMAC)
3. **Deteksi Otomatis Saat Dekripsi**:
   * Sistem secara otomatis mendeteksi metode enkripsi yang digunakan (melalui *header* paket terenkripsi) dan mencocokkan tipe kunci privat yang dibutuhkan. Pengguna tidak perlu mengingat metode yang tepat untuk melakukan dekripsi.
4. **Enkripsi & Dekripsi Berkas (File) Berukuran Besar**:
   * Mendukung enkripsi bertahap (*chunk-by-chunk* 64 KB) untuk meminimalisasi konsumsi memori RAM.
5. **Verifikasi Integritas Otomatis**:
   * Melindungi file dari modifikasi tidak sah selama pengiriman dengan pemeriksaan hash **SHA-256** secara *constant-time* (GCM) atau verifikasi **HMAC-SHA256** (pada CBC).

---

## 🛠️ Arsitektur Kriptografi

Aplikasi ini menerapkan standar keamanan modern:

*   **ECC (Elliptic Curve Cryptography) - X25519**: Kurva eliptik berkinerja tinggi untuk pertukaran kunci sesi yang dinamis.
*   **RSA-2048**: Standar kriptografi kunci publik klasik industri untuk enkripsi kunci sesi.
*   **AES-256-GCM & ChaCha20-Poly1305**: Dua algoritma AEAD (Authenticated Encryption with Associated Data) terbaik untuk enkripsi payload dengan jaminan integritas.
*   **AES-256-CBC + HMAC-SHA256**: Skema klasik yang kokoh menggunakan pendekatan *Encrypt-then-MAC* untuk keamanan optimal pada mode CBC.

---

## 🔍 Penjelasan & Perbedaan 4 Metode Enkripsi

Aplikasi ini menyediakan 4 metode enkripsi hibrida. Enkripsi hibrida menggabungkan kekuatan **Asymmetric Encryption** (lambat, untuk bertukar kunci secara aman) dan **Symmetric Encryption** (sangat cepat, untuk mengenkripsi pesan/file besar).

### 1. Method 1: X25519 + AES-256-GCM
*   **Cara Kerja**:
    1. Pengirim membuat kunci X25519 sementara (*ephemeral key*).
    2. Kunci privat sementara tersebut dipadukan dengan kunci publik X25519 penerima menggunakan algoritma pertukaran kunci Diffie-Hellman untuk mendapatkan *shared secret*.
    3. *Shared secret* diturunkan menjadi kunci sesi simetris 256-bit menggunakan fungsi HKDF-SHA256.
    4. Pesan/file dienkripsi dengan **AES-256-GCM** yang menghasilkan ciphertext dan tag otentikasi.
    5. Hasil enkripsi dibungkus menjadi: `[Method Byte 0x01] + [Ephemeral Pub Key (32B)] + [Nonce (12B)] + [Tag (16B)] + [Ciphertext]`.
*   **Karakteristik**:
    *   **Sangat Cepat & Efisien**: Algoritma kurva eliptik X25519 jauh lebih hemat daya dibanding RSA tradisional.
    *   **Forward Secrecy**: Kunci sesi dibuat baru dan dinamis di setiap proses enkripsi.
    *   **AEAD (Authenticated Encryption)**: Menjamin kerahasiaan sekaligus integritas pesan (mencegah modifikasi data).

### 2. Method 2: X25519 + ChaCha20-Poly1305
*   **Cara Kerja**:
    *   Sama seperti Metode 1 dalam pertukaran kunci asimetris X25519.
    *   Perbedaannya terletak pada enkripsi simetrisnya yang menggunakan **ChaCha20-Poly1305** alih-alih AES-GCM.
    *   Paket dibungkus dengan byte penanda metode `0x02`.
*   **Karakteristik**:
    *   **Stream Cipher Modern**: ChaCha20 adalah cipher berbasis bit stream, bukan block cipher seperti AES.
    *   **Optimal untuk Mobile/IoT**: Sangat efisien pada prosesor yang tidak memiliki instruksi akselerasi perangkat keras khusus AES (seperti perangkat mobile tua atau komputer papan tunggal).

### 3. Method 3: RSA + AES-256-GCM
*   **Cara Kerja**:
    1. Pengirim menghasilkan kunci simetris 256-bit acak (*session key*) langsung dari sistem OS.
    2. Kunci sesi tersebut dienkripsi (*key wrap*) menggunakan kunci publik **RSA-2048** penerima dengan padding aman **OAEP (SHA-256)**.
    3. Pesan/file dienkripsi menggunakan **AES-256-GCM** dengan kunci sesi tersebut.
    4. Paket dibungkus menjadi: `[Method Byte 0x03] + [Length (4B)] + [Encrypted Session Key] + [Nonce (12B)] + [Tag (16B)] + [Ciphertext]`.
*   **Karakteristik**:
    *   **Klasik & Kompatibel**: Kombinasi RSA adalah standar industri lama yang paling didukung luas di berbagai sistem komputer tradisional.
    *   **Ukuran Data & Kunci Lebih Besar**: Kunci RSA (2048-bit) memakan ruang memori lebih besar dibanding ECC (256-bit).

### 4. Method 4: RSA + AES-256-CBC (dengan HMAC-SHA256)
*   **Cara Kerja**:
    1. Pengirim membuat dua kunci simetris acak: Kunci AES (32-byte) dan Kunci HMAC (32-byte).
    2. Kedua kunci ini dienkripsi bersamaan menggunakan kunci publik **RSA-2048** penerima.
    3. Pesan/file dienkripsi menggunakan **AES-256-CBC** dengan IV acak 16-byte dan padding PKCS7.
    4. Untuk menjamin keutuhan data (karena CBC tidak mendukung autentikasi bawaan), pengirim menghitung kode otentikasi **HMAC-SHA256** atas seluruh ciphertext beserta IV-nya (*Encrypt-then-MAC*).
    5. Paket dibungkus menjadi: `[Method Byte 0x04] + [Length (4B)] + [Encrypted Keys] + [IV (16B)] + [HMAC Tag (32B)] + [Ciphertext]`.
*   **Karakteristik**:
    *   **Menerapkan Encrypt-then-MAC**: Metode ini merupakan standar keamanan tertinggi untuk algoritma non-AEAD guna mencegah serangan *padding oracle*.
    *   **Lebih Lambat**: Membutuhkan proses komputasi ganda karena enkripsi dan otentikasi (HMAC) dihitung secara terpisah.

---

### Perbandingan Ringkas 4 Metode

| Fitur / Parameter | Method 1 (X25519+AES-GCM) | Method 2 (X25519+ChaCha20) | Method 3 (RSA+AES-GCM) | Method 4 (RSA+AES-CBC) |
| :--- | :--- | :--- | :--- | :--- |
| **Tipe Kunci Asimetris** | ECC (X25519 - 256-bit) | ECC (X25519 - 256-bit) | RSA (2048-bit) | RSA (2048-bit) |
| **Cipher Simetris** | AES-256-GCM | ChaCha20-Poly1305 | AES-256-GCM | AES-256-CBC |
| **Metode Autentikasi** | Bawaan (AEAD) | Bawaan (AEAD) | Bawaan (AEAD) | HMAC-SHA256 (EtM) |
| **Forward Secrecy** | Ya (Menggunakan Ephemeral) | Ya (Menggunakan Ephemeral) | Tidak secara langsung | Tidak secara langsung |
| **Kelebihan Utama** | Sangat cepat & modern | Sangat optimal tanpa hardware AES | Standar industri mapan | Keamanan CBC + MAC klasik |

---

## 📂 Struktur Proyek

```text
enkripsi-dekripsi-keamanan-siber/
│
├── main.py              # Titik masuk aplikasi (entrypoint), penangan dependensi, dan inisialisasi GUI
├── README.md            # Dokumentasi proyek
└── src/                 # Folder sumber kode program
    ├── __init__.py      # Menandai src sebagai Python package
    ├── crypto.py        # Logika inti kriptografi (X25519, RSA, AES-GCM, ChaCha20, CBC, HMAC)
    ├── utils.py         # Logika utilitas (hashing SHA-256, verifikasi integritas)
    └── gui.py           # Desain antarmuka pengguna grafis (GUI Tkinter)
```

---

## 📋 Persyaratan Sistem

*   **Python 3.8** atau versi yang lebih baru.
*   **Tkinter** (biasanya sudah terinstal secara bawaan bersama Python).
*   Library **cryptography** (akan terinstal otomatis jika belum ada).

---

## 🏁 Cara Menjalankan Aplikasi

Buka terminal di direktori proyek ini dan jalankan perintah:

```powershell
# Menggunakan Python Launcher (Windows)
py main.py

# Atau menggunakan perintah Python standar
python main.py
```

---

## 📖 Cara Penggunaan

### 1. Membuat Kunci
*   Klik **"1. Hasilkan Pasangan Kunci Baru (Keys)"**.
*   Pilih jenis kunci: **X25519** atau **RSA-2048**.
*   Pilih folder penyimpanan. Sistem akan menghasilkan berkas `private_key.pem` dan `public_key.pem`.

### 2. Enkripsi & Dekripsi Pesan
*   **Enkripsi**: Masukkan pesan teks, pilih metode enkripsi dari dropdown list (Metode 1-4), klik tombol enkripsi, lalu pilih berkas kunci publik penerima yang sesuai (X25519 untuk Metode 1-2, RSA untuk Metode 3-4). Salin ciphertext Base64 yang dihasilkan.
*   **Dekripsi**: Masukkan ciphertext Base64, linter aplikasi akan langsung menampilkan **"Metode Terdeteksi"**. Klik tombol dekripsi, dan pilih berkas kunci privat Anda untuk membaca pesan asli.

### 3. Enkripsi & Dekripsi Berkas (File)
*   **Enkripsi File**: Klik tombol enkripsi berkas, pilih berkas asal, metode enkripsi, serta kunci publik penerima yang sesuai. Simpan hasil dengan ekstensi `.enc`.
*   **Dekripsi File**: Klik tombol dekripsi berkas, pilih berkas `.enc`. Aplikasi akan langsung mendeteksi metode enkripsi yang digunakan. Pilih kunci privat Anda yang sesuai untuk mengembalikan file ke format semula.
