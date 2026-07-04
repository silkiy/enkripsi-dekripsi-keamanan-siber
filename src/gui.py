import os
import base64
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

# Impor modul internal
from src.crypto import (
    generate_key,
    load_private_key,
    load_public_key,
    encrypt_message,
    decrypt_message,
    encrypt_file,
    decrypt_file
)
from src.utils import calculate_hash


class E2EEApp:
    def __init__(self, root, mode="all"):
        self.root = root
        self.mode = mode
        
        if mode == "encrypt":
            self.root.title("E2EE Encryptor Tool (X25519 / RSA)")
            self.root.geometry("520x300")
        elif mode == "decrypt":
            self.root.title("E2EE Decryptor Tool (X25519 / RSA)")
            self.root.geometry("520x300")
        else:
            self.root.title("E2EE Cryptography Tool (X25519 / RSA)")
            self.root.geometry("520x420")
            
        self.root.resizable(False, False)
        
        # Style layout
        self.root.configure(bg="#f4f6f9")
        
        title_label = tk.Label(
            root, 
            text="Aplikasi End-to-End Encryption" if mode == "all" else ("E2EE Encryptor Tool" if mode == "encrypt" else "E2EE Decryptor Tool"), 
            font=("Arial", 16, "bold"), 
            bg="#f4f6f9", 
            fg="#2c3e50"
        )
        title_label.pack(pady=15)
        
        subtitle_label = tk.Label(
            root, 
            text="Multi-Metode: X25519 & RSA dengan AES-GCM / ChaCha20 / AES-CBC" if mode == "all" else 
            ("Enkripsi Pesan & Berkas menggunakan Kunci Publik Penerima" if mode == "encrypt" else 
             "Dekripsi Pesan & Berkas menggunakan Kunci Privat Anda"),
            font=("Arial", 9, "italic"), 
            bg="#f4f6f9", 
            fg="#7f8c8d"
        )
        subtitle_label.pack(pady=2)

        # Frame Tombol Utama
        btn_frame = tk.Frame(root, bg="#f4f6f9")
        btn_frame.pack(pady=10)
        
        buttons_info = []
        
        # 1. Kunci Manajemen (Selalu ada)
        buttons_info.append({
            "text": "1. Hasilkan Pasangan Kunci Baru (Keys)",
            "bg": "#3498db",
            "active": "#2980b9",
            "cmd": self.gui_generate_keys
        })
        
        if mode in ("all", "encrypt"):
            buttons_info.append({
                "text": "2. Enkripsi Pesan Teks (Encrypt Message)",
                "bg": "#2ecc71",
                "active": "#27ae60",
                "cmd": self.gui_encrypt_message
            })
            
        if mode in ("all", "decrypt"):
            num = "2" if mode == "decrypt" else "3"
            buttons_info.append({
                "text": f"{num}. Dekripsi Pesan Teks (Decrypt Message)",
                "bg": "#e67e22",
                "active": "#d35400",
                "cmd": self.gui_decrypt_message
            })
            
        if mode in ("all", "encrypt"):
            num = "3" if mode == "encrypt" else "4"
            buttons_info.append({
                "text": f"{num}. Enkripsi Berkas / File (Encrypt File)",
                "bg": "#9b59b6",
                "active": "#8e44ad",
                "cmd": self.gui_encrypt_file
            })
            
        if mode in ("all", "decrypt"):
            num = "3" if mode == "decrypt" else "5"
            buttons_info.append({
                "text": f"{num}. Dekripsi Berkas / File (Decrypt File)",
                "bg": "#34495e",
                "active": "#2c3e50",
                "cmd": self.gui_decrypt_file
            })
            
        for idx, btn_data in enumerate(buttons_info):
            btn = tk.Button(
                btn_frame, 
                text=btn_data["text"], 
                width=45, 
                height=2, 
                font=("Arial", 10),
                bg=btn_data["bg"], 
                fg="white", 
                activebackground=btn_data["active"],
                command=btn_data["cmd"]
            )
            btn.grid(row=idx, column=0, pady=8)

    def gui_generate_keys(self):
        # Window pop-up pilihan tipe kunci
        top = tk.Toplevel(self.root)
        top.title("Hasilkan Pasangan Kunci")
        top.geometry("380x180")
        top.resizable(False, False)
        top.configure(bg="#f4f6f9")
        
        tk.Label(top, text="Pilih Jenis Kunci:", font=("Arial", 10, "bold"), bg="#f4f6f9").pack(anchor="w", padx=20, pady=10)
        
        key_type_var = tk.StringVar(value="X25519")
        combo = ttk.Combobox(top, textvariable=key_type_var, values=["X25519", "RSA-2048"], state="readonly", font=("Arial", 10))
        combo.pack(fill="x", padx=20, pady=5)
        
        def do_generate():
            k_type = key_type_var.get()
            folder = filedialog.askdirectory(title="Pilih Folder untuk Menyimpan Kunci")
            if folder:
                try:
                    generate_key(folder, key_type=k_type)
                    messagebox.showinfo(
                        "Sukses", 
                        f"Kunci publik dan privat ({k_type}) berhasil dibuat di:\n{folder}\n\n"
                        "File:\n- private_key.pem (Rahasia!)\n- public_key.pem (Bagi ke Pengirim)"
                    )
                    top.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Gagal membuat kunci: {e}")
                    
        btn = tk.Button(top, text="Tentukan Folder & Buat Kunci", bg="#3498db", fg="white", font=("Arial", 10), command=do_generate)
        btn.pack(pady=20)

    def gui_encrypt_message(self):
        # Window pop-up input
        top = tk.Toplevel(self.root)
        top.title("Enkripsi Pesan")
        top.geometry("450x450")
        top.resizable(False, False)
        top.configure(bg="#f4f6f9")
        
        tk.Label(top, text="Masukkan Pesan:", font=("Arial", 10, "bold"), bg="#f4f6f9").pack(anchor="w", padx=15, pady=8)
        txt_input = scrolledtext.ScrolledText(top, height=5, width=50)
        txt_input.pack(padx=15)
        
        tk.Label(top, text="Pilih Metode Enkripsi:", font=("Arial", 10, "bold"), bg="#f4f6f9").pack(anchor="w", padx=15, pady=8)
        method_var = tk.StringVar(value="Method 1: X25519 + AES-256-GCM")
        methods_list = [
            "Method 1: X25519 + AES-256-GCM",
            "Method 2: X25519 + ChaCha20-Poly1305",
            "Method 3: RSA + AES-256-GCM",
            "Method 4: RSA + AES-256-CBC"
        ]
        combo = ttk.Combobox(top, textvariable=method_var, values=methods_list, state="readonly", font=("Arial", 9))
        combo.pack(fill="x", padx=15)
        
        def do_encrypt():
            msg = txt_input.get("1.0", tk.END).strip()
            if not msg:
                messagebox.showwarning("Peringatan", "Pesan tidak boleh kosong!")
                return
                
            selected = method_var.get()
            method_idx = int(selected.split(":")[0].split(" ")[1])
            
            key_path = filedialog.askopenfilename(
                title="Pilih Kunci Publik Penerima (.pem)", 
                filetypes=[("PEM Files", "*.pem")]
            )
            if key_path:
                try:
                    pub_key = load_public_key(key_path)
                    cipher_b64 = encrypt_message(msg, pub_key, method=method_idx)
                    
                    # Tampilkan hasil
                    lbl_res.config(text="Hasil Teks Terenkripsi (Base64):")
                    txt_output.delete("1.0", tk.END)
                    txt_output.insert(tk.END, cipher_b64)
                except Exception as e:
                    messagebox.showerror("Error", f"Enkripsi gagal: {e}")
                    
        btn_enc = tk.Button(top, text="Pilih Kunci Publik & Enkripsi", bg="#2ecc71", fg="white", font=("Arial", 10), command=do_encrypt)
        btn_enc.pack(pady=15)
        
        lbl_res = tk.Label(top, text="", font=("Arial", 10, "bold"), bg="#f4f6f9")
        lbl_res.pack(anchor="w", padx=15, pady=2)
        txt_output = scrolledtext.ScrolledText(top, height=6, width=50)
        txt_output.pack(padx=15)

    def gui_decrypt_message(self):
        # Window pop-up input
        top = tk.Toplevel(self.root)
        top.title("Dekripsi Pesan")
        top.geometry("450x420")
        top.resizable(False, False)
        top.configure(bg="#f4f6f9")
        
        tk.Label(top, text="Masukkan Teks Terenkripsi (Base64):", font=("Arial", 10, "bold"), bg="#f4f6f9").pack(anchor="w", padx=15, pady=8)
        txt_input = scrolledtext.ScrolledText(top, height=5, width=50)
        txt_input.pack(padx=15)
        
        lbl_info = tk.Label(top, text="Metode Terdeteksi: -", font=("Arial", 9, "italic"), bg="#f4f6f9", fg="#e67e22")
        lbl_info.pack(anchor="w", padx=15, pady=5)
        
        def on_text_change(*args):
            cipher_b64 = txt_input.get("1.0", tk.END).strip()
            if not cipher_b64:
                lbl_info.config(text="Metode Terdeteksi: -")
                return
            try:
                # Bersihkan spasi/line break
                cipher_b64_clean = cipher_b64.replace("\n", "").replace(" ", "")
                packet = base64.b64decode(cipher_b64_clean.encode('utf-8'))
                if len(packet) > 0:
                    first_byte = packet[0]
                    if first_byte == 1:
                        detected = "Method 1 (X25519 + AES-256-GCM)"
                    elif first_byte == 2:
                        detected = "Method 2 (X25519 + ChaCha20-Poly1305)"
                    elif first_byte == 3:
                        detected = "Method 3 (RSA + AES-256-GCM)"
                    elif first_byte == 4:
                        detected = "Method 4 (RSA + AES-256-CBC)"
                    else:
                        detected = "Method 1 (Legacy X25519 + AES-GCM)"
                else:
                    detected = "Data kosong"
            except Exception:
                detected = "Bukan Base64 valid / Format salah"
            lbl_info.config(text=f"Metode Terdeteksi: {detected}")
            
        # Hubungkan event pengetikan untuk auto detect
        txt_input.bind("<KeyRelease>", on_text_change)
        
        def do_decrypt():
            cipher_b64 = txt_input.get("1.0", tk.END).strip()
            if not cipher_b64:
                messagebox.showwarning("Peringatan", "Teks terenkripsi tidak boleh kosong!")
                return
                
            key_path = filedialog.askopenfilename(
                title="Pilih Kunci Privat Anda (.pem)", 
                filetypes=[("PEM Files", "*.pem")]
            )
            if key_path:
                try:
                    priv_key = load_private_key(key_path)
                    plain = decrypt_message(cipher_b64, priv_key)
                    
                    # Tampilkan hasil
                    lbl_res.config(text="Hasil Teks Biasa (Plaintext):")
                    txt_output.delete("1.0", tk.END)
                    txt_output.insert(tk.END, plain)
                except Exception as e:
                    messagebox.showerror("Error", f"Dekripsi gagal! Kunci salah atau data rusak.\nDetail: {e}")
                    
        btn_dec = tk.Button(top, text="Pilih Kunci Privat & Dekripsi", bg="#e67e22", fg="white", font=("Arial", 10), command=do_decrypt)
        btn_dec.pack(pady=10)
        
        lbl_res = tk.Label(top, text="", font=("Arial", 10, "bold"), bg="#f4f6f9")
        lbl_res.pack(anchor="w", padx=15, pady=2)
        txt_output = scrolledtext.ScrolledText(top, height=6, width=50)
        txt_output.pack(padx=15)

    def gui_encrypt_file(self):
        top = tk.Toplevel(self.root)
        top.title("Enkripsi File / Berkas")
        top.geometry("460x300")
        top.resizable(False, False)
        top.configure(bg="#f4f6f9")
        
        # File Asli
        file_asli_var = tk.StringVar(value="")
        tk.Label(top, text="Berkas Sumber:", font=("Arial", 9, "bold"), bg="#f4f6f9").grid(row=0, column=0, sticky="w", padx=15, pady=10)
        entry_file = tk.Entry(top, textvariable=file_asli_var, width=32, state="readonly")
        entry_file.grid(row=0, column=1, padx=5, pady=10)
        def select_file():
            path = filedialog.askopenfilename(title="Pilih Berkas Asli")
            if path:
                file_asli_var.set(path)
        btn_file = tk.Button(top, text="Cari...", command=select_file)
        btn_file.grid(row=0, column=2, padx=5, pady=10)
        
        # Metode Enkripsi
        tk.Label(top, text="Metode Enkripsi:", font=("Arial", 9, "bold"), bg="#f4f6f9").grid(row=1, column=0, sticky="w", padx=15, pady=10)
        method_var = tk.StringVar(value="Method 1: X25519 + AES-256-GCM")
        methods_list = [
            "Method 1: X25519 + AES-256-GCM",
            "Method 2: X25519 + ChaCha20-Poly1305",
            "Method 3: RSA + AES-256-GCM",
            "Method 4: RSA + AES-256-CBC"
        ]
        combo = ttk.Combobox(top, textvariable=method_var, values=methods_list, state="readonly", width=30)
        combo.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=10)
        
        # Kunci Publik
        key_path_var = tk.StringVar(value="")
        tk.Label(top, text="Kunci Publik (.pem):", font=("Arial", 9, "bold"), bg="#f4f6f9").grid(row=2, column=0, sticky="w", padx=15, pady=10)
        entry_key = tk.Entry(top, textvariable=key_path_var, width=32, state="readonly")
        entry_key.grid(row=2, column=1, padx=5, pady=10)
        def select_key():
            path = filedialog.askopenfilename(title="Pilih Kunci Publik Penerima (.pem)", filetypes=[("PEM Files", "*.pem")])
            if path:
                key_path_var.set(path)
        btn_key = tk.Button(top, text="Cari...", command=select_key)
        btn_key.grid(row=2, column=2, padx=5, pady=10)
        
        # Tombol Enkripsi
        def do_encrypt_file():
            file_asli = file_asli_var.get()
            key_path = key_path_var.get()
            if not file_asli or not key_path:
                messagebox.showwarning("Peringatan", "Harap lengkapi semua berkas dan kunci publik!")
                return
                
            suggested_name = os.path.basename(file_asli) + ".enc"
            file_enc = filedialog.asksaveasfilename(
                title="Simpan File Terenkripsi Sebagai", 
                initialfile=suggested_name,
                filetypes=[("Encrypted Files", "*.enc")]
            )
            if not file_enc:
                return
                
            selected = method_var.get()
            method_idx = int(selected.split(":")[0].split(" ")[1])
            
            try:
                pub_key = load_public_key(key_path)
                hash_asli = calculate_hash(file_asli)
                
                encrypt_file(file_asli, file_enc, pub_key, method=method_idx)
                
                messagebox.showinfo(
                    "Sukses", 
                    f"File berhasil dienkripsi!\n\n"
                    f"Metode: {selected}\n"
                    f"Tujuan: {file_enc}\n"
                    f"SHA-256 Asli: {hash_asli}"
                )
                top.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Enkripsi berkas gagal: {e}")
                
        btn_action = tk.Button(top, text="Enkripsi Berkas", bg="#9b59b6", fg="white", font=("Arial", 10, "bold"), height=2, command=do_encrypt_file)
        btn_action.grid(row=3, column=0, columnspan=3, pady=20)

    def gui_decrypt_file(self):
        top = tk.Toplevel(self.root)
        top.title("Dekripsi File / Berkas")
        top.geometry("460x300")
        top.resizable(False, False)
        top.configure(bg="#f4f6f9")
        
        # File Terenkripsi
        file_enc_var = tk.StringVar(value="")
        method_info_var = tk.StringVar(value="-")
        
        tk.Label(top, text="Berkas Terenkripsi:", font=("Arial", 9, "bold"), bg="#f4f6f9").grid(row=0, column=0, sticky="w", padx=15, pady=10)
        entry_file = tk.Entry(top, textvariable=file_enc_var, width=32, state="readonly")
        entry_file.grid(row=0, column=1, padx=5, pady=10)
        
        def select_enc_file():
            path = filedialog.askopenfilename(title="Pilih Berkas Terenkripsi", filetypes=[("Encrypted Files", "*.enc")])
            if path:
                file_enc_var.set(path)
                # Auto detect method
                try:
                    with open(path, "rb") as f:
                        first_byte = f.read(1)
                        if first_byte:
                            m = first_byte[0]
                            if m == 1:
                                info = "Method 1 (X25519 + AES-256-GCM)"
                            elif m == 2:
                                info = "Method 2 (X25519 + ChaCha20-Poly1305)"
                            elif m == 3:
                                info = "Method 3 (RSA + AES-256-GCM)"
                            elif m == 4:
                                info = "Method 4 (RSA + AES-256-CBC)"
                            else:
                                info = "Method 1 (Legacy X25519 + AES-GCM)"
                        else:
                            info = "Berkas kosong"
                except Exception:
                    info = "Gagal memproses berkas"
                method_info_var.set(info)
                
        btn_file = tk.Button(top, text="Cari...", command=select_enc_file)
        btn_file.grid(row=0, column=2, padx=5, pady=10)
        
        # Informasi Metode Terdeteksi
        tk.Label(top, text="Metode Terdeteksi:", font=("Arial", 9, "bold"), bg="#f4f6f9").grid(row=1, column=0, sticky="w", padx=15, pady=10)
        lbl_method = tk.Label(top, textvariable=method_info_var, font=("Arial", 9, "italic"), bg="#f4f6f9", fg="#e67e22")
        lbl_method.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=10)
        
        # Kunci Privat
        key_path_var = tk.StringVar(value="")
        tk.Label(top, text="Kunci Privat (.pem):", font=("Arial", 9, "bold"), bg="#f4f6f9").grid(row=2, column=0, sticky="w", padx=15, pady=10)
        entry_key = tk.Entry(top, textvariable=key_path_var, width=32, state="readonly")
        entry_key.grid(row=2, column=1, padx=5, pady=10)
        def select_key():
            path = filedialog.askopenfilename(title="Pilih Kunci Privat Anda (.pem)", filetypes=[("PEM Files", "*.pem")])
            if path:
                key_path_var.set(path)
        btn_key = tk.Button(top, text="Cari...", command=select_key)
        btn_key.grid(row=2, column=2, padx=5, pady=10)
        
        # Tombol Dekripsi
        def do_decrypt_file():
            file_enc = file_enc_var.get()
            key_path = key_path_var.get()
            if not file_enc or not key_path:
                messagebox.showwarning("Peringatan", "Harap lengkapi semua berkas terenkripsi dan kunci privat!")
                return
                
            suggested_name = os.path.basename(file_enc).replace(".enc", "")
            file_dec = filedialog.asksaveasfilename(
                title="Simpan File Terdekripsi Sebagai", 
                initialfile=suggested_name
            )
            if not file_dec:
                return
                
            try:
                priv_key = load_private_key(key_path)
                decrypt_file(file_enc, file_dec, priv_key)
                hash_dec = calculate_hash(file_dec)
                
                messagebox.showinfo(
                    "Sukses", 
                    f"File berhasil didekripsi!\n\n"
                    f"Tujuan: {file_dec}\n"
                    f"SHA-256 Hasil Dekripsi: {hash_dec}"
                )
                top.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Dekripsi berkas gagal! Detail: {e}")
                
        btn_action = tk.Button(top, text="Dekripsi Berkas", bg="#34495e", fg="white", font=("Arial", 10, "bold"), height=2, command=do_decrypt_file)
        btn_action.grid(row=3, column=0, columnspan=3, pady=20)
