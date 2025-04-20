import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import serial
import threading
import time
from datetime import datetime

class SiparisTakipSistemi:
    def __init__(self, root):
        self.root = root
        self.root.title("Sipariş Takip Sistemi")
        self.root.geometry("1024x768")
        
        # Tema ve stil ayarları
        self.style = ttk.Style()
        self.style.theme_use('clam')  
        
        # Özel renkler ve stiller
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Helvetica', 10))
        self.style.configure('TButton', font=('Helvetica', 10))
        self.style.configure('Header.TLabel', font=('Helvetica', 16, 'bold'))
        self.style.configure('Subheader.TLabel', font=('Helvetica', 12, 'bold'))
        self.style.configure('Money.TLabel', font=('Helvetica', 14, 'bold'), foreground='green')
        
        # Veritabanı bağlantısı
        self.conn = sqlite3.connect('siparis_takip.db')
        self.create_tables()
        
        # Seri port ayarları
        self.serial_ports = {
            'hat1': None,
            'hat2': None,
            'hat3': None
        }
        
        # Ana container
        self.main_container = ttk.Frame(root, padding="20")
        self.main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Başlık
        self.header_frame = ttk.Frame(self.main_container)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Label(self.header_frame, text="Sipariş Takip Sistemi", 
                 style='Header.TLabel').grid(row=0, column=0, sticky=tk.W)
        
        # Durum çubuğu
        self.status_frame = ttk.Frame(self.main_container)
        self.status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(self.status_frame, text="Sistem Hazır", 
                                    style='TLabel')
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Sekmeler
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Sekmeleri oluştur
        self.create_arayan_tab()
        self.create_musteri_tab()
        self.create_urun_tab()
        self.create_siparis_tab()
        self.create_gunluk_rapor_tab()
        
        # Grid yapılandırması
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.main_container.columnconfigure(1, weight=1)
        self.main_container.rowconfigure(2, weight=1)
        
        # Seri port bağlantılarını başlat
        self.start_serial_connections()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Müşteriler tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS musteriler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telefon TEXT UNIQUE,
            ad TEXT,
            adres TEXT,
            kayit_tarihi DATETIME
        )
        ''')
        
        # Ürünler tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS urunler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT UNIQUE,
            fiyat REAL
        )
        ''')
        
        # Siparişler tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS siparisler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            musteri_id INTEGER,
            urun_id INTEGER,
            tarih DATETIME,
            FOREIGN KEY (musteri_id) REFERENCES musteriler (id),
            FOREIGN KEY (urun_id) REFERENCES urunler (id)
        )
        ''')
        
        self.conn.commit()
    
    def create_arayan_tab(self):
        arayan_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(arayan_frame, text="Arayanlar")
        
        # Sol panel - Arayan bilgileri
        left_panel = ttk.Frame(arayan_frame)
        left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Arayan bilgileri
        ttk.Label(left_panel, text="Arayan Bilgileri", 
                 style='Subheader.TLabel').grid(row=0, column=0, pady=(0, 10))
        
        self.arayan_label = ttk.Label(left_panel, text="Arayan Numara: ", 
                                    style='TLabel')
        self.arayan_label.grid(row=1, column=0, pady=5)
        
        # Müşteri bilgileri
        musteri_frame = ttk.LabelFrame(left_panel, text="Müşteri Bilgileri", padding="10")
        musteri_frame.grid(row=2, column=0, pady=10, sticky=(tk.W, tk.E))
        
        # Yeni müşteri formu
        ttk.Label(musteri_frame, text="Ad:").grid(row=0, column=0, pady=5, padx=5)
        self.yeni_ad = ttk.Entry(musteri_frame, width=30)
        self.yeni_ad.grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(musteri_frame, text="Telefon:").grid(row=1, column=0, pady=5, padx=5)
        self.yeni_telefon = ttk.Entry(musteri_frame, width=30)
        self.yeni_telefon.grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Label(musteri_frame, text="Adres:").grid(row=2, column=0, pady=5, padx=5)
        self.yeni_adres = ttk.Entry(musteri_frame, width=30)
        self.yeni_adres.grid(row=2, column=1, pady=5, padx=5)
        
        ttk.Button(musteri_frame, text="Yeni Müşteri Kaydet", 
                  command=self.yeni_musteri_kaydet).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Sağ panel - Sipariş ekleme
        right_panel = ttk.Frame(arayan_frame)
        right_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Sipariş ekleme
        siparis_frame = ttk.LabelFrame(right_panel, text="Sipariş Ekle", padding="10")
        siparis_frame.grid(row=0, column=0, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(siparis_frame, text="Müşteri:").grid(row=0, column=0, pady=5, padx=5)
        self.musteri_combo = ttk.Combobox(siparis_frame, width=30)
        self.musteri_combo.grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(siparis_frame, text="Ürün:").grid(row=1, column=0, pady=5, padx=5)
        self.urun_combo = ttk.Combobox(siparis_frame, width=30)
        self.urun_combo.grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Button(siparis_frame, text="Sipariş Ekle", 
                  command=self.siparis_ekle).grid(row=2, column=0, columnspan=2, pady=10)
        
        # Grid yapılandırması
        arayan_frame.columnconfigure(1, weight=1)
        arayan_frame.rowconfigure(0, weight=1)
    
    def create_musteri_tab(self):
        musteri_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(musteri_frame, text="Müşteriler")
        
        # Başlık
        ttk.Label(musteri_frame, text="Müşteri Listesi", 
                 style='Subheader.TLabel').grid(row=0, column=0, pady=(0, 10))
        
        # Müşteri listesi
        self.musteri_tree = ttk.Treeview(musteri_frame, 
                                       columns=("telefon", "ad", "adres", "kayit_tarihi"),
                                       show='headings')
        
        # Sütun başlıkları
        self.musteri_tree.heading("telefon", text="Telefon")
        self.musteri_tree.heading("ad", text="Ad")
        self.musteri_tree.heading("adres", text="Adres")
        self.musteri_tree.heading("kayit_tarihi", text="Kayıt Tarihi")
        
        # Sütun genişlikleri
        self.musteri_tree.column("telefon", width=120)
        self.musteri_tree.column("ad", width=150)
        self.musteri_tree.column("adres", width=300)
        self.musteri_tree.column("kayit_tarihi", width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(musteri_frame, orient=tk.VERTICAL, 
                                command=self.musteri_tree.yview)
        self.musteri_tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid
        self.musteri_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # Grid yapılandırması
        musteri_frame.columnconfigure(0, weight=1)
        musteri_frame.rowconfigure(1, weight=1)
        
        self.musteri_listesi_guncelle()
    
    def create_urun_tab(self):
        urun_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(urun_frame, text="Ürünler")
        
        # Sol panel - Ürün ekleme
        left_panel = ttk.Frame(urun_frame)
        left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        ttk.Label(left_panel, text="Yeni Ürün Ekle", 
                 style='Subheader.TLabel').grid(row=0, column=0, pady=(0, 10))
        
        # Ürün ekleme formu
        form_frame = ttk.LabelFrame(left_panel, text="Ürün Bilgileri", padding="10")
        form_frame.grid(row=1, column=0, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(form_frame, text="Ürün Adı:").grid(row=0, column=0, pady=5, padx=5)
        self.urun_adi = ttk.Entry(form_frame, width=30)
        self.urun_adi.grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Fiyat:").grid(row=1, column=0, pady=5, padx=5)
        self.urun_fiyat = ttk.Entry(form_frame, width=30)
        self.urun_fiyat.grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Button(form_frame, text="Ürün Ekle", 
                  command=self.urun_ekle).grid(row=2, column=0, columnspan=2, pady=10)
        
        # Sağ panel - Ürün listesi
        right_panel = ttk.Frame(urun_frame)
        right_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(right_panel, text="Ürün Listesi", 
                 style='Subheader.TLabel').grid(row=0, column=0, pady=(0, 10))
        
        # Ürün listesi
        self.urun_tree = ttk.Treeview(right_panel, columns=("ad", "fiyat"),
                                    show='headings')
        
        # Sütun başlıkları
        self.urun_tree.heading("ad", text="Ürün Adı")
        self.urun_tree.heading("fiyat", text="Fiyat")
        
        # Sütun genişlikleri
        self.urun_tree.column("ad", width=200)
        self.urun_tree.column("fiyat", width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(right_panel, orient=tk.VERTICAL, 
                                command=self.urun_tree.yview)
        self.urun_tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid
        self.urun_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # Grid yapılandırması
        urun_frame.columnconfigure(1, weight=1)
        urun_frame.rowconfigure(0, weight=1)
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)
        
        self.urun_listesi_guncelle()
    
    def create_siparis_tab(self):
        siparis_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(siparis_frame, text="Siparişler")
        
        # Başlık
        ttk.Label(siparis_frame, text="Sipariş Listesi", 
                 style='Subheader.TLabel').grid(row=0, column=0, pady=(0, 10))
        
        # Sipariş listesi
        self.siparis_tree = ttk.Treeview(siparis_frame, 
                                       columns=("musteri", "urun", "tarih"),
                                       show='headings')
        
        # Sütun başlıkları
        self.siparis_tree.heading("musteri", text="Müşteri")
        self.siparis_tree.heading("urun", text="Ürün")
        self.siparis_tree.heading("tarih", text="Tarih")
        
        # Sütun genişlikleri
        self.siparis_tree.column("musteri", width=150)
        self.siparis_tree.column("urun", width=200)
        self.siparis_tree.column("tarih", width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(siparis_frame, orient=tk.VERTICAL, 
                                command=self.siparis_tree.yview)
        self.siparis_tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid
        self.siparis_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # Grid yapılandırması
        siparis_frame.columnconfigure(0, weight=1)
        siparis_frame.rowconfigure(1, weight=1)
        
        self.siparis_listesi_guncelle()
    
    def create_gunluk_rapor_tab(self):
        rapor_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(rapor_frame, text="Günlük Rapor")
        
        # Üst panel - Özet bilgiler
        ust_panel = ttk.Frame(rapor_frame)
        ust_panel.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Günlük toplam kazanç
        self.gunluk_kazanc_label = ttk.Label(ust_panel, text="Günlük Toplam Kazanç: 0.00 TL", 
                                           style='Money.TLabel')
        self.gunluk_kazanc_label.grid(row=0, column=0, padx=20)
        
        # Toplam sipariş sayısı
        self.gunluk_siparis_label = ttk.Label(ust_panel, text="Günlük Toplam Sipariş: 0", 
                                            style='TLabel')
        self.gunluk_siparis_label.grid(row=0, column=1, padx=20)
        
        # Ürün bazlı satış detayları
        ttk.Label(rapor_frame, text="Ürün Bazlı Satış Detayları", 
                 style='Subheader.TLabel').grid(row=1, column=0, pady=(0, 10))
        
        # Ürün satış listesi
        self.urun_satis_tree = ttk.Treeview(rapor_frame, 
                                          columns=("urun", "adet", "toplam_gelir"),
                                          show='headings')
        
        # Sütun başlıkları
        self.urun_satis_tree.heading("urun", text="Ürün Adı")
        self.urun_satis_tree.heading("adet", text="Satış Adedi")
        self.urun_satis_tree.heading("toplam_gelir", text="Toplam Gelir")
        
        # Sütun genişlikleri
        self.urun_satis_tree.column("urun", width=200)
        self.urun_satis_tree.column("adet", width=100)
        self.urun_satis_tree.column("toplam_gelir", width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(rapor_frame, orient=tk.VERTICAL, 
                                command=self.urun_satis_tree.yview)
        self.urun_satis_tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid
        self.urun_satis_tree.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=2, column=1, sticky=(tk.N, tk.S))
        
        # Yenile butonu
        ttk.Button(rapor_frame, text="Raporu Yenile", 
                  command=self.gunluk_rapor_guncelle).grid(row=3, column=0, pady=10)
        
        # Grid yapılandırması
        rapor_frame.columnconfigure(0, weight=1)
        rapor_frame.rowconfigure(2, weight=1)
        
        # İlk raporu oluştur
        self.gunluk_rapor_guncelle()
    
    def start_serial_connections(self):
        try:
            # Her hat için seri port bağlantısı
            for i, port in enumerate(['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2'], 1):
                try:
                    self.serial_ports[f'hat{i}'] = serial.Serial(
                        port=port,
                        baudrate=9600,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        timeout=1
                    )
                    # Her hat için ayrı thread başlat
                    thread = threading.Thread(target=self.read_serial, args=(f'hat{i}',))
                    thread.daemon = True
                    thread.start()
                except serial.SerialException as e:
                    print(f"Hat {i} bağlantı hatası: {str(e)}")
        except Exception as e:
            print(f"Seri port bağlantı hatası: {str(e)}")
    
    def read_serial(self, hat):
        while True:
            try:
                if self.serial_ports[hat] and self.serial_ports[hat].is_open:
                    data = self.serial_ports[hat].readline().decode('utf-8').strip()
                    if data:
                        # Arayan numarayı işle
                        self.root.after(0, self.arayan_numara_geldi, data)
            except Exception as e:
                print(f"{hat} okuma hatası: {str(e)}")
            time.sleep(0.1)
    
    def arayan_numara_geldi(self, numara):
        self.arayan_label.config(text=f"Arayan Numara: {numara}")
        # Telefon numarasını otomatik olarak doldur
        self.yeni_telefon.delete(0, tk.END)
        self.yeni_telefon.insert(0, numara)
        
        # Müşteri kontrolü
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM musteriler WHERE telefon = ?", (numara,))
        musteri = cursor.fetchone()
        
        if musteri:
            messagebox.showinfo("Müşteri Bilgisi", 
                              f"Müşteri: {musteri[2]}\nAdres: {musteri[3]}")
            # Müşteri combobox'ını güncelle ve seç
            self.musteri_combo_guncelle()
            self.musteri_combo.set(f"{musteri[2]} ({musteri[1]})")
        else:
            if messagebox.askyesno("Yeni Müşteri", 
                                 "Bu numara kayıtlı değil. Yeni müşteri olarak kaydetmek ister misiniz?"):
                self.yeni_musteri_pencere(numara)
    
    def yeni_musteri_pencere(self, numara):
        # Yeni müşteri bilgilerini al
        self.yeni_ad.delete(0, tk.END)
        self.yeni_telefon.delete(0, tk.END)
        self.yeni_telefon.insert(0, numara)
        self.yeni_adres.delete(0, tk.END)
        self.notebook.select(0)  # Arayanlar sekmesine geç
    
    def yeni_musteri_kaydet(self):
        ad = self.yeni_ad.get()
        telefon = self.yeni_telefon.get()
        adres = self.yeni_adres.get()
        
        if ad and telefon and adres:
            cursor = self.conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO musteriler (telefon, ad, adres, kayit_tarihi)
                    VALUES (?, ?, ?, ?)
                """, (telefon, ad, adres, datetime.now()))
                self.conn.commit()
                
                self.musteri_listesi_guncelle()
                messagebox.showinfo("Başarılı", "Müşteri kaydedildi!")
            except sqlite3.IntegrityError:
                messagebox.showerror("Hata", "Bu telefon numarası zaten kayıtlı!")
        else:
            messagebox.showerror("Hata", "Lütfen tüm alanları doldurun!")
    
    def urun_ekle(self):
        ad = self.urun_adi.get()
        fiyat = self.urun_fiyat.get()
        
        if ad and fiyat:
            try:
                fiyat = float(fiyat)
                cursor = self.conn.cursor()
                cursor.execute("INSERT INTO urunler (ad, fiyat) VALUES (?, ?)", (ad, fiyat))
                self.conn.commit()
                
                self.urun_listesi_guncelle()
                self.urun_combo_guncelle()
                messagebox.showinfo("Başarılı", "Ürün eklendi!")
            except ValueError:
                messagebox.showerror("Hata", "Geçerli bir fiyat girin!")
        else:
            messagebox.showerror("Hata", "Lütfen tüm alanları doldurun!")
    
    def siparis_ekle(self):
        musteri_secim = self.musteri_combo.get()
        urun = self.urun_combo.get()
        
        if musteri_secim and urun:
            # Müşteri telefonunu parantez içinden al
            telefon = musteri_secim.split("(")[1].strip(")")
            
            cursor = self.conn.cursor()
            # Müşteri ID'sini al
            cursor.execute("SELECT id FROM musteriler WHERE telefon = ?", (telefon,))
            musteri = cursor.fetchone()
            
            if musteri:
                # Ürün ID'sini al
                cursor.execute("SELECT id FROM urunler WHERE ad = ?", (urun,))
                urun_id = cursor.fetchone()[0]
                
                # Siparişi kaydet
                cursor.execute("""
                    INSERT INTO siparisler (musteri_id, urun_id, tarih)
                    VALUES (?, ?, ?)
                """, (musteri[0], urun_id, datetime.now()))
                self.conn.commit()
                
                self.siparis_listesi_guncelle()
                messagebox.showinfo("Başarılı", "Sipariş eklendi!")
            else:
                messagebox.showerror("Hata", "Müşteri bulunamadı!")
        else:
            messagebox.showerror("Hata", "Lütfen müşteri ve ürün seçin!")
    
    def musteri_listesi_guncelle(self):
        # Mevcut listeyi temizle
        for item in self.musteri_tree.get_children():
            self.musteri_tree.delete(item)
        
        # Müşterileri getir ve listele
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM musteriler")
        for musteri in cursor.fetchall():
            self.musteri_tree.insert("", "end", values=musteri[1:])
        
        # Müşteri combobox'ını güncelle
        self.musteri_combo_guncelle()
    
    def urun_listesi_guncelle(self):
        # Mevcut listeyi temizle
        for item in self.urun_tree.get_children():
            self.urun_tree.delete(item)
        
        # Ürünleri getir ve listele
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM urunler")
        for urun in cursor.fetchall():
            self.urun_tree.insert("", "end", values=urun[1:])
        
        # Ürün combobox'ını güncelle
        self.urun_combo_guncelle()
    
    def urun_combo_guncelle(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT ad FROM urunler")
        urunler = [urun[0] for urun in cursor.fetchall()]
        self.urun_combo['values'] = urunler
    
    def siparis_listesi_guncelle(self):
        # Mevcut listeyi temizle
        for item in self.siparis_tree.get_children():
            self.siparis_tree.delete(item)
        
        # Siparişleri getir ve listele
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.ad, u.ad, s.tarih
            FROM siparisler s
            JOIN musteriler m ON s.musteri_id = m.id
            JOIN urunler u ON s.urun_id = u.id
            ORDER BY s.tarih DESC
        """)
        for siparis in cursor.fetchall():
            self.siparis_tree.insert("", "end", values=siparis)
    
    def musteri_combo_guncelle(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT ad, telefon FROM musteriler")
        musteriler = [f"{musteri[0]} ({musteri[1]})" for musteri in cursor.fetchall()]
        self.musteri_combo['values'] = musteriler
    
    def gunluk_rapor_guncelle(self):
        # Mevcut listeyi temizle
        for item in self.urun_satis_tree.get_children():
            self.urun_satis_tree.delete(item)
        
        # Bugünün tarihini al
        bugun = datetime.now().strftime('%Y-%m-%d')
        
        cursor = self.conn.cursor()
        
        # Günlük toplam kazancı hesapla
        cursor.execute("""
            SELECT SUM(u.fiyat) as toplam_kazanc, COUNT(*) as siparis_sayisi
            FROM siparisler s
            JOIN urunler u ON s.urun_id = u.id
            WHERE DATE(s.tarih) = ?
        """, (bugun,))
        
        sonuc = cursor.fetchone()
        toplam_kazanc = sonuc[0] if sonuc[0] else 0
        siparis_sayisi = sonuc[1] if sonuc[1] else 0
        
        # Etiketleri güncelle
        self.gunluk_kazanc_label.config(text=f"Günlük Toplam Kazanç: {toplam_kazanc:.2f} TL")
        self.gunluk_siparis_label.config(text=f"Günlük Toplam Sipariş: {siparis_sayisi}")
        
        # Ürün bazlı satış detaylarını getir
        cursor.execute("""
            SELECT u.ad, COUNT(*) as adet, SUM(u.fiyat) as toplam_gelir
            FROM siparisler s
            JOIN urunler u ON s.urun_id = u.id
            WHERE DATE(s.tarih) = ?
            GROUP BY u.id, u.ad
            ORDER BY toplam_gelir DESC
        """, (bugun,))
        
        for urun in cursor.fetchall():
            self.urun_satis_tree.insert("", "end", values=(
                urun[0],  # Ürün adı
                urun[1],  # Satış adedi
                f"{urun[2]:.2f} TL"  # Toplam gelir
            ))

if __name__ == "__main__":
    root = tk.Tk()
    app = SiparisTakipSistemi(root)
    root.mainloop() 