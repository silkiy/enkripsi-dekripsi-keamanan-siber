import os
import base64
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import threading

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

# Inisialisasi konfigurasi dasar CustomTkinter
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

# ==========================================
# DESIGN SYSTEM: KONFIGURASI TEMA TERPUSAT
# ==========================================
class AppTheme:
    # Warna
    BG_PRIMARY = "#f8fafc"          # Slate 50 (Latar belakang utama)
    BG_CARD = "#ffffff"             # White (Latar Panel/Card)
    BORDER_COLOR = "#e2e8f0"        # Slate 200 (Garis batas/Border)
    TEXT_MAIN = "#0f172a"           # Slate 900 (Teks Utama)
    TEXT_MUTED = "#64748b"          # Slate 500 (Teks Redup/Keterangan)
    ACCENT = "#4f46e5"              # Indigo 600 (Aksen Utama)
    ACCENT_HOVER = "#4338ca"        # Indigo 700 (Aksen Hover)
    COLOR_TEAL = "#0d9488"          # Teal 600 (Aksen Sukses/Info)
    COLOR_TEAL_HOVER = "#0f766e"    # Teal 700
    COLOR_EMERALD = "#059669"       # Emerald 600 (Enkripsi)
    COLOR_EMERALD_HOVER = "#047857" # Emerald 700
    COLOR_AMBER = "#d97706"         # Amber 600 (Dekripsi)
    COLOR_AMBER_HOVER = "#b45309"   # Amber 700
    COLOR_RED = "#e11d48"           # Red 600 (Error/Peringatan)
    COLOR_VIOLET = "#7c3aed"        # Violet 600
    COLOR_BLUE = "#2563eb"          # Blue 600
    COLOR_SLATE = "#475569"         # Slate 600
    
    # Grid/Window Dimensions
    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 700
    WINDOW_MIN_WIDTH = 980
    WINDOW_MIN_HEIGHT = 680
    SIDEBAR_WIDTH = 230
    
    # Font Sizes & Families
    FONT_FAMILY = "Segoe UI"
    FONT_CODE_FAMILY = "Consolas"
    
    # Font Configurations
    FONT_XS = ("Segoe UI", 8)
    FONT_XS_BOLD = ("Segoe UI", 8, "bold")
    FONT_SM = ("Segoe UI", 9)
    FONT_SM_BOLD = ("Segoe UI", 9, "bold")
    FONT_MD = ("Segoe UI", 10)
    FONT_MD_BOLD = ("Segoe UI", 10, "bold")
    FONT_LG = ("Segoe UI", 11, "bold")
    FONT_XL = ("Segoe UI", 13, "bold")
    FONT_TITLE = ("Segoe UI", 14, "bold")
    FONT_CODE_SM = ("Consolas", 10)
    FONT_CODE_BOLD = ("Consolas", 10, "bold")
    
    # Padding/Spacing System (Sistem kelipatan 8, plus Tiny 4)
    PAD_NONE = 0
    PAD_TINY = 4
    PAD_XS = 8
    PAD_SM = 16
    PAD_MD = 24
    PAD_LG = 32
    
    # Corner Radius & Inner Widget Padding
    CORNER_RADIUS_SM = 8
    CORNER_RADIUS_MD = 12
    TEXTBOX_PADDING = 10


class E2EEApp:
    def __init__(self, root, mode="all"):
        self.root = root
        self.mode = mode
        self.is_processing = False
        
        # Inisialisasi penampilan CustomTkinter
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")
        
        # Penentuan Judul & Tampilan Awal Berdasarkan Mode
        if mode == "encrypt":
            self.initial_view = "encrypt"
            self.root.title("E2EE Encryptor Tool (X25519 / RSA)")
        elif mode == "decrypt":
            self.initial_view = "decrypt"
            self.root.title("E2EE Decryptor Tool (X25519 / RSA)")
        else:
            self.initial_view = "key_gen"
            self.root.title("E2EE Cryptography Tool (X25519 / RSA)")
            
        # Konfigurasi Geometri dan Resizing Window Utama
        self.root.geometry(f"{AppTheme.WINDOW_WIDTH}x{AppTheme.WINDOW_HEIGHT}")
        self.root.minsize(AppTheme.WINDOW_MIN_WIDTH, AppTheme.WINDOW_MIN_HEIGHT)
        self.root.configure(fg_color=AppTheme.BG_PRIMARY)
        
        # Konfigurasi Kolom & Baris Grid Utama (Menggunakan grid_columnconfigure kompatibel CTk)
        self.root.grid_columnconfigure(0, weight=0) # Sidebar
        self.root.grid_columnconfigure(1, weight=1) # Konten Utama
        self.root.grid_rowconfigure(0, weight=1)
        
        # Kumpulan Widget Read-Only untuk Penanganan State UI
        self.read_only_widgets = set()
        
        # Variabel State Internal
        self.encrypt_subview = "message"
        self.decrypt_subview = "message"
        self.selected_method = tk.IntVar(value=1)
        
        # Pembuatan Struktur Layout
        self.create_layout()
        
        # Inisialisasi status tombol aksi awal (Progressive Disclosure)
        self.update_all_action_buttons_state()

    # ==========================================
    # PENYUSUNAN TAMPILAN GUI UTAMA
    # ==========================================
    def create_layout(self):
        # 1. Panel Sidebar (Kiri)
        self.sidebar_frame = ctk.CTkFrame(self.root, fg_color=AppTheme.BG_PRIMARY, width=AppTheme.SIDEBAR_WIDTH, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        
        # Garis Batas Vertikal Kanan Sidebar
        sidebar_sep = ctk.CTkFrame(self.sidebar_frame, width=1, fg_color=AppTheme.BORDER_COLOR, corner_radius=0)
        sidebar_sep.pack(side="right", fill="y")
        
        # Header Sidebar (Brand Title)
        header_frame = ctk.CTkFrame(self.sidebar_frame, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        header_frame.pack(fill="x", padx=AppTheme.PAD_MD, pady=AppTheme.PAD_LG)
        
        lbl_brand = ctk.CTkLabel(header_frame, text="E2EE CRYPTO", font=AppTheme.FONT_XL, text_color=AppTheme.ACCENT, anchor="w")
        lbl_brand.pack(fill="x")
        
        lbl_subtitle = ctk.CTkLabel(header_frame, text="Hybrid Asymmetric Security", font=AppTheme.FONT_XS_BOLD, text_color=AppTheme.TEXT_MUTED, anchor="w")
        lbl_subtitle.pack(fill="x", pady=(AppTheme.PAD_TINY, AppTheme.PAD_NONE))
        
        # Pembatas Horizontal
        sep_line = ctk.CTkFrame(self.sidebar_frame, height=1, fg_color=AppTheme.BORDER_COLOR, corner_radius=0)
        sep_line.pack(fill="x", padx=AppTheme.PAD_SM)
        
        # Kontainer Menu Navigasi
        self.sidebar_menu_frame = ctk.CTkFrame(self.sidebar_frame, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        self.sidebar_menu_frame.pack(fill="both", expand=True, padx=AppTheme.PAD_SM, pady=AppTheme.PAD_MD)
        
        # Footer Info di Bawah Sidebar
        footer_info = ctk.CTkFrame(self.sidebar_frame, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        footer_info.pack(side="bottom", fill="x", padx=AppTheme.PAD_MD, pady=AppTheme.PAD_SM)
        
        lbl_info = ctk.CTkLabel(
            footer_info,
            text=f"Mode: {self.mode.upper()}\nOS: Windows\nVer: 2.4.0",
            font=AppTheme.FONT_XS,
            text_color=AppTheme.TEXT_MUTED,
            justify="left",
            anchor="w"
        )
        lbl_info.pack(fill="x")
        
        # 2. Panel Konten Utama (Kanan)
        self.content_container = ctk.CTkFrame(self.root, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        self.content_container.grid(row=0, column=1, sticky="nsew")
        
        # Area Spesifik Tempat Setiap Halaman/View Ditampilkan
        self.main_content_area = ctk.CTkFrame(self.content_container, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        self.main_content_area.pack(side="top", fill="both", expand=True)
        
        # Batas Horizontal untuk Status Bar di Bawah Konten
        footer_sep = ctk.CTkFrame(self.content_container, height=1, fg_color=AppTheme.BORDER_COLOR, corner_radius=0)
        footer_sep.pack(side="bottom", fill="x")
        
        self.footer_frame = ctk.CTkFrame(self.content_container, fg_color=AppTheme.BG_PRIMARY, height=40, corner_radius=0)
        self.footer_frame.pack(side="bottom", fill="x")
        
        # Status Badge Frame and Label (Warna kontras, informatif)
        self.status_badge_frame = ctk.CTkFrame(
            self.footer_frame,
            fg_color=AppTheme.COLOR_EMERALD,
            corner_radius=AppTheme.CORNER_RADIUS_SM
        )
        self.status_badge_frame.pack(side="left", padx=AppTheme.PAD_SM, pady=AppTheme.PAD_XS)
        
        self.status_label = ctk.CTkLabel(
            self.status_badge_frame,
            text="STATUS: READY",
            font=AppTheme.FONT_XS_BOLD,
            text_color="#ffffff"
        )
        self.status_label.pack(padx=AppTheme.PAD_XS, pady=4)
        
        # Indeterminate Progress Bar (Ditampilkan saat proses enkripsi/dekripsi/keygen)
        self.progress_bar = ctk.CTkProgressBar(self.footer_frame, orientation="horizontal", width=180, mode="indeterminate")
        self.progress_bar.configure(fg_color=AppTheme.BG_PRIMARY, progress_color=AppTheme.ACCENT)
        
        # Inisialisasi Setiap Frame View
        self.frames = {}
        
        self.frames["key_gen"] = ctk.CTkFrame(self.main_content_area, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        self.init_key_gen_view()
        
        if self.mode in ("all", "encrypt"):
            self.frames["encrypt"] = ctk.CTkFrame(self.main_content_area, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
            self.init_encrypt_view()
            
        if self.mode in ("all", "decrypt"):
            self.frames["decrypt"] = ctk.CTkFrame(self.main_content_area, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
            self.init_decrypt_view()
            
        # Menampilkan View Default Pertama Kali
        self.select_view(self.initial_view)

    # ==========================================
    # WIDGET BUILDER & CONTROLLER COMPONENT
    # ==========================================
    def make_sidebar_button(self, parent, text, command, active=False):
        """Membuat tombol menu navigasi dengan indikator bar vertikal di kirinya."""
        btn_frame = ctk.CTkFrame(parent, fg_color=AppTheme.BG_PRIMARY, height=45, corner_radius=0)
        btn_frame.pack(fill="x", pady=AppTheme.PAD_TINY)
        btn_frame.pack_propagate(False)
        
        # Garis aksen aktif disebelah kiri tombol
        indicator = ctk.CTkFrame(btn_frame, width=4, fg_color=AppTheme.ACCENT if active else AppTheme.BG_PRIMARY, corner_radius=0)
        indicator.pack(side="left", fill="y")
        
        btn = ctk.CTkButton(
            btn_frame,
            text=text,
            command=command,
            fg_color=AppTheme.BG_CARD if active else "transparent",
            text_color=AppTheme.TEXT_MAIN if active else AppTheme.TEXT_MUTED,
            hover_color=AppTheme.BG_CARD,
            font=AppTheme.FONT_MD_BOLD if active else AppTheme.FONT_MD,
            corner_radius=AppTheme.CORNER_RADIUS_SM,
            anchor="w",
            height=40,
            cursor="hand2"
        )
        btn.pack(side="left", fill="both", expand=True, padx=(AppTheme.PAD_TINY, AppTheme.PAD_NONE))

    def select_view(self, view_name):
        """Mengganti view aktif di area konten utama."""
        if self.is_processing:
            messagebox.showwarning("Peringatan", "Harap tunggu hingga proses yang sedang berjalan selesai!")
            return
            
        # Sembunyikan semua frame konten
        for name, frame in self.frames.items():
            frame.pack_forget()
            
        # Tampilkan frame terpilih
        self.frames[view_name].pack(fill="both", expand=True)
        self.current_view = view_name
        
        # Gambar ulang daftar tombol sidebar untuk memperbarui state aktif
        for child in self.sidebar_menu_frame.winfo_children():
            child.destroy()
            
        self.make_sidebar_button(self.sidebar_menu_frame, "Key Generator", lambda: self.select_view("key_gen"), active=(view_name == "key_gen"))
        
        if self.mode in ("all", "encrypt"):
            self.make_sidebar_button(self.sidebar_menu_frame, "Encrypt Panel", lambda: self.select_view("encrypt"), active=(view_name == "encrypt"))
            
        if self.mode in ("all", "decrypt"):
            self.make_sidebar_button(self.sidebar_menu_frame, "Decrypt Panel", lambda: self.select_view("decrypt"), active=(view_name == "decrypt"))

        # Perbarui status tombol aksi sesuai progressive disclosure
        self.update_all_action_buttons_state()

    def make_subview_toggle(self, parent, current_subview, on_toggle):
        """Membuat tombol tab horizontal penukar subview (Pesan teks vs Berkas file)."""
        toggle_frame = ctk.CTkFrame(parent, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        toggle_frame.pack(fill="x", pady=(AppTheme.PAD_NONE, AppTheme.PAD_SM))
        
        # Tombol Pesan Teks
        msg_active = (current_subview == "message")
        msg_btn = ctk.CTkButton(
            toggle_frame,
            text="MESSAGE MODE",
            command=lambda: on_toggle("message"),
            fg_color=AppTheme.ACCENT if msg_active else AppTheme.BG_CARD,
            text_color=AppTheme.TEXT_MAIN,
            hover_color=AppTheme.ACCENT_HOVER if msg_active else AppTheme.BORDER_COLOR,
            font=AppTheme.FONT_SM_BOLD,
            corner_radius=AppTheme.CORNER_RADIUS_SM,
            height=40,
            cursor="hand2"
        )
        msg_btn.pack(side="left", padx=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        # Tombol File / Berkas
        file_active = (current_subview == "file")
        file_btn = ctk.CTkButton(
            toggle_frame,
            text="FILE MODE",
            command=lambda: on_toggle("file"),
            fg_color=AppTheme.ACCENT if file_active else AppTheme.BG_CARD,
            text_color=AppTheme.TEXT_MAIN,
            hover_color=AppTheme.ACCENT_HOVER if file_active else AppTheme.BORDER_COLOR,
            font=AppTheme.FONT_SM_BOLD,
            corner_radius=AppTheme.CORNER_RADIUS_SM,
            height=40,
            cursor="hand2"
        )
        file_btn.pack(side="left")

    def create_custom_button(self, parent, text, command, bg_color=None, hover_bg=None, fg_color=None, font=None, corner_radius=None, height=40, **kwargs):
        """Pabrik pembuatan tombol modern CustomTkinter dengan tinggi minimal 40px untuk kenyamanan klik."""
        # Bersihkan argument padding yang tidak didukung CTkButton
        kwargs.pop("padx", None)
        kwargs.pop("pady", None)
        
        if bg_color is None:
            bg_color = AppTheme.ACCENT
        if hover_bg is None:
            hover_bg = AppTheme.ACCENT_HOVER
        if fg_color is None:
            fg_color = AppTheme.TEXT_MAIN
        if font is None:
            font = AppTheme.FONT_SM_BOLD
        if corner_radius is None:
            corner_radius = AppTheme.CORNER_RADIUS_SM
            
        is_outline = (bg_color == AppTheme.BG_PRIMARY)
        
        if is_outline:
            btn = ctk.CTkButton(
                parent,
                text=text,
                command=command,
                fg_color="transparent",
                border_color=AppTheme.BORDER_COLOR,
                border_width=1,
                text_color=AppTheme.TEXT_MAIN,
                hover_color=AppTheme.BORDER_COLOR,
                font=font,
                corner_radius=corner_radius,
                height=height,
                cursor="hand2",
                **kwargs
            )
        else:
            btn = ctk.CTkButton(
                parent,
                text=text,
                command=command,
                fg_color=bg_color,
                hover_color=hover_bg,
                text_color=fg_color,
                font=font,
                corner_radius=corner_radius,
                height=height,
                cursor="hand2",
                **kwargs
            )
        return btn

    def create_scrolled_text(self, parent, height, read_only=False):
        """Membuat CTkTextbox dengan penyesuaian font, tema gelap, dan internal padding."""
        pixel_height = height * 22 if height < 20 else height
        st = ctk.CTkTextbox(
            parent,
            height=pixel_height,
            fg_color=AppTheme.BG_PRIMARY,
            text_color=AppTheme.TEXT_MAIN,
            border_color=AppTheme.BORDER_COLOR,
            border_width=1,
            corner_radius=AppTheme.CORNER_RADIUS_SM,
            font=AppTheme.FONT_CODE_SM
        )
        try:
            st._textbox.configure(padx=AppTheme.TEXTBOX_PADDING, pady=AppTheme.TEXTBOX_PADDING)
        except Exception:
            pass
            
        if read_only:
            st.configure(state="disabled")
        return st

    def create_entry(self, parent, textvariable=None, state="normal"):
        """Membuat single-line input/entry dengan gaya CustomTkinter."""
        entry = ctk.CTkEntry(
            parent,
            textvariable=textvariable,
            state=state,
            fg_color=AppTheme.BG_PRIMARY,
            text_color=AppTheme.TEXT_MAIN,
            border_color=AppTheme.BORDER_COLOR,
            border_width=1,
            corner_radius=AppTheme.CORNER_RADIUS_SM,
            font=AppTheme.FONT_MD,
            height=40
        )
        return entry

    def set_placeholder(self, text_widget, placeholder_text, is_output=False):
        """Memasang fungsionalitas placeholder teks abu-abu."""
        text_widget.configure(state="normal")
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", placeholder_text)
        text_widget.configure(text_color=AppTheme.TEXT_MUTED)
        if is_output:
            text_widget.configure(state="disabled")
            
        if not is_output:
            def on_focus_in(e):
                content = text_widget.get("1.0", tk.END).strip()
                if content == placeholder_text:
                    text_widget.delete("1.0", tk.END)
                    text_widget.configure(text_color=AppTheme.TEXT_MAIN)
                self.update_all_action_buttons_state()
                    
            def on_focus_out(e):
                content = text_widget.get("1.0", tk.END).strip()
                if not content:
                    text_widget.insert("1.0", placeholder_text)
                    text_widget.configure(text_color=AppTheme.TEXT_MUTED)
                self.update_all_action_buttons_state()
                    
            text_widget.bind("<FocusIn>", on_focus_in)
            text_widget.bind("<FocusOut>", on_focus_out)

    def update_status(self, text, status_type="info"):
        """Memperbarui label status dengan skema warna yang elegan sesuai tipe status."""
        self.status_label.configure(text=text.upper())
        if status_type == "success":
            self.status_badge_frame.configure(fg_color=AppTheme.COLOR_EMERALD)
            self.status_label.configure(text_color="#ffffff")
        elif status_type == "error":
            self.status_badge_frame.configure(fg_color=AppTheme.COLOR_RED)
            self.status_label.configure(text_color="#ffffff")
        elif status_type == "warning" or status_type == "processing":
            self.status_badge_frame.configure(fg_color=AppTheme.COLOR_AMBER)
            self.status_label.configure(text_color=AppTheme.BG_PRIMARY)
        else:
            self.status_badge_frame.configure(fg_color=AppTheme.BORDER_COLOR)
            self.status_label.configure(text_color=AppTheme.TEXT_MAIN)

    def update_all_action_buttons_state(self):
        """Mengatur status (disabled/normal) tombol aksi berdasarkan pemenuhan syarat input (Progressive Disclosure)."""
        if self.is_processing:
            return

        # 1. Enkripsi Pesan
        if hasattr(self, "btn_encrypt_message"):
            msg = self.enc_msg_input.get("1.0", tk.END).strip()
            msg_valid = msg and msg != "Tempel atau ketik pesan di sini..."
            key_valid = bool(self.enc_msg_pubkey_var.get())
            if msg_valid and key_valid:
                self.btn_encrypt_message.configure(state="normal")
            else:
                self.btn_encrypt_message.configure(state="disabled")

        # 2. Enkripsi Berkas
        if hasattr(self, "btn_encrypt_file"):
            file_valid = bool(self.enc_file_path_var.get())
            key_valid = bool(self.enc_file_key_var.get())
            if file_valid and key_valid:
                self.btn_encrypt_file.configure(state="normal")
            else:
                self.btn_encrypt_file.configure(state="disabled")

        # 3. Dekripsi Pesan
        if hasattr(self, "btn_decrypt_message"):
            cipher = self.dec_msg_input.get("1.0", tk.END).strip()
            cipher_valid = cipher and cipher != "Tempel ciphertext Base64 di sini..."
            key_valid = bool(self.dec_msg_privkey_var.get())
            if cipher_valid and key_valid:
                self.btn_decrypt_message.configure(state="normal")
            else:
                self.btn_decrypt_message.configure(state="disabled")

        # 4. Dekripsi Berkas
        if hasattr(self, "btn_decrypt_file"):
            file_valid = bool(self.dec_file_path_var.get())
            key_valid = bool(self.dec_file_key_var.get())
            if file_valid and key_valid:
                self.btn_decrypt_file.configure(state="normal")
            else:
                self.btn_decrypt_file.configure(state="disabled")

    # ==========================================
    # VIEW: KEY GENERATOR (PEMBUAT KUNCI)
    # ==========================================
    def init_key_gen_view(self):
        frame = self.frames["key_gen"]
        
        pad_frame = ctk.CTkFrame(frame, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        pad_frame.pack(fill="both", expand=True, padx=AppTheme.PAD_MD, pady=AppTheme.PAD_MD)
        
        lbl_title = ctk.CTkLabel(pad_frame, text="KEY PAIR GENERATOR", text_color=AppTheme.TEXT_MAIN, font=AppTheme.FONT_TITLE, anchor="w")
        lbl_title.pack(fill="x", pady=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        lbl_desc = ctk.CTkLabel(
            pad_frame,
            text="Hasilkan pasangan kunci publik dan privat untuk enkripsi asimetris hibrida.\n"
                 "Kunci publik dibagikan kepada pengirim, sedangkan kunci privat harus dijaga kerahasiaannya.",
            text_color=AppTheme.TEXT_MUTED,
            font=AppTheme.FONT_MD,
            justify="left",
            anchor="w"
        )
        lbl_desc.pack(fill="x", pady=(AppTheme.PAD_NONE, AppTheme.PAD_MD))
        
        # Card Pilihan Algoritma
        config_card = ctk.CTkFrame(pad_frame, fg_color=AppTheme.BG_CARD, border_color=AppTheme.BORDER_COLOR, border_width=1, corner_radius=AppTheme.CORNER_RADIUS_MD)
        config_card.pack(fill="x", pady=(AppTheme.PAD_NONE, AppTheme.PAD_SM))
        
        lbl_opt_title = ctk.CTkLabel(config_card, text="Pilih Jenis Algoritma Kunci:", font=AppTheme.FONT_LG, text_color=AppTheme.TEXT_MAIN)
        lbl_opt_title.pack(anchor="w", padx=AppTheme.PAD_MD, pady=(AppTheme.PAD_MD, AppTheme.PAD_XS))
        
        radio_frame = ctk.CTkFrame(config_card, fg_color=AppTheme.BG_CARD, corner_radius=0)
        radio_frame.pack(fill="x", padx=AppTheme.PAD_MD)
        
        self.keygen_type_var = tk.StringVar(value="X25519")
        
        rb_x = ctk.CTkRadioButton(
            radio_frame,
            text="X25519 (Kurva Eliptik Modern & Cepat)",
            variable=self.keygen_type_var,
            value="X25519",
            fg_color=AppTheme.ACCENT,
            text_color=AppTheme.TEXT_MAIN,
            hover_color=AppTheme.ACCENT_HOVER,
            font=AppTheme.FONT_MD_BOLD
        )
        rb_x.pack(side="left", padx=(AppTheme.PAD_NONE, AppTheme.PAD_LG))
        
        rb_rsa = ctk.CTkRadioButton(
            radio_frame,
            text="RSA-2048 (Klasik & Kompatibilitas Luas)",
            variable=self.keygen_type_var,
            value="RSA-2048",
            fg_color=AppTheme.ACCENT,
            text_color=AppTheme.TEXT_MAIN,
            hover_color=AppTheme.ACCENT_HOVER,
            font=AppTheme.FONT_MD_BOLD
        )
        rb_rsa.pack(side="left")
        
        lbl_help = ctk.CTkLabel(
            config_card,
            text="• X25519: Ukuran kunci sangat kecil (32-byte), performa super cepat, dan sangat aman.\n"
                 "• RSA-2048: Standar industri lama, kompatibel dengan sistem warisan (legacy). Komputasi lebih berat.",
            text_color=AppTheme.TEXT_MUTED,
            font=AppTheme.FONT_SM,
            justify="left",
            anchor="w"
        )
        lbl_help.pack(anchor="w", padx=AppTheme.PAD_MD, pady=(AppTheme.PAD_SM, AppTheme.PAD_SM))
        
        self.btn_generate_keys = self.create_custom_button(
            config_card,
            text="Tentukan Folder & Buat Pasangan Kunci",
            command=self.do_generate_keys,
            bg_color=AppTheme.ACCENT,
            hover_bg=AppTheme.ACCENT_HOVER,
            corner_radius=AppTheme.CORNER_RADIUS_SM
        )
        self.btn_generate_keys.pack(anchor="w", padx=AppTheme.PAD_MD, pady=(AppTheme.PAD_XS, AppTheme.PAD_MD))
        
        # Card Hasil Pembuatan Kunci (Tampil Dinamis Setelah Sukses)
        self.keygen_result_frame = ctk.CTkFrame(pad_frame, fg_color=AppTheme.BG_CARD, border_color=AppTheme.COLOR_EMERALD, border_width=1, corner_radius=AppTheme.CORNER_RADIUS_MD)
        
        lbl_success = ctk.CTkLabel(self.keygen_result_frame, text="Kunci Berhasil Dibuat", font=AppTheme.FONT_LG, text_color=AppTheme.COLOR_EMERALD)
        lbl_success.pack(anchor="w", padx=AppTheme.PAD_MD, pady=(AppTheme.PAD_MD, AppTheme.PAD_XS))
        
        self.keygen_result_folder = tk.StringVar(value="")
        
        folder_display_frame = ctk.CTkFrame(self.keygen_result_frame, fg_color=AppTheme.BG_CARD, corner_radius=0)
        folder_display_frame.pack(fill="x", padx=AppTheme.PAD_MD, pady=AppTheme.PAD_TINY)
        
        lbl_folder_tag = ctk.CTkLabel(folder_display_frame, text="Folder Penyimpanan:", font=AppTheme.FONT_MD, text_color=AppTheme.TEXT_MUTED)
        lbl_folder_tag.pack(side="left")
        
        lbl_folder_val = ctk.CTkLabel(
            folder_display_frame,
            textvariable=self.keygen_result_folder,
            font=AppTheme.FONT_CODE_SM,
            text_color=AppTheme.TEXT_MAIN,
            fg_color=AppTheme.BG_PRIMARY,
            corner_radius=AppTheme.CORNER_RADIUS_SM
        )
        lbl_folder_val.pack(side="left", fill="x", expand=True, padx=AppTheme.PAD_SM)
        
        btn_open_dir = self.create_custom_button(
            folder_display_frame,
            text="Buka Folder",
            command=lambda: self.open_folder(self.keygen_result_folder.get()),
            bg_color=AppTheme.BG_PRIMARY,
            hover_bg=AppTheme.BORDER_COLOR,
            font=AppTheme.FONT_SM_BOLD
        )
        btn_open_dir.pack(side="left")
        
        lbl_files_info = ctk.CTkLabel(
            self.keygen_result_frame,
            text="• private_key.pem  -> Kunci Privat Anda (Rahasia, simpan baik-baik!)\n"
                 "• public_key.pem   -> Kunci Publik Anda (Bagikan ke pengirim pesan)",
            text_color=AppTheme.TEXT_MAIN,
            font=AppTheme.FONT_SM,
            justify="left",
            anchor="w"
        )
        lbl_files_info.pack(anchor="w", padx=AppTheme.PAD_MD, pady=(AppTheme.PAD_XS, AppTheme.PAD_MD))

    def do_generate_keys(self):
        """Memicu pembuatan kunci di background thread."""
        k_type = self.keygen_type_var.get()
        folder = filedialog.askdirectory(title="Pilih Folder untuk Menyimpan Kunci")
        if not folder:
            return
            
        def task():
            generate_key(folder, key_type=k_type)
            return folder
            
        def on_success(res):
            self.keygen_result_folder.set(res)
            self.keygen_result_frame.pack(fill="x", pady=AppTheme.PAD_SM)
            messagebox.showinfo(
                "Sukses", 
                f"Kunci publik dan privat ({k_type}) berhasil dibuat di:\n{res}\n\n"
                "File:\n- private_key.pem (Rahasia!)\n- public_key.pem (Bagi ke Pengirim)"
            )
            self.update_status("Kunci berhasil dibuat", "success")
            
        def on_error(err):
            messagebox.showerror("Error", f"Gagal membuat kunci: {err}")
            self.update_status("Pembuatan kunci gagal", "error")
            
        self.run_task_in_background(
            task, on_success, on_error, "Membuat Pasangan Kunci...",
            self.btn_generate_keys, "Membuat Kunci..."
        )

    # ==========================================
    # VIEW: ENCRYPT PANEL (ENKRIPSI)
    # ==========================================
    def init_encrypt_view(self):
        frame = self.frames["encrypt"]
        
        pad_frame = ctk.CTkFrame(frame, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        pad_frame.pack(fill="both", expand=True, padx=AppTheme.PAD_MD, pady=AppTheme.PAD_MD)
        
        lbl_title = ctk.CTkLabel(pad_frame, text="ENCRYPT PANEL", text_color=AppTheme.TEXT_MAIN, font=AppTheme.FONT_TITLE, anchor="w")
        lbl_title.pack(fill="x", pady=(AppTheme.PAD_NONE, AppTheme.PAD_SM))
        
        self.make_subview_toggle(pad_frame, self.encrypt_subview, self.toggle_encrypt_subview)
        
        self.encrypt_content_area = ctk.CTkFrame(pad_frame, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        self.encrypt_content_area.pack(fill="both", expand=True)
        
        # Stacked Frames: Inisialisasi frame message dan file satu kali
        self.enc_msg_frame = ctk.CTkFrame(self.encrypt_content_area, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        self.enc_file_frame = ctk.CTkFrame(self.encrypt_content_area, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        
        self.render_encrypt_message_view(self.enc_msg_frame)
        self.render_encrypt_file_view(self.enc_file_frame)
        
        self.render_encrypt_content()

    def render_encrypt_message_view(self, parent):
        """Membuat visualisasi komplit enkripsi pesan teks dengan pembagian rasio responsif 60:40."""
        parent.grid_columnconfigure(0, weight=3)
        parent.grid_columnconfigure(1, weight=2)
        parent.grid_rowconfigure(0, weight=1)
        
        left_col = ctk.CTkFrame(parent, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(AppTheme.PAD_NONE, AppTheme.PAD_SM))
        
        right_col = ctk.CTkFrame(parent, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(AppTheme.PAD_SM, AppTheme.PAD_NONE))
        
        # KIRI: Teks Input dan Output
        # 1. Input Teks Asli
        msg_card = ctk.CTkFrame(left_col, fg_color=AppTheme.BG_CARD, border_color=AppTheme.BORDER_COLOR, border_width=1, corner_radius=AppTheme.CORNER_RADIUS_MD)
        msg_card.pack(fill="both", expand=True, pady=(AppTheme.PAD_NONE, AppTheme.PAD_SM))
        
        lbl_plain_tag = ctk.CTkLabel(msg_card, text="Pesan Teks (Plaintext):", font=AppTheme.FONT_MD_BOLD, text_color=AppTheme.TEXT_MAIN)
        lbl_plain_tag.pack(anchor="w", padx=AppTheme.PAD_SM, pady=(AppTheme.PAD_SM, AppTheme.PAD_XS))
        
        self.enc_msg_input = self.create_scrolled_text(msg_card, height=5)
        self.enc_msg_input.pack(fill="both", expand=True, padx=AppTheme.PAD_SM)
        self.enc_msg_input.bind("<KeyRelease>", self.on_encrypt_text_change)
        self.set_placeholder(self.enc_msg_input, "Tempel atau ketik pesan di sini...")
        
        btn_row_input = ctk.CTkFrame(msg_card, fg_color=AppTheme.BG_CARD, corner_radius=0)
        btn_row_input.pack(fill="x", padx=AppTheme.PAD_SM, pady=(AppTheme.PAD_TINY, AppTheme.PAD_SM))
        
        btn_import = self.create_custom_button(
            btn_row_input,
            text="Buka File TXT",
            command=lambda: self.import_txt_file(self.enc_msg_input, self.on_encrypt_text_change),
            bg_color=AppTheme.BG_PRIMARY,
            hover_bg=AppTheme.BORDER_COLOR,
            font=AppTheme.FONT_SM_BOLD,
            height=32
        )
        btn_import.pack(side="left")
        
        self.enc_char_count_lbl = ctk.CTkLabel(btn_row_input, text="Karakter: 0", text_color=AppTheme.TEXT_MUTED, font=AppTheme.FONT_XS)
        self.enc_char_count_lbl.pack(side="right")
        
        # 2. Output Ciphertext
        out_card = ctk.CTkFrame(left_col, fg_color=AppTheme.BG_CARD, border_color=AppTheme.BORDER_COLOR, border_width=1, corner_radius=AppTheme.CORNER_RADIUS_MD)
        out_card.pack(fill="both", expand=True, pady=(AppTheme.PAD_SM, AppTheme.PAD_NONE))
        
        lbl_cipher_tag = ctk.CTkLabel(out_card, text="Hasil Enkripsi (Ciphertext - Base64):", font=AppTheme.FONT_MD_BOLD, text_color=AppTheme.COLOR_TEAL)
        lbl_cipher_tag.pack(anchor="w", padx=AppTheme.PAD_SM, pady=(AppTheme.PAD_SM, AppTheme.PAD_XS))
        
        self.enc_msg_output = self.create_scrolled_text(out_card, height=5, read_only=True)
        self.read_only_widgets.add(self.enc_msg_output)
        self.enc_msg_output.pack(fill="both", expand=True, padx=AppTheme.PAD_SM)
        self.set_placeholder(self.enc_msg_output, "Hasil enkripsi (Base64) akan muncul di sini...", is_output=True)
        
        btn_row = ctk.CTkFrame(out_card, fg_color=AppTheme.BG_CARD, corner_radius=0)
        btn_row.pack(fill="x", padx=AppTheme.PAD_SM, pady=(AppTheme.PAD_XS, AppTheme.PAD_SM))
        
        btn_copy = self.create_custom_button(
            btn_row,
            text="Salin Ciphertext",
            command=lambda: self.copy_to_clipboard(self.enc_msg_output.get("1.0", tk.END).strip(), btn_copy, "Salin Ciphertext"),
            bg_color=AppTheme.BG_PRIMARY,
            hover_bg=AppTheme.BORDER_COLOR,
            font=AppTheme.FONT_SM_BOLD,
            height=32
        )
        btn_copy.pack(side="left", padx=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        btn_clear = self.create_custom_button(
            btn_row,
            text="Bersihkan",
            command=self.clear_encrypt_message,
            bg_color=AppTheme.BG_PRIMARY,
            hover_bg=AppTheme.BORDER_COLOR,
            font=AppTheme.FONT_SM_BOLD,
            height=32
        )
        btn_clear.pack(side="left", padx=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        btn_save = self.create_custom_button(
            btn_row,
            text="Simpan File TXT",
            command=lambda: self.export_txt_file(self.enc_msg_output, "encrypted_message.txt"),
            bg_color=AppTheme.BG_PRIMARY,
            hover_bg=AppTheme.BORDER_COLOR,
            font=AppTheme.FONT_SM_BOLD,
            height=32
        )
        btn_save.pack(side="left")
        
        # KANAN: Penyatuan Kontrol Kunci & Metode ke dalam panel yang padu
        right_panel_card = ctk.CTkFrame(right_col, fg_color=AppTheme.BG_CARD, border_color=AppTheme.BORDER_COLOR, border_width=1, corner_radius=AppTheme.CORNER_RADIUS_MD)
        right_panel_card.pack(fill="both", expand=True)
        
        # Bagian Kunci Publik
        key_section = ctk.CTkFrame(right_panel_card, fg_color=AppTheme.BG_CARD, corner_radius=0)
        key_section.pack(fill="x", padx=AppTheme.PAD_SM, pady=AppTheme.PAD_SM)
        
        lbl_row = ctk.CTkFrame(key_section, fg_color=AppTheme.BG_CARD, corner_radius=0)
        lbl_row.pack(fill="x", pady=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        lbl_pub_tag = ctk.CTkLabel(lbl_row, text="Kunci Publik Penerima (.pem):", font=AppTheme.FONT_MD_BOLD, text_color=AppTheme.TEXT_MAIN)
        lbl_pub_tag.pack(side="left")
        
        btn_help = ctk.CTkButton(
            lbl_row,
            text="?",
            width=20,
            height=20,
            fg_color="transparent",
            hover_color=AppTheme.BORDER_COLOR,
            text_color=AppTheme.COLOR_TEAL,
            font=AppTheme.FONT_XS_BOLD,
            command=lambda: self.show_help_info(
                "Info Kunci Publik",
                "Kunci Publik (.pem) digunakan untuk MENGENKRIPSI data sehingga hanya penerima yang sah yang bisa membacanya.\n\n"
                "• Kunci ini aman untuk dibagikan ke siapa saja.\n"
                "• Mintalah kunci publik ini dari orang yang ingin Anda kirimi pesan."
            ),
            cursor="hand2"
        )
        btn_help.pack(side="left", padx=AppTheme.PAD_XS)
        
        key_row = ctk.CTkFrame(key_section, fg_color=AppTheme.BG_CARD, corner_radius=0)
        key_row.pack(fill="x")
        
        self.enc_msg_pubkey_var = tk.StringVar(value="")
        entry_key = self.create_entry(key_row, textvariable=self.enc_msg_pubkey_var, state="readonly")
        self.read_only_widgets.add(entry_key)
        entry_key.pack(side="left", fill="x", expand=True, padx=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        btn_browse_key = self.create_custom_button(
            key_row,
            text="Cari...",
            command=self.browse_enc_msg_key,
            bg_color=AppTheme.ACCENT,
            hover_bg=AppTheme.ACCENT_HOVER,
            font=AppTheme.FONT_SM_BOLD
        )
        btn_browse_key.pack(side="right")
        
        self.enc_key_status_lbl = ctk.CTkLabel(key_section, text="Status: Kunci belum dimuat", text_color=AppTheme.COLOR_RED, font=AppTheme.FONT_XS_BOLD, anchor="w")
        self.enc_key_status_lbl.pack(anchor="w", pady=(AppTheme.PAD_TINY, AppTheme.PAD_NONE))
        
        # Garis Separator
        sep = ctk.CTkFrame(right_panel_card, height=1, fg_color=AppTheme.BORDER_COLOR, corner_radius=0)
        sep.pack(fill="x")
        
        # Bagian Pilihan Metode
        method_section = ctk.CTkFrame(right_panel_card, fg_color=AppTheme.BG_CARD, corner_radius=0)
        method_section.pack(fill="both", expand=True, padx=AppTheme.PAD_SM, pady=AppTheme.PAD_SM)
        
        lbl_method_tag = ctk.CTkLabel(method_section, text="Pilih Metode Enkripsi (Hibrida):", font=AppTheme.FONT_MD_BOLD, text_color=AppTheme.TEXT_MAIN)
        lbl_method_tag.pack(anchor="w", pady=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        self.method_grid_frame = ctk.CTkFrame(method_section, fg_color=AppTheme.BG_CARD, corner_radius=0)
        self.method_grid_frame.pack(fill="both", expand=True)
        self.render_method_selection_grid(self.method_grid_frame)
        
        self.btn_encrypt_message = self.create_custom_button(
            method_section,
            text="ENKRIPSI PESAN",
            command=self.do_encrypt_message,
            bg_color=AppTheme.COLOR_EMERALD,
            hover_bg=AppTheme.COLOR_EMERALD_HOVER
        )
        self.btn_encrypt_message.pack(fill="x", pady=(AppTheme.PAD_SM, AppTheme.PAD_NONE))

    def render_encrypt_file_view(self, parent):
        """Membuat visualisasi komplit enkripsi berkas file dengan pembagian responsif 60:40."""
        parent.grid_columnconfigure(0, weight=3) # 60%
        parent.grid_columnconfigure(1, weight=2) # 40%
        parent.grid_rowconfigure(0, weight=1)
        
        left_col = ctk.CTkFrame(parent, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(AppTheme.PAD_NONE, AppTheme.PAD_SM))
        
        right_col = ctk.CTkFrame(parent, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(AppTheme.PAD_SM, AppTheme.PAD_NONE))
        
        # KIRI: Penyatuan Kontrol File & Kunci
        left_panel_card = ctk.CTkFrame(left_col, fg_color=AppTheme.BG_CARD, border_color=AppTheme.BORDER_COLOR, border_width=1, corner_radius=AppTheme.CORNER_RADIUS_MD)
        left_panel_card.pack(fill="both", expand=True)
        
        # Bagian Pilih Berkas
        file_section = ctk.CTkFrame(left_panel_card, fg_color=AppTheme.BG_CARD, corner_radius=0)
        file_section.pack(fill="x", padx=AppTheme.PAD_SM, pady=AppTheme.PAD_SM)
        
        lbl_row_file = ctk.CTkFrame(file_section, fg_color=AppTheme.BG_CARD, corner_radius=0)
        lbl_row_file.pack(fill="x", pady=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        lbl_src_tag = ctk.CTkLabel(lbl_row_file, text="Pilih Berkas Sumber (File Asli):", font=AppTheme.FONT_MD_BOLD, text_color=AppTheme.TEXT_MAIN)
        lbl_src_tag.pack(side="left")
        
        btn_help_file = ctk.CTkButton(
            lbl_row_file,
            text="?",
            width=20,
            height=20,
            fg_color="transparent",
            hover_color=AppTheme.BORDER_COLOR,
            text_color=AppTheme.COLOR_TEAL,
            font=AppTheme.FONT_XS_BOLD,
            command=lambda: self.show_help_info(
                "Info Berkas Sumber",
                "Pilih berkas/file jenis apa saja dari komputer Anda (seperti dokumen, gambar, PDF, zip) yang ingin Anda enkripsi secara aman."
            ),
            cursor="hand2"
        )
        btn_help_file.pack(side="left", padx=AppTheme.PAD_XS)
        
        file_row = ctk.CTkFrame(file_section, fg_color=AppTheme.BG_CARD, corner_radius=0)
        file_row.pack(fill="x")
        
        self.enc_file_path_var = tk.StringVar(value="")
        entry_file = self.create_entry(file_row, textvariable=self.enc_file_path_var, state="readonly")
        self.read_only_widgets.add(entry_file)
        entry_file.pack(side="left", fill="x", expand=True, padx=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        btn_browse_file = self.create_custom_button(
            file_row,
            text="Cari...",
            command=self.browse_enc_file,
            bg_color=AppTheme.ACCENT,
            hover_bg=AppTheme.ACCENT_HOVER,
            font=AppTheme.FONT_SM_BOLD
        )
        btn_browse_file.pack(side="right")
        
        self.enc_file_details_lbl = ctk.CTkLabel(file_section, text="File belum dipilih", text_color=AppTheme.COLOR_RED, font=AppTheme.FONT_XS_BOLD, anchor="w")
        self.enc_file_details_lbl.pack(anchor="w", pady=(AppTheme.PAD_TINY, AppTheme.PAD_NONE))
        
        # Garis Separator
        sep = ctk.CTkFrame(left_panel_card, height=1, fg_color=AppTheme.BORDER_COLOR, corner_radius=0)
        sep.pack(fill="x")
        
        # Bagian Pilih Kunci
        key_section = ctk.CTkFrame(left_panel_card, fg_color=AppTheme.BG_CARD, corner_radius=0)
        key_section.pack(fill="x", padx=AppTheme.PAD_SM, pady=AppTheme.PAD_SM)
        
        lbl_row_key = ctk.CTkFrame(key_section, fg_color=AppTheme.BG_CARD, corner_radius=0)
        lbl_row_key.pack(fill="x", pady=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        lbl_pub_tag = ctk.CTkLabel(lbl_row_key, text="Kunci Publik Penerima (.pem):", font=AppTheme.FONT_MD_BOLD, text_color=AppTheme.TEXT_MAIN)
        lbl_pub_tag.pack(side="left")
        
        btn_help_key = ctk.CTkButton(
            lbl_row_key,
            text="?",
            width=20,
            height=20,
            fg_color="transparent",
            hover_color=AppTheme.BORDER_COLOR,
            text_color=AppTheme.COLOR_TEAL,
            font=AppTheme.FONT_XS_BOLD,
            command=lambda: self.show_help_info(
                "Info Kunci Publik",
                "Pilih berkas kunci publik (.pem) milik penerima berkas. Ini memastikan hanya penerima tersebut yang dapat membuka berkas yang terenkripsi."
            ),
            cursor="hand2"
        )
        btn_help_key.pack(side="left", padx=AppTheme.PAD_XS)
        
        key_row = ctk.CTkFrame(key_section, fg_color=AppTheme.BG_CARD, corner_radius=0)
        key_row.pack(fill="x")
        
        self.enc_file_key_var = tk.StringVar(value="")
        entry_key = self.create_entry(key_row, textvariable=self.enc_file_key_var, state="readonly")
        self.read_only_widgets.add(entry_key)
        entry_key.pack(side="left", fill="x", expand=True, padx=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        btn_browse_key = self.create_custom_button(
            key_row,
            text="Cari...",
            command=self.browse_enc_file_key,
            bg_color=AppTheme.ACCENT,
            hover_bg=AppTheme.ACCENT_HOVER,
            font=AppTheme.FONT_SM_BOLD
        )
        btn_browse_key.pack(side="right")
        
        self.enc_file_key_status_lbl = ctk.CTkLabel(key_section, text="Kunci belum dimuat", text_color=AppTheme.COLOR_RED, font=AppTheme.FONT_XS_BOLD, anchor="w")
        self.enc_file_key_status_lbl.pack(anchor="w", pady=(AppTheme.PAD_TINY, AppTheme.PAD_NONE))
        
        # KANAN: Grid Metode & Aksi
        method_card = ctk.CTkFrame(right_col, fg_color=AppTheme.BG_CARD, border_color=AppTheme.BORDER_COLOR, border_width=1, corner_radius=AppTheme.CORNER_RADIUS_MD)
        method_card.pack(fill="both", expand=True)
        
        lbl_method_tag = ctk.CTkLabel(method_card, text="Pilih Metode Enkripsi (Hibrida):", font=AppTheme.FONT_MD_BOLD, text_color=AppTheme.TEXT_MAIN)
        lbl_method_tag.pack(anchor="w", padx=AppTheme.PAD_SM, pady=(AppTheme.PAD_SM, AppTheme.PAD_XS))
        
        self.method_grid_frame_file = ctk.CTkFrame(method_card, fg_color=AppTheme.BG_CARD, corner_radius=0)
        self.method_grid_frame_file.pack(fill="both", expand=True, padx=AppTheme.PAD_SM)
        self.render_method_selection_grid(self.method_grid_frame_file)
        
        self.btn_encrypt_file = self.create_custom_button(
            method_card,
            text="ENKRIPSI BERKAS",
            command=self.do_encrypt_file,
            bg_color=AppTheme.COLOR_EMERALD,
            hover_bg=AppTheme.COLOR_EMERALD_HOVER
        )
        self.btn_encrypt_file.pack(fill="x", padx=AppTheme.PAD_SM, pady=AppTheme.PAD_SM)

    def render_method_selection_grid(self, parent_frame):
        """Membuat grid 2x2 kartu interaktif dengan penjelasan komponen kriptografi yang seragam tingginya."""
        if not hasattr(self, "method_cards_dict"):
            self.method_cards_dict = {}
            
        old_cards = self.method_cards_dict.get(parent_frame, [])
        for card in old_cards:
            try:
                card.destroy()
            except Exception:
                pass
        self.method_cards_dict[parent_frame] = []
        
        methods = [
            {
                "num": 1,
                "title": "Method 1: X25519 + AES-GCM",
                "subtitle": "ECC & Authenticated Cipher (Recommended)",
                "desc": "Sangat cepat, aman, efisien, dengan ukuran pembungkus ciphertext terkecil."
            },
            {
                "num": 2,
                "title": "Method 2: X25519 + ChaCha20",
                "subtitle": "ECC & Stream Cipher Modern",
                "desc": "Optimal untuk perangkat tanpa akselerasi AES hardware (seperti mobile tua)."
            },
            {
                "num": 3,
                "title": "Method 3: RSA + AES-GCM",
                "subtitle": "RSA Key Wrap & Authenticated Cipher",
                "desc": "Standar industri klasik, sangat kompatibel untuk transfer antar platform."
            },
            {
                "num": 4,
                "title": "Method 4: RSA + AES-CBC",
                "subtitle": "RSA Key Wrap & Block Cipher (HMAC)",
                "desc": "Kombinasi klasik dengan jaminan integritas terpisah melalui skema HMAC-SHA256."
            }
        ]
        
        # Menerapkan uniform group "row" & "col" agar semua card memiliki tinggi dan lebar seragam
        for i in range(2):
            parent_frame.grid_columnconfigure(i, weight=1, uniform="col")
            parent_frame.grid_rowconfigure(i, weight=1, uniform="row", minsize=120)
            
        for idx, m in enumerate(methods):
            row = idx // 2
            col = idx % 2
            
            is_selected = (self.selected_method.get() == m["num"])
            card_bg = AppTheme.BG_PRIMARY if is_selected else AppTheme.BG_CARD
            border_color = AppTheme.ACCENT if is_selected else AppTheme.BORDER_COLOR
            border_thickness = 2 if is_selected else 1
            
            card = ctk.CTkFrame(
                parent_frame,
                fg_color=card_bg,
                border_color=border_color,
                border_width=border_thickness,
                corner_radius=AppTheme.CORNER_RADIUS_MD,
                cursor="hand2"
            )
            card.grid(row=row, column=col, padx=AppTheme.PAD_TINY, pady=AppTheme.PAD_TINY, sticky="nsew")
            
            rb = ctk.CTkRadioButton(
                card,
                text=m["title"],
                variable=self.selected_method,
                value=m["num"],
                command=self.on_method_selected,
                fg_color=AppTheme.ACCENT,
                text_color=AppTheme.TEXT_MAIN,
                hover_color=AppTheme.ACCENT_HOVER,
                font=AppTheme.FONT_SM_BOLD,
                cursor="hand2"
            )
            rb.pack(anchor="w", padx=AppTheme.PAD_SM, pady=(AppTheme.PAD_SM, AppTheme.PAD_TINY))
            
            lbl_sub = ctk.CTkLabel(
                card,
                text=m["subtitle"],
                text_color=AppTheme.COLOR_TEAL if is_selected else AppTheme.TEXT_MUTED,
                font=AppTheme.FONT_XS_BOLD,
                anchor="w"
            )
            lbl_sub.pack(anchor="w", padx=32, pady=(AppTheme.PAD_NONE, AppTheme.PAD_TINY))
            
            lbl_desc = ctk.CTkLabel(
                card,
                text=m["desc"],
                text_color=AppTheme.TEXT_MAIN if is_selected else AppTheme.TEXT_MUTED,
                font=AppTheme.FONT_XS,
                wraplength=220,
                justify="left",
                anchor="w"
            )
            lbl_desc.pack(anchor="w", padx=32, pady=(AppTheme.PAD_NONE, AppTheme.PAD_SM))
            
            # Memungkinkan klik dimanapun pada kartu untuk memilih metode
            def make_select_func(num=m["num"]):
                return lambda e: self.select_method_num(num)
                
            card.bind("<Button-1>", make_select_func())
            lbl_sub.bind("<Button-1>", make_select_func())
            lbl_desc.bind("<Button-1>", make_select_func())
            
            self.method_cards_dict[parent_frame].append(card)

    def select_method_num(self, num):
        self.selected_method.set(num)
        self.on_method_selected()

    def on_method_selected(self):
        if hasattr(self, "method_grid_frame") and self.method_grid_frame.winfo_exists():
            self.render_method_selection_grid(self.method_grid_frame)
        if hasattr(self, "method_grid_frame_file") and self.method_grid_frame_file.winfo_exists():
            self.render_method_selection_grid(self.method_grid_frame_file)

    # ==========================================
    # LOGIKA PENDUKUNG ENKRIPSI
    # ==========================================
    def browse_enc_msg_key(self):
        path = filedialog.askopenfilename(title="Pilih Kunci Publik Penerima (.pem)", filetypes=[("PEM Files", "*.pem")])
        if path:
            self.enc_msg_pubkey_var.set(path)
            self.enc_key_status_lbl.configure(text=f"Kunci dimuat: {os.path.basename(path)}", text_color=AppTheme.COLOR_TEAL)
            self.update_all_action_buttons_state()

    def browse_enc_file(self):
        path = filedialog.askopenfilename(title="Pilih Berkas Asli")
        if path:
            self.enc_file_path_var.set(path)
            try:
                size_bytes = os.path.getsize(path)
                if size_bytes >= 1024 * 1024:
                    size_str = f"{size_bytes / (1024*1024):.2f} MB"
                elif size_bytes >= 1024:
                    size_str = f"{size_bytes / 1024:.2f} KB"
                else:
                    size_str = f"{size_bytes} B"
                self.enc_file_details_lbl.configure(text=f"Terpilih: {os.path.basename(path)} ({size_str})", text_color=AppTheme.COLOR_TEAL)
            except Exception:
                self.enc_file_details_lbl.configure(text=f"Terpilih: {os.path.basename(path)}", text_color=AppTheme.COLOR_TEAL)
            self.update_all_action_buttons_state()

    def browse_enc_file_key(self):
        path = filedialog.askopenfilename(title="Pilih Kunci Publik Penerima (.pem)", filetypes=[("PEM Files", "*.pem")])
        if path:
            self.enc_file_key_var.set(path)
            self.enc_file_key_status_lbl.configure(text=f"Kunci dimuat: {os.path.basename(path)}", text_color=AppTheme.COLOR_TEAL)
            self.update_all_action_buttons_state()

    def do_encrypt_message(self):
        msg = self.enc_msg_input.get("1.0", tk.END).strip()
        if not msg or msg == "Tempel atau ketik pesan di sini...":
            messagebox.showwarning("Peringatan", "Pesan tidak boleh kosong!")
            return
            
        key_path = self.enc_msg_pubkey_var.get()
        if not key_path:
            messagebox.showwarning("Peringatan", "Pilih kunci publik penerima terlebih dahulu!")
            return
            
        method_idx = self.selected_method.get()
        
        def task():
            pub_key = load_public_key(key_path)
            cipher_b64 = encrypt_message(msg, pub_key, method=method_idx)
            return cipher_b64
            
        def on_success(res):
            self.enc_msg_output.configure(state="normal")
            self.enc_msg_output.delete("1.0", tk.END)
            self.enc_msg_output.insert(tk.END, res)
            self.enc_msg_output.configure(text_color=AppTheme.TEXT_MAIN)
            self.enc_msg_output.configure(state="disabled")
            self.update_status("Pesan berhasil dienkripsi", "success")
            
        def on_error(err):
            messagebox.showerror("Error", f"Enkripsi gagal: {err}")
            self.update_status("Enkripsi gagal", "error")
            
        self.run_task_in_background(
            task, on_success, on_error, "Mengenkripsi Pesan...", 
            self.btn_encrypt_message, "Mengenkripsi..."
        )

    def do_encrypt_file(self):
        file_asli = self.enc_file_path_var.get()
        key_path = self.enc_file_key_var.get()
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
            
        method_idx = self.selected_method.get()
        
        try:
            pub_key = load_public_key(key_path)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memuat kunci publik: {e}")
            return
            
        # Pengeksekusian di background thread agar UI tidak beku
        def task():
            encrypt_file(file_asli, file_enc, pub_key, method=method_idx)
            return file_enc
            
        def on_success(res):
            try:
                hash_asli = calculate_hash(file_asli)
            except Exception:
                hash_asli = "Gagal memproses checksum"
                
            messagebox.showinfo(
                "Sukses", 
                f"File berhasil dienkripsi!\n\n"
                f"Metode: Method {method_idx}\n"
                f"Tujuan: {res}\n"
                f"SHA-256 Asli: {hash_asli}"
            )
            self.update_status("Enkripsi berkas sukses", "success")
            
        def on_error(err):
            messagebox.showerror("Error", f"Enkripsi berkas gagal: {err}")
            self.update_status("Enkripsi berkas gagal", "error")
            
        self.run_task_in_background(
            task, on_success, on_error, "Mengenkripsi Berkas...",
            self.btn_encrypt_file, "Mengenkripsi..."
        )

    def clear_encrypt_message(self):
        self.set_placeholder(self.enc_msg_input, "Tempel atau ketik pesan di sini...")
        self.enc_char_count_lbl.configure(text="Karakter: 0")
        self.set_placeholder(self.enc_msg_output, "Hasil enkripsi (Base64) akan muncul di sini...", is_output=True)
        self.update_status("Ready", "success")
        self.update_all_action_buttons_state()

    def toggle_encrypt_subview(self, subview):
        if self.is_processing:
            return
        self.encrypt_subview = subview
        self.render_encrypt_content()

    def render_encrypt_content(self):
        """Menampilkan/menyembunyikan subview enkripsi tanpa menghancurkan widget."""
        if self.encrypt_subview == "message":
            self.enc_file_frame.pack_forget()
            self.enc_msg_frame.pack(fill="both", expand=True)
        else:
            self.enc_msg_frame.pack_forget()
            self.enc_file_frame.pack(fill="both", expand=True)

    # ==========================================
    # VIEW: DECRYPT PANEL (DEKRIPSI)
    # ==========================================
    def init_decrypt_view(self):
        frame = self.frames["decrypt"]
        
        pad_frame = ctk.CTkFrame(frame, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        pad_frame.pack(fill="both", expand=True, padx=AppTheme.PAD_MD, pady=AppTheme.PAD_MD)
        
        lbl_title = ctk.CTkLabel(pad_frame, text="DECRYPT PANEL", text_color=AppTheme.TEXT_MAIN, font=AppTheme.FONT_TITLE, anchor="w")
        lbl_title.pack(fill="x", pady=(AppTheme.PAD_NONE, AppTheme.PAD_SM))
        
        self.make_subview_toggle(pad_frame, self.decrypt_subview, self.toggle_decrypt_subview)
        
        self.decrypt_content_area = ctk.CTkFrame(pad_frame, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        self.decrypt_content_area.pack(fill="both", expand=True)
        
        # Stacked Frames: Inisialisasi frame message dan file satu kali
        self.dec_msg_frame = ctk.CTkFrame(self.decrypt_content_area, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        self.dec_file_frame = ctk.CTkFrame(self.decrypt_content_area, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        
        self.render_decrypt_message_view(self.dec_msg_frame)
        self.render_decrypt_file_view(self.dec_file_frame)
        
        self.render_decrypt_content()

    def toggle_decrypt_subview(self, subview):
        if self.is_processing:
            return
        self.decrypt_subview = subview
        self.render_decrypt_content()

    def render_decrypt_content(self):
        """Menampilkan/menyembunyikan subview dekripsi tanpa menghancurkan widget."""
        if self.decrypt_subview == "message":
            self.dec_file_frame.pack_forget()
            self.dec_msg_frame.pack(fill="both", expand=True)
        else:
            self.dec_msg_frame.pack_forget()
            self.dec_file_frame.pack(fill="both", expand=True)

    def render_decrypt_message_view(self, parent):
        """Membuat visualisasi komplit dekripsi pesan teks dengan pembagian rasio responsif 60:40."""
        parent.grid_columnconfigure(0, weight=3)
        parent.grid_columnconfigure(1, weight=2)
        parent.grid_rowconfigure(0, weight=1)
        
        left_col = ctk.CTkFrame(parent, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(AppTheme.PAD_NONE, AppTheme.PAD_SM))
        
        right_col = ctk.CTkFrame(parent, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(AppTheme.PAD_SM, AppTheme.PAD_NONE))
        
        # KIRI: Teks input/output
        # 1. Input Ciphertext
        input_card = ctk.CTkFrame(left_col, fg_color=AppTheme.BG_CARD, border_color=AppTheme.BORDER_COLOR, border_width=1, corner_radius=AppTheme.CORNER_RADIUS_MD)
        input_card.pack(fill="both", expand=True, pady=(AppTheme.PAD_NONE, AppTheme.PAD_SM))
        
        lbl_cipher_tag = ctk.CTkLabel(input_card, text="Pesan Terenkripsi (Ciphertext - Base64):", font=AppTheme.FONT_MD_BOLD, text_color=AppTheme.TEXT_MAIN)
        lbl_cipher_tag.pack(anchor="w", padx=AppTheme.PAD_SM, pady=(AppTheme.PAD_SM, AppTheme.PAD_XS))
        
        self.dec_msg_input = self.create_scrolled_text(input_card, height=5)
        self.dec_msg_input.pack(fill="both", expand=True, padx=AppTheme.PAD_SM)
        self.dec_msg_input.bind("<KeyRelease>", self.on_decrypt_text_change)
        self.set_placeholder(self.dec_msg_input, "Tempel ciphertext Base64 di sini...")
        
        btn_row_input = ctk.CTkFrame(input_card, fg_color=AppTheme.BG_CARD, corner_radius=0)
        btn_row_input.pack(fill="x", padx=AppTheme.PAD_SM, pady=(AppTheme.PAD_TINY, AppTheme.PAD_SM))
        
        btn_import = self.create_custom_button(
            btn_row_input,
            text="Buka File TXT",
            command=lambda: self.import_txt_file(self.dec_msg_input, self.on_decrypt_text_change),
            bg_color=AppTheme.BG_PRIMARY,
            hover_bg=AppTheme.BORDER_COLOR,
            font=AppTheme.FONT_SM_BOLD,
            height=32
        )
        btn_import.pack(side="left")
        
        self.dec_char_count_lbl = ctk.CTkLabel(btn_row_input, text="Karakter: 0", text_color=AppTheme.TEXT_MUTED, font=AppTheme.FONT_XS)
        self.dec_char_count_lbl.pack(side="right")
        
        # 2. Output Plaintext
        output_card = ctk.CTkFrame(left_col, fg_color=AppTheme.BG_CARD, border_color=AppTheme.BORDER_COLOR, border_width=1, corner_radius=AppTheme.CORNER_RADIUS_MD)
        output_card.pack(fill="both", expand=True, pady=(AppTheme.PAD_SM, AppTheme.PAD_NONE))
        
        lbl_plain_tag = ctk.CTkLabel(output_card, text="Hasil Dekripsi (Plaintext):", font=AppTheme.FONT_MD_BOLD, text_color=AppTheme.COLOR_TEAL)
        lbl_plain_tag.pack(anchor="w", padx=AppTheme.PAD_SM, pady=(AppTheme.PAD_SM, AppTheme.PAD_XS))
        
        self.dec_msg_output = self.create_scrolled_text(output_card, height=5, read_only=True)
        self.read_only_widgets.add(self.dec_msg_output)
        self.dec_msg_output.pack(fill="both", expand=True, padx=AppTheme.PAD_SM)
        self.set_placeholder(self.dec_msg_output, "Hasil dekripsi akan muncul di sini...", is_output=True)
        
        btn_row = ctk.CTkFrame(output_card, fg_color=AppTheme.BG_CARD, corner_radius=0)
        btn_row.pack(fill="x", padx=AppTheme.PAD_SM, pady=(AppTheme.PAD_XS, AppTheme.PAD_SM))
        
        btn_copy = self.create_custom_button(
            btn_row,
            text="Salin Plaintext",
            command=lambda: self.copy_to_clipboard(self.dec_msg_output.get("1.0", tk.END).strip(), btn_copy, "Salin Plaintext"),
            bg_color=AppTheme.BG_PRIMARY,
            hover_bg=AppTheme.BORDER_COLOR,
            font=AppTheme.FONT_SM_BOLD,
            height=32
        )
        btn_copy.pack(side="left", padx=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        btn_clear = self.create_custom_button(
            btn_row,
            text="Bersihkan",
            command=self.clear_decrypt_message,
            bg_color=AppTheme.BG_PRIMARY,
            hover_bg=AppTheme.BORDER_COLOR,
            font=AppTheme.FONT_SM_BOLD,
            height=32
        )
        btn_clear.pack(side="left", padx=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        btn_save = self.create_custom_button(
            btn_row,
            text="Simpan File TXT",
            command=lambda: self.export_txt_file(self.dec_msg_output, "decrypted_message.txt"),
            bg_color=AppTheme.BG_PRIMARY,
            hover_bg=AppTheme.BORDER_COLOR,
            font=AppTheme.FONT_SM_BOLD,
            height=32
        )
        btn_save.pack(side="left")
        
        # KANAN: Penyatuan Kontrol Kunci, Badge & Detail Komponen
        right_panel_card = ctk.CTkFrame(right_col, fg_color=AppTheme.BG_CARD, border_color=AppTheme.BORDER_COLOR, border_width=1, corner_radius=AppTheme.CORNER_RADIUS_MD)
        right_panel_card.pack(fill="both", expand=True)
        
        # Bagian Kunci Privat
        key_section = ctk.CTkFrame(right_panel_card, fg_color=AppTheme.BG_CARD, corner_radius=0)
        key_section.pack(fill="x", padx=AppTheme.PAD_SM, pady=AppTheme.PAD_SM)
        
        lbl_row = ctk.CTkFrame(key_section, fg_color=AppTheme.BG_CARD, corner_radius=0)
        lbl_row.pack(fill="x", pady=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        lbl_priv_tag = ctk.CTkLabel(lbl_row, text="Kunci Privat Anda (.pem):", font=AppTheme.FONT_MD_BOLD, text_color=AppTheme.TEXT_MAIN)
        lbl_priv_tag.pack(side="left")
        
        btn_help = ctk.CTkButton(
            lbl_row,
            text="?",
            width=20,
            height=20,
            fg_color="transparent",
            hover_color=AppTheme.BORDER_COLOR,
            text_color=AppTheme.COLOR_TEAL,
            font=AppTheme.FONT_XS_BOLD,
            command=lambda: self.show_help_info(
                "Info Kunci Privat",
                "Kunci Privat (.pem) digunakan untuk MENDEKRIPSI data yang telah dikirimkan kepada Anda.\n\n"
                "• JANGAN PERNAH membagikan file ini kepada siapa pun.\n"
                "• Simpan file ini di tempat yang aman dan rahasia."
            ),
            cursor="hand2"
        )
        btn_help.pack(side="left", padx=AppTheme.PAD_XS)
        
        key_row = ctk.CTkFrame(key_section, fg_color=AppTheme.BG_CARD, corner_radius=0)
        key_row.pack(fill="x")
        
        self.dec_msg_privkey_var = tk.StringVar(value="")
        entry_key = self.create_entry(key_row, textvariable=self.dec_msg_privkey_var, state="readonly")
        self.read_only_widgets.add(entry_key)
        entry_key.pack(side="left", fill="x", expand=True, padx=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        btn_browse_key = self.create_custom_button(
            key_row,
            text="Cari...",
            command=self.browse_dec_msg_key,
            bg_color=AppTheme.ACCENT,
            hover_bg=AppTheme.ACCENT_HOVER,
            font=AppTheme.FONT_SM_BOLD
        )
        btn_browse_key.pack(side="right")
        
        self.dec_key_status_lbl = ctk.CTkLabel(key_section, text="Status: Kunci belum dimuat", text_color=AppTheme.COLOR_RED, font=AppTheme.FONT_XS_BOLD, anchor="w")
        self.dec_key_status_lbl.pack(anchor="w", pady=(AppTheme.PAD_TINY, AppTheme.PAD_NONE))
        
        # Garis Separator
        sep = ctk.CTkFrame(right_panel_card, height=1, fg_color=AppTheme.BORDER_COLOR, corner_radius=0)
        sep.pack(fill="x")
        
        # Bagian Status Deteksi & Rincian Komponen Kriptografi
        badge_section = ctk.CTkFrame(right_panel_card, fg_color=AppTheme.BG_CARD, corner_radius=0)
        badge_section.pack(fill="both", expand=True, padx=AppTheme.PAD_SM, pady=AppTheme.PAD_SM)
        
        lbl_detect_tag = ctk.CTkLabel(badge_section, text="Metode Enkripsi Terdeteksi:", font=AppTheme.FONT_MD_BOLD, text_color=AppTheme.TEXT_MAIN)
        lbl_detect_tag.pack(anchor="w", pady=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        self.detected_badge_frame = ctk.CTkFrame(badge_section, fg_color=AppTheme.BORDER_COLOR, corner_radius=AppTheme.CORNER_RADIUS_SM)
        self.detected_badge_frame.pack(fill="x", pady=(AppTheme.PAD_NONE, AppTheme.PAD_SM))
        
        self.detected_badge = ctk.CTkLabel(
            self.detected_badge_frame,
            text="FORMAT: KOSONG",
            text_color=AppTheme.TEXT_MAIN,
            fg_color=AppTheme.BORDER_COLOR,
            font=AppTheme.FONT_CODE_BOLD,
            anchor="center"
        )
        self.detected_badge.pack(fill="both", expand=True, pady=AppTheme.PAD_XS)
        
        # Card Detail Rincian Komponen Kriptografi
        self.dec_msg_details_card = ctk.CTkFrame(badge_section, fg_color=AppTheme.BG_PRIMARY, border_color=AppTheme.BORDER_COLOR, border_width=1, corner_radius=AppTheme.CORNER_RADIUS_SM)
        self.dec_msg_details_card.pack(fill="x", pady=(AppTheme.PAD_NONE, AppTheme.PAD_SM))
        
        self.dec_msg_details_lbl = ctk.CTkLabel(
            self.dec_msg_details_card,
            text="Masukkan atau tempel ciphertext Base64 untuk melihat rincian komponen kriptografi.",
            text_color=AppTheme.TEXT_MUTED,
            font=AppTheme.FONT_SM,
            wraplength=280,
            justify="left",
            anchor="w"
        )
        self.dec_msg_details_lbl.pack(fill="x", padx=AppTheme.PAD_XS, pady=AppTheme.PAD_XS)
        
        self.btn_decrypt_message = self.create_custom_button(
            badge_section,
            text="DEKRIPSI PESAN",
            command=self.do_decrypt_message,
            bg_color=AppTheme.COLOR_AMBER,
            hover_bg=AppTheme.COLOR_AMBER_HOVER
        )
        self.btn_decrypt_message.pack(fill="x", side="bottom")

    def render_decrypt_file_view(self, parent):
        """Membuat visualisasi komplit dekripsi berkas file dengan pembagian responsif 60:40."""
        parent.grid_columnconfigure(0, weight=3) # 60%
        parent.grid_columnconfigure(1, weight=2) # 40%
        parent.grid_rowconfigure(0, weight=1)
        
        left_col = ctk.CTkFrame(parent, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(AppTheme.PAD_NONE, AppTheme.PAD_SM))
        
        right_col = ctk.CTkFrame(parent, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(AppTheme.PAD_SM, AppTheme.PAD_NONE))
        
        # KIRI: Penyatuan Kontrol File & Kunci
        left_panel_card = ctk.CTkFrame(left_col, fg_color=AppTheme.BG_CARD, border_color=AppTheme.BORDER_COLOR, border_width=1, corner_radius=AppTheme.CORNER_RADIUS_MD)
        left_panel_card.pack(fill="both", expand=True)
        
        # Bagian Pilih Berkas
        file_section = ctk.CTkFrame(left_panel_card, fg_color=AppTheme.BG_CARD, corner_radius=0)
        file_section.pack(fill="x", padx=AppTheme.PAD_SM, pady=AppTheme.PAD_SM)
        
        lbl_row_file = ctk.CTkFrame(file_section, fg_color=AppTheme.BG_CARD, corner_radius=0)
        lbl_row_file.pack(fill="x", pady=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        lbl_src_tag = ctk.CTkLabel(lbl_row_file, text="Pilih Berkas Terenkripsi (.enc):", font=AppTheme.FONT_MD_BOLD, text_color=AppTheme.TEXT_MAIN)
        lbl_src_tag.pack(side="left")
        
        btn_help_file = ctk.CTkButton(
            lbl_row_file,
            text="?",
            width=20,
            height=20,
            fg_color="transparent",
            hover_color=AppTheme.BORDER_COLOR,
            text_color=AppTheme.COLOR_TEAL,
            font=AppTheme.FONT_XS_BOLD,
            command=lambda: self.show_help_info(
                "Info Berkas Terenkripsi",
                "Pilih berkas terenkripsi dengan ekstensi (.enc) yang ingin Anda kembalikan ke berkas asli."
            ),
            cursor="hand2"
        )
        btn_help_file.pack(side="left", padx=AppTheme.PAD_XS)
        
        file_row = ctk.CTkFrame(file_section, fg_color=AppTheme.BG_CARD, corner_radius=0)
        file_row.pack(fill="x")
        
        self.dec_file_path_var = tk.StringVar(value="")
        entry_file = self.create_entry(file_row, textvariable=self.dec_file_path_var, state="readonly")
        self.read_only_widgets.add(entry_file)
        entry_file.pack(side="left", fill="x", expand=True, padx=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        btn_browse_file = self.create_custom_button(
            file_row,
            text="Cari...",
            command=self.browse_dec_file,
            bg_color=AppTheme.ACCENT,
            hover_bg=AppTheme.ACCENT_HOVER,
            font=AppTheme.FONT_SM_BOLD
        )
        btn_browse_file.pack(side="right")
        
        self.dec_file_selection_lbl = ctk.CTkLabel(file_section, text="File belum dipilih", text_color=AppTheme.COLOR_RED, font=AppTheme.FONT_XS_BOLD, anchor="w")
        self.dec_file_selection_lbl.pack(anchor="w", pady=(AppTheme.PAD_TINY, AppTheme.PAD_NONE))
        
        # Garis Separator
        sep = ctk.CTkFrame(left_panel_card, height=1, fg_color=AppTheme.BORDER_COLOR, corner_radius=0)
        sep.pack(fill="x")
        
        # Bagian Pilih Kunci
        key_section = ctk.CTkFrame(left_panel_card, fg_color=AppTheme.BG_CARD, corner_radius=0)
        key_section.pack(fill="x", padx=AppTheme.PAD_SM, pady=AppTheme.PAD_SM)
        
        lbl_row_key = ctk.CTkFrame(key_section, fg_color=AppTheme.BG_CARD, corner_radius=0)
        lbl_row_key.pack(fill="x", pady=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        lbl_priv_tag = ctk.CTkLabel(lbl_row_key, text="Kunci Privat Anda (.pem):", font=AppTheme.FONT_MD_BOLD, text_color=AppTheme.TEXT_MAIN)
        lbl_priv_tag.pack(side="left")
        
        btn_help_key = ctk.CTkButton(
            lbl_row_key,
            text="?",
            width=20,
            height=20,
            fg_color="transparent",
            hover_color=AppTheme.BORDER_COLOR,
            text_color=AppTheme.COLOR_TEAL,
            font=AppTheme.FONT_XS_BOLD,
            command=lambda: self.show_help_info(
                "Info Kunci Privat",
                "Pilih berkas kunci privat (.pem) Anda yang cocok dengan kunci publik yang digunakan untuk mengenkripsi berkas ini. Ini diperlukan untuk membuka dekripsi berkas."
            ),
            cursor="hand2"
        )
        btn_help_key.pack(side="left", padx=AppTheme.PAD_XS)
        
        key_row = ctk.CTkFrame(key_section, fg_color=AppTheme.BG_CARD, corner_radius=0)
        key_row.pack(fill="x")
        
        self.dec_file_key_var = tk.StringVar(value="")
        entry_key = self.create_entry(key_row, textvariable=self.dec_file_key_var, state="readonly")
        self.read_only_widgets.add(entry_key)
        entry_key.pack(side="left", fill="x", expand=True, padx=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        btn_browse_key = self.create_custom_button(
            key_row,
            text="Cari...",
            command=self.browse_dec_file_key,
            bg_color=AppTheme.ACCENT,
            hover_bg=AppTheme.ACCENT_HOVER,
            font=AppTheme.FONT_SM_BOLD
        )
        btn_browse_key.pack(side="right")
        
        self.dec_file_key_status_lbl = ctk.CTkLabel(key_section, text="Kunci belum dimuat", text_color=AppTheme.COLOR_RED, font=AppTheme.FONT_XS_BOLD, anchor="w")
        self.dec_file_key_status_lbl.pack(anchor="w", pady=(AppTheme.PAD_TINY, AppTheme.PAD_NONE))
        
        # KANAN: Panel 'Metode Enkripsi Terdeteksi' (menggunakan CTkFrame yang konsisten)
        self.dec_file_method_card = ctk.CTkFrame(
            right_col,
            fg_color=AppTheme.BG_CARD,
            border_color=AppTheme.BORDER_COLOR,
            border_width=1,
            corner_radius=8
        )
        self.dec_file_method_card.pack(fill="both", expand=True)
        
        lbl_method_tag = ctk.CTkLabel(self.dec_file_method_card, text="Metode Terdeteksi (Dari Berkas):", font=AppTheme.FONT_MD_BOLD, text_color=AppTheme.TEXT_MAIN)
        lbl_method_tag.pack(anchor="w", padx=AppTheme.PAD_SM, pady=(AppTheme.PAD_SM, AppTheme.PAD_XS))
        
        self.dec_file_badge_frame = ctk.CTkFrame(self.dec_file_method_card, fg_color=AppTheme.BORDER_COLOR, corner_radius=AppTheme.CORNER_RADIUS_SM)
        self.dec_file_badge_frame.pack(fill="x", padx=AppTheme.PAD_SM, pady=(AppTheme.PAD_NONE, AppTheme.PAD_SM))
        
        self.dec_file_detected_badge = ctk.CTkLabel(
            self.dec_file_badge_frame,
            text="FORMAT: KOSONG / FILE BELUM DIPILIH",
            text_color=AppTheme.TEXT_MAIN,
            fg_color=AppTheme.BORDER_COLOR,
            font=AppTheme.FONT_CODE_BOLD,
            anchor="center"
        )
        self.dec_file_detected_badge.pack(fill="both", expand=True, pady=AppTheme.PAD_XS)
        
        # Container Rincian Komponen Kriptografi
        self.dec_file_details_container = ctk.CTkFrame(
            self.dec_file_method_card,
            fg_color=AppTheme.BG_PRIMARY,
            border_color=AppTheme.BORDER_COLOR,
            border_width=1,
            corner_radius=8
        )
        self.dec_file_details_container.pack(fill="both", expand=True, padx=AppTheme.PAD_SM, pady=(AppTheme.PAD_NONE, AppTheme.PAD_SM))
        
        # Render placeholder awal
        self.render_crypto_details_file(None)
        
        self.btn_decrypt_file = self.create_custom_button(
            self.dec_file_method_card,
            text="DEKRIPSI BERKAS",
            command=self.do_decrypt_file,
            bg_color=AppTheme.COLOR_AMBER,
            hover_bg=AppTheme.COLOR_AMBER_HOVER
        )
        self.btn_decrypt_file.pack(fill="x", padx=AppTheme.PAD_SM, pady=(AppTheme.PAD_NONE, AppTheme.PAD_SM))

    def render_crypto_details_file(self, method_num):
        """Memperbarui visual rincian komponen kriptografi secara terstruktur di panel File Mode."""
        # Bersihkan widget lama di dalam container rincian
        for child in self.dec_file_details_container.winfo_children():
            child.destroy()
            
        if method_num is None:
            # Tampilkan placeholder teks dengan elegan menggunakan TEXT_MUTED
            placeholder_lbl = ctk.CTkLabel(
                self.dec_file_details_container,
                text="Pilih berkas terenkripsi (.enc) untuk mendeteksi metode dan rincian komponen kriptografi.",
                text_color=AppTheme.TEXT_MUTED,
                font=AppTheme.FONT_SM,
                wraplength=240,
                justify="center"
            )
            placeholder_lbl.pack(fill="both", expand=True, padx=AppTheme.PAD_SM, pady=AppTheme.PAD_SM)
            return

        # Data rincian per metode enkripsi
        methods_info = {
            1: {
                "title": "Method 1: X25519 + AES-GCM",
                "subtitle": "ECC & Authenticated Cipher (Recommended)",
                "asym": "X25519 (256-bit ECDH)",
                "sym": "AES-256-GCM",
                "auth": "AEAD (Built-in)",
                "fs": "Ya (Ephemeral Key)"
            },
            2: {
                "title": "Method 2: X25519 + ChaCha20",
                "subtitle": "ECC & Stream Cipher Modern",
                "asym": "X25519 (256-bit ECDH)",
                "sym": "ChaCha20-Poly1305",
                "auth": "AEAD (Built-in)",
                "fs": "Ya (Ephemeral Key)"
            },
            3: {
                "title": "Method 3: RSA + AES-GCM",
                "subtitle": "RSA Key Wrap & Authenticated Cipher",
                "asym": "RSA-2048 (OAEP-SHA256)",
                "sym": "AES-256-GCM",
                "auth": "AEAD (Built-in)",
                "fs": "Tidak (Static Key Wrap)"
            },
            4: {
                "title": "Method 4: RSA + AES-CBC",
                "subtitle": "RSA Key Wrap & Block Cipher (HMAC)",
                "asym": "RSA-2048 (OAEP-SHA256)",
                "sym": "AES-256-CBC",
                "auth": "HMAC-SHA256 (Encrypt-then-MAC)",
                "fs": "Tidak (Static Key Wrap)"
            }
        }
        
        info = methods_info.get(method_num)
        if not info:
            err_lbl = ctk.CTkLabel(
                self.dec_file_details_container,
                text="Metode tidak dikenal atau format berkas tidak valid.",
                text_color=AppTheme.COLOR_RED,
                font=AppTheme.FONT_MD_BOLD,
                wraplength=240,
                justify="center"
            )
            err_lbl.pack(fill="both", expand=True, padx=AppTheme.PAD_SM, pady=AppTheme.PAD_SM)
            return

        # Render judul dan deskripsi metode enkripsi
        lbl_title = ctk.CTkLabel(
            self.dec_file_details_container,
            text=info["title"],
            font=AppTheme.FONT_MD_BOLD,
            text_color=AppTheme.TEXT_MAIN,
            anchor="w"
        )
        lbl_title.pack(fill="x", padx=AppTheme.PAD_SM, pady=(AppTheme.PAD_SM, AppTheme.PAD_TINY))
        
        lbl_sub = ctk.CTkLabel(
            self.dec_file_details_container,
            text=info["subtitle"],
            font=AppTheme.FONT_XS_BOLD,
            text_color=AppTheme.COLOR_TEAL,
            anchor="w"
        )
        lbl_sub.pack(fill="x", padx=AppTheme.PAD_SM, pady=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        # Garis pembatas horizontal tipis
        div = ctk.CTkFrame(self.dec_file_details_container, height=1, fg_color=AppTheme.BORDER_COLOR, corner_radius=0)
        div.pack(fill="x", padx=AppTheme.PAD_SM, pady=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        # Grid Rincian Komponen Kriptografi (Asimetris, Simetris, Autentikasi)
        grid_frame = ctk.CTkFrame(self.dec_file_details_container, fg_color="transparent", corner_radius=0)
        grid_frame.pack(fill="x", padx=AppTheme.PAD_SM, pady=(AppTheme.PAD_NONE, AppTheme.PAD_SM))
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=2)
        
        rows_data = [
            ("Asimetris:", info["asym"]),
            ("Simetris:", info["sym"]),
            ("Autentikasi:", info["auth"]),
            ("Forward Secrecy:", info["fs"])
        ]
        
        for row_idx, (label_text, val_text) in enumerate(rows_data):
            lbl_param = ctk.CTkLabel(
                grid_frame,
                text=label_text,
                font=AppTheme.FONT_SM_BOLD,
                text_color=AppTheme.TEXT_MUTED,
                anchor="w"
            )
            lbl_param.grid(row=row_idx, column=0, sticky="w", pady=AppTheme.PAD_TINY)
            
            lbl_val = ctk.CTkLabel(
                grid_frame,
                text=val_text,
                font=AppTheme.FONT_SM,
                text_color=AppTheme.TEXT_MAIN,
                anchor="w"
            )
            lbl_val.grid(row=row_idx, column=1, sticky="w", pady=AppTheme.PAD_TINY)

    # ==========================================
    # LOGIKA PENDUKUNG DEKRIPSI
    # ==========================================
    def browse_dec_msg_key(self):
        path = filedialog.askopenfilename(title="Pilih Kunci Privat Anda (.pem)", filetypes=[("PEM Files", "*.pem")])
        if path:
            self.dec_msg_privkey_var.set(path)
            self.dec_key_status_lbl.configure(text=f"Kunci dimuat: {os.path.basename(path)}", text_color=AppTheme.COLOR_TEAL)
            self.update_all_action_buttons_state()

    def browse_dec_file(self):
        path = filedialog.askopenfilename(title="Pilih Berkas Terenkripsi", filetypes=[("Encrypted Files", "*.enc")])
        if path:
            self.dec_file_path_var.set(path)
            try:
                size_bytes = os.path.getsize(path)
                if size_bytes >= 1024 * 1024:
                    size_str = f"{size_bytes / (1024*1024):.2f} MB"
                elif size_bytes >= 1024:
                    size_str = f"{size_bytes / 1024:.2f} KB"
                else:
                    size_str = f"{size_bytes} B"
                self.dec_file_selection_lbl.configure(text=f"Terpilih: {os.path.basename(path)} ({size_str})", text_color=AppTheme.COLOR_TEAL)
            except Exception:
                self.dec_file_selection_lbl.configure(text=f"Terpilih: {os.path.basename(path)}", text_color=AppTheme.COLOR_TEAL)
                
            self.detect_file_encryption_method(path)
            self.update_all_action_buttons_state()

    def detect_file_encryption_method(self, path):
        """Membaca byte pertama file untuk mendeteksi metode enkripsi yang dipakai."""
        try:
            with open(path, "rb") as f:
                first_byte = f.read(1)
                if first_byte:
                    m = first_byte[0]
                    if m == 1:
                        self.update_file_detected_badge("METHOD 1: X25519 + AES-GCM", AppTheme.COLOR_TEAL)
                    elif m == 2:
                        self.update_file_detected_badge("METHOD 2: X25519 + CHACHA20", AppTheme.COLOR_VIOLET)
                    elif m == 3:
                        self.update_file_detected_badge("METHOD 3: RSA + AES-GCM", AppTheme.COLOR_BLUE)
                    elif m == 4:
                        self.update_file_detected_badge("METHOD 4: RSA + AES-CBC", AppTheme.COLOR_AMBER)
                    else:
                        self.update_file_detected_badge("LEGACY / UNKNOWN METHOD", AppTheme.COLOR_SLATE)
                        
                    if m in (1, 2, 3, 4):
                        self.render_crypto_details_file(m)
                    else:
                        self.update_file_detected_badge("METHOD UNKNOWN", AppTheme.COLOR_RED)
                        self.render_crypto_details_file(None)
                else:
                    self.update_file_detected_badge("BERKAS KOSONG", AppTheme.COLOR_RED)
                    self.render_crypto_details_file(None)
        except Exception:
            self.update_file_detected_badge("GAGAL MEMBACA BERKAS", AppTheme.COLOR_RED)
            self.render_crypto_details_file(None)

    def update_file_detected_badge(self, text, bg_color):
        if hasattr(self, "dec_file_detected_badge") and hasattr(self, "dec_file_badge_frame"):
            self.dec_file_detected_badge.configure(text=text, fg_color=bg_color)
            self.dec_file_badge_frame.configure(fg_color=bg_color)

    def browse_dec_file_key(self):
        path = filedialog.askopenfilename(title="Pilih Kunci Privat Anda (.pem)", filetypes=[("PEM Files", "*.pem")])
        if path:
            self.dec_file_key_var.set(path)
            self.dec_file_key_status_lbl.configure(text=f"Kunci dimuat: {os.path.basename(path)}", text_color=AppTheme.COLOR_TEAL)
            self.update_all_action_buttons_state()

    def do_decrypt_message(self):
        cipher_b64 = self.dec_msg_input.get("1.0", tk.END).strip()
        if not cipher_b64 or cipher_b64 == "Tempel ciphertext Base64 di sini...":
            messagebox.showwarning("Peringatan", "Teks terenkripsi tidak boleh kosong!")
            return
            
        key_path = self.dec_msg_privkey_var.get()
        if not key_path:
            messagebox.showwarning("Peringatan", "Pilih kunci privat terlebih dahulu!")
            return
            
        def task():
            priv_key = load_private_key(key_path)
            plain = decrypt_message(cipher_b64, priv_key)
            return plain
            
        def on_success(res):
            self.dec_msg_output.configure(state="normal")
            self.dec_msg_output.delete("1.0", tk.END)
            self.dec_msg_output.insert(tk.END, res)
            self.dec_msg_output.configure(text_color=AppTheme.TEXT_MAIN)
            self.dec_msg_output.configure(state="disabled")
            self.update_status("Pesan berhasil didekripsi", "success")
            
        def on_error(err):
            messagebox.showerror("Error", f"Dekripsi gagal! Kunci salah atau data rusak.\nDetail: {err}")
            self.update_status("Dekripsi gagal", "error")
            
        self.run_task_in_background(
            task, on_success, on_error, "Mendekripsi Pesan...", 
            self.btn_decrypt_message, "Mendekripsi..."
        )

    def do_decrypt_file(self):
        file_enc = self.dec_file_path_var.get()
        key_path = self.dec_file_key_var.get()
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
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memuat kunci privat: {e}")
            return
            
        # Pengeksekusian di background thread agar UI tidak beku
        def task():
            decrypt_file(file_enc, file_dec, priv_key)
            return file_dec
            
        def on_success(res):
            try:
                hash_dec = calculate_hash(res)
            except Exception:
                hash_dec = "Gagal memproses checksum"
                
            messagebox.showinfo(
                "Sukses", 
                f"File berhasil didekripsi!\n\n"
                f"Tujuan: {res}\n"
                f"SHA-256 Hasil Dekripsi: {hash_dec}"
            )
            self.update_status("Dekripsi berkas sukses", "success")
            
        def on_error(err):
            messagebox.showerror("Error", f"Dekripsi berkas gagal! Detail: {err}")
            self.update_status("Dekripsi berkas gagal", "error")
            
        self.run_task_in_background(
            task, on_success, on_error, "Mendekripsi Berkas...",
            self.btn_decrypt_file, "Mendekripsi..."
        )

    def on_decrypt_text_change(self, event=None):
        """Auto detect metode enkripsi hibrida dari packet header payload Base64 secara real-time."""
        cipher_b64 = self.dec_msg_input.get("1.0", tk.END).strip()
        self.dec_char_count_lbl.configure(text=f"Karakter: {len(cipher_b64)}")
        
        if not cipher_b64 or cipher_b64 == "Tempel ciphertext Base64 di sini...":
            self.update_detected_badge("FORMAT: KOSONG", AppTheme.BORDER_COLOR)
            self.dec_msg_details_lbl.configure(text="Masukkan atau tempel ciphertext Base64 untuk melihat rincian komponen kriptografi.", text_color=AppTheme.TEXT_MUTED)
        else:
            try:
                cipher_clean = cipher_b64.replace("\n", "").replace(" ", "")
                packet = base64.b64decode(cipher_clean.encode('utf-8'))
                if len(packet) > 0:
                    first_byte = packet[0]
                    if first_byte == 1:
                        self.update_detected_badge("METHOD 1: X25519 + AES-GCM", AppTheme.COLOR_TEAL)
                    elif first_byte == 2:
                        self.update_detected_badge("METHOD 2: X25519 + CHACHA20", AppTheme.COLOR_VIOLET)
                    elif first_byte == 3:
                        self.update_detected_badge("METHOD 3: RSA + AES-GCM", AppTheme.COLOR_BLUE)
                    elif first_byte == 4:
                        self.update_detected_badge("METHOD 4: RSA + AES-CBC", AppTheme.COLOR_AMBER)
                    else:
                        self.update_detected_badge("LEGACY / UNKNOWN METHOD", AppTheme.COLOR_SLATE)
                        
                    if first_byte in (1, 2, 3, 4):
                        self.update_crypto_details(first_byte, is_file=False)
                    else:
                        self.dec_msg_details_lbl.configure(text="Metode tidak dikenal atau format salah.", text_color=AppTheme.COLOR_RED)
                else:
                    self.update_detected_badge("DATA KOSONG", AppTheme.COLOR_RED)
                    self.dec_msg_details_lbl.configure(text="Paket data kosong.", text_color=AppTheme.COLOR_RED)
            except Exception:
                self.update_detected_badge("BUKAN BASE64 VALID", AppTheme.COLOR_RED)
                self.dec_msg_details_lbl.configure(text="Format data salah / bukan Base64 valid.", text_color=AppTheme.COLOR_RED)
        
        self.update_all_action_buttons_state()

    def update_crypto_details(self, method_num):
        """Memperbarui visual rincian komponen kriptografi untuk mode dekripsi pesan."""
        details = {
            1: "• Asymmetric: X25519 (256-bit ECDH)\n• Symmetric: AES-256-GCM\n• Auth: AEAD (Built-in)\n• Forward Secrecy: Ya (Ephemeral Key)",
            2: "• Asymmetric: X25519 (256-bit ECDH)\n• Symmetric: ChaCha20-Poly1305\n• Auth: AEAD (Built-in)\n• Forward Secrecy: Ya (Ephemeral Key)",
            3: "• Asymmetric: RSA-2048 (OAEP-SHA256)\n• Symmetric: AES-256-GCM\n• Auth: AEAD (Built-in)\n• Forward Secrecy: Tidak (Static Key Wrap)",
            4: "• Asymmetric: RSA-2048 (OAEP-SHA256)\n• Symmetric: AES-256-CBC\n• Auth: HMAC-SHA256 (Encrypt-then-MAC)\n• Forward Secrecy: Tidak (Static Key Wrap)"
        }
        
        text = details.get(method_num, "Metode tidak dikenal atau format berkas tidak valid.")
        self.dec_msg_details_lbl.configure(text=text, text_color=AppTheme.TEXT_MAIN)

    def clear_decrypt_message(self):
        self.set_placeholder(self.dec_msg_input, "Tempel ciphertext Base64 di sini...")
        self.dec_char_count_lbl.configure(text="Karakter: 0")
        self.set_placeholder(self.dec_msg_output, "Hasil dekripsi akan muncul di sini...", is_output=True)
        self.update_detected_badge("FORMAT: KOSONG", AppTheme.BORDER_COLOR)
        self.dec_msg_details_lbl.configure(text="Masukkan atau tempel ciphertext Base64 untuk melihat rincian komponen kriptografi.", text_color=AppTheme.TEXT_MUTED)
        self.update_status("Ready", "success")
        self.update_all_action_buttons_state()

    def toggle_decrypt_subview(self, subview):
        if self.is_processing:
            return
        self.decrypt_subview = subview
        self.render_decrypt_content()

    # ==========================================
    # UTILITAS PEMBANTU LAINNYA
    # ==========================================
    def copy_to_clipboard(self, text, button=None, original_text="Salin"):
        """Menyalin teks ke clipboard sistem dan mengubah status tombol untuk konfirmasi visual."""
        if not text or text.startswith("Hasil ") or text.startswith("Tempel "):
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        if button:
            orig_bg = button.cget("fg_color")
            button.configure(text="Tersalin! ✓", fg_color=AppTheme.COLOR_EMERALD)
            self.root.after(1500, lambda: button.configure(text=original_text, fg_color=orig_bg))

    def open_folder(self, folder):
        """Membuka direktori terpilih menggunakan file explorer sistem bawaan OS secara aman."""
        if not folder or not os.path.exists(folder):
            return
        try:
            if hasattr(os, "startfile"):
                os.startfile(folder)
            else:
                import platform
                system = platform.system()
                if system == "Darwin":
                    import subprocess
                    subprocess.Popen(["open", folder])
                else:
                    import subprocess
                    subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membuka folder: {e}")

    def show_help_info(self, title, message):
        """Menampilkan jendela informasi bantuan modern."""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry("420x240")
        dialog.resizable(False, False)
        dialog.transient(self.root) # Selalu di atas window utama
        dialog.grab_set() # Blokir interaksi window utama
        
        # Center the dialog on root window
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 210
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 120
        dialog.geometry(f"+{x}+{y}")
        
        dialog.configure(fg_color=AppTheme.BG_PRIMARY)
        
        pad_frame = ctk.CTkFrame(dialog, fg_color=AppTheme.BG_PRIMARY, corner_radius=0)
        pad_frame.pack(fill="both", expand=True, padx=AppTheme.PAD_SM, pady=AppTheme.PAD_SM)
        
        lbl_title = ctk.CTkLabel(pad_frame, text=title.upper(), text_color=AppTheme.COLOR_TEAL, font=AppTheme.FONT_LG, anchor="w")
        lbl_title.pack(fill="x", pady=(AppTheme.PAD_NONE, AppTheme.PAD_XS))
        
        lbl_msg = ctk.CTkLabel(pad_frame, text=message, text_color=AppTheme.TEXT_MAIN, font=AppTheme.FONT_SM, justify="left", anchor="w", wraplength=380)
        lbl_msg.pack(fill="both", expand=True, pady=(AppTheme.PAD_NONE, AppTheme.PAD_SM))
        
        btn_close = self.create_custom_button(
            pad_frame,
            text="TUTUP",
            command=dialog.destroy,
            bg_color=AppTheme.BG_PRIMARY,
            hover_bg=AppTheme.BORDER_COLOR,
            font=AppTheme.FONT_SM_BOLD,
            height=32
        )
        btn_close.pack(anchor="e")

    def import_txt_file(self, text_widget, on_change_callback):
        """Membuka file dialog untuk memilih berkas .txt dan menampilkan isinya di input area."""
        path = filedialog.askopenfilename(
            title="Pilih File Teks (.txt)",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            text_widget.configure(state="normal")
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", content)
            text_widget.configure(text_color=AppTheme.TEXT_MAIN)
            if on_change_callback:
                on_change_callback()
            self.update_status(f"File {os.path.basename(path)} berhasil dimuat", "success")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membaca file: {e}")
            self.update_status("Gagal memuat file", "error")

    def export_txt_file(self, text_widget, suggested_filename):
        """Menyimpan konten dari widget text ke dalam berkas .txt."""
        content = text_widget.get("1.0", tk.END).strip()
        if not content or content in (
            "Hasil enkripsi (Base64) akan muncul di sini...",
            "Hasil dekripsi akan muncul di sini...",
            "Tempel atau ketik pesan di sini...",
            "Tempel ciphertext Base64 di sini..."
        ):
            messagebox.showwarning("Peringatan", "Tidak ada konten valid untuk disimpan!")
            return
            
        path = filedialog.asksaveasfilename(
            title="Simpan File Sebagai",
            initialfile=suggested_filename,
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Sukses", f"Berhasil menyimpan file ke:\n{path}")
            self.update_status("File berhasil disimpan", "success")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan file: {e}")
            self.update_status("Gagal menyimpan file", "error")

    def on_encrypt_text_change(self, event=None):
        """Menghitung karakter pesan plaintext secara real-time."""
        text = self.enc_msg_input.get("1.0", tk.END).strip()
        if text == "Tempel atau ketik pesan di sini...":
            self.enc_char_count_lbl.configure(text="Karakter: 0")
        else:
            self.enc_char_count_lbl.configure(text=f"Karakter: {len(text)}")
        self.update_all_action_buttons_state()

    def update_detected_badge(self, text, bg_color):
        """Memperbarui visual badge pendeteksi metode enkripsi."""
        if hasattr(self, "detected_badge") and hasattr(self, "detected_badge_frame"):
            self.detected_badge.configure(text=text, fg_color=bg_color)
            self.detected_badge_frame.configure(fg_color=bg_color)

    # ==========================================
    # MULTITHREADING TASK RUNNER
    # ==========================================
    def run_task_in_background(self, target_func, on_success_func, on_error_func, status_text, trigger_button=None, processing_text="Memproses..."):
        """Menjalankan fungsi kalkulasi asinkronus, menampilkan progress bar, dan memblokir input sementara."""
        self.is_processing = True
        self.set_widgets_state(self.content_container, "disabled")
        
        if trigger_button:
            self.active_trigger_button = trigger_button
            self.active_trigger_button_original_text = trigger_button.cget("text")
            trigger_button.configure(text=processing_text, state="disabled")
        else:
            self.active_trigger_button = None
            self.active_trigger_button_original_text = ""
            
        self.progress_bar.start()
        self.progress_bar.pack(side="right", padx=AppTheme.PAD_SM, pady=AppTheme.PAD_XS)
        self.update_status(status_text, "processing")
        
        def worker():
            try:
                result = target_func()
                self.root.after(0, lambda r=result: self.finish_task(True, r, on_success_func, on_error_func))
            except Exception as e:
                self.root.after(0, lambda err=e: self.finish_task(False, err, on_success_func, on_error_func))
                
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def finish_task(self, success, result, on_success, on_error):
        """Mematikan progress bar, melepas blokir input, dan mengeksekusi callback pasca-proses selesai."""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.update_status("Ready", "success")
        self.set_widgets_state(self.content_container, "normal")
        
        if getattr(self, "active_trigger_button", None):
            try:
                self.active_trigger_button.configure(text=self.active_trigger_button_original_text, state="normal")
            except Exception:
                pass
            self.active_trigger_button = None
            
        self.is_processing = False
        self.update_all_action_buttons_state()
        
        if success:
            on_success(result)
        else:
            on_error(result)

    def set_widgets_state(self, container, state):
        """Mengubah status input aktif agar tidak dapat diklik berganda saat proses background berjalan."""
        for child in container.winfo_children():
            widget_class = child.winfo_class()
            if hasattr(child, "configure"):
                if "CTkButton" in widget_class or "CTkRadioButton" in widget_class:
                    try:
                        child.configure(state=state)
                    except Exception:
                        pass
                elif "CTkEntry" in widget_class:
                    if child in self.read_only_widgets:
                        target_state = "disabled" if state == "disabled" else "readonly"
                    else:
                        target_state = state
                    try:
                        child.configure(state=target_state)
                    except Exception:
                        pass
                elif "CTkTextbox" in widget_class:
                    if child not in self.read_only_widgets:
                        try:
                            child.configure(state=state)
                        except Exception:
                            pass
            # Rekursi ke anak widget di dalamnya
            self.set_widgets_state(child, state)

    # ==========================================
    # METODE COMPATIBILITY UNTUK EKSTERNAL RUNNER
    # ==========================================
    def gui_generate_keys(self):
        self.select_view("key_gen")

    def gui_encrypt_message(self):
        self.select_view("encrypt")
        self.toggle_encrypt_subview("message")

    def gui_decrypt_message(self):
        self.select_view("decrypt")
        self.toggle_decrypt_subview("message")

    def gui_encrypt_file(self):
        self.select_view("encrypt")
        self.toggle_encrypt_subview("file")

    def gui_decrypt_file(self):
        self.select_view("decrypt")
        self.toggle_decrypt_subview("file")
