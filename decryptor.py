import os
import sys
import subprocess

# Auto-install library cryptography jika belum terpasang (PEP 668 bypass included)
try:
    import cryptography
except ImportError:
    print("Modul 'cryptography' tidak ditemukan. Menginstal...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
    except Exception:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography", "--break-system-packages"])
        except Exception as e:
            print(f"Gagal memasang library: {e}")
            sys.exit(1)

import tkinter as tk
from src.gui import E2EEApp

if __name__ == "__main__":
    # Cegah peluncuran GUI memblokir pengujian otomatis (headless)
    if os.environ.get("HEADLESS_TEST") == "1":
        print("[INFO] Mode pengujian headless aktif. GUI tidak diluncurkan.")
    else:
        root = tk.Tk()
        app = E2EEApp(root, mode="decrypt")
        root.mainloop()
