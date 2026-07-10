import os
import sys
import subprocess

# Auto-install library cryptography & customtkinter jika belum terpasang (PEP 668 bypass included)
for lib in ("cryptography", "customtkinter"):
    try:
        __import__(lib)
    except ImportError:
        print(f"Modul '{lib}' tidak ditemukan. Menginstal...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
        except Exception:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib, "--break-system-packages"])
            except Exception as e:
                print(f"Gagal memasang library {lib}: {e}")
                sys.exit(1)

import customtkinter as ctk
from src.gui import E2EEApp

if __name__ == "__main__":
    # Cegah peluncuran GUI memblokir pengujian otomatis (headless)
    if os.environ.get("HEADLESS_TEST") == "1":
        print("[INFO] Mode pengujian headless aktif. GUI tidak diluncurkan.")
    else:
        root = ctk.CTk()
        app = E2EEApp(root)
        root.mainloop()
