import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import subprocess
import os
import sys
import threading
from datetime import datetime, timedelta

# 'pip install tkcalendar' gereklidir
from tkcalendar import DateEntry 

class GitAnalyzerApp:
    # Modern Renk Paleti
    COLORS = {
        'bg_dark': '#1a1b26',           # Ana arka plan (koyu)
        'bg_card': '#24283b',           # Kart arka planı
        'bg_hover': '#414868',          # Hover durumu
        'accent': '#7aa2f7',            # Ana vurgu rengi (mavi)
        'accent_green': '#9ece6a',      # Yeşil vurgu
        'accent_red': '#f7768e',        # Kırmızı vurgu  
        'accent_orange': '#ff9e64',     # Turuncu vurgu
        'accent_purple': '#bb9af7',     # Mor vurgu
        'accent_cyan': '#7dcfff',       # Cyan vurgu
        'text_primary': '#e0e4f7',      # Ana metin (daha parlak)
        'text_secondary': '#a9b1d6',    # İkincil metin (daha görünür)
        'text_bright': '#ffffff',       # Parlak metin
        'text_muted': '#787c99',        # Soluk metin (eskisi)
        'border': '#3b4261',            # Kenarlık rengi
        'success': '#73daca',           # Başarı rengi
        'warning': '#e0af68',           # Uyarı rengi
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Git Analiz Pro")
        self.root.geometry("1300x950")
        self.root.configure(bg=self.COLORS['bg_dark'])
        
        # Minimum boyut ayarla
        self.root.minsize(1100, 800)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Global değişkenler
        self.current_repo_path = ""
        self.tree = None
        self.df = None
        self.filtered_df = None
        self.popup_commit_hash = ""

        # Modern Stil Ayarları
        self.setup_modern_styles()

        # --- HEADER PANEL ---
        self.create_header()

        # --- ÜST PANEL (Kontroller) ---
        self.create_control_panel()

        # --- ALT PANEL ---
        self.frame_bottom = tk.Frame(root, bg=self.COLORS['bg_dark'])
        self.frame_bottom.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        self.notebook = None

    def setup_modern_styles(self):
        """Modern ttk stilleri oluştur"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Notebook (Tab) Stili
        self.style.configure("TNotebook", 
                           background=self.COLORS['bg_dark'],
                           borderwidth=0)
        self.style.configure("TNotebook.Tab",
                           background=self.COLORS['bg_hover'],
                           foreground=self.COLORS['text_bright'],
                           padding=[22, 14],
                           font=('Segoe UI', 10, 'bold'))
        self.style.map("TNotebook.Tab",
                      background=[('selected', self.COLORS['accent']),
                                ('active', self.COLORS['accent_purple'])],
                      foreground=[('selected', self.COLORS['bg_dark']),
                                ('active', self.COLORS['text_bright'])])

        # Treeview Stili
        self.style.configure("Modern.Treeview",
                           background=self.COLORS['bg_card'],
                           foreground=self.COLORS['text_bright'],
                           fieldbackground=self.COLORS['bg_card'],
                           rowheight=34,
                           borderwidth=0,
                           font=('Segoe UI', 10))
        self.style.configure("Modern.Treeview.Heading",
                           background=self.COLORS['accent'],
                           foreground=self.COLORS['bg_dark'],
                           font=('Segoe UI', 10, 'bold'),
                           padding=[12, 10])
        self.style.map('Modern.Treeview',
                      background=[('selected', self.COLORS['accent'])],
                      foreground=[('selected', self.COLORS['bg_dark'])])

        # Combobox Stili
        self.style.configure("Modern.TCombobox",
                           background=self.COLORS['bg_hover'],
                           foreground=self.COLORS['text_bright'],
                           fieldbackground=self.COLORS['bg_hover'],
                           arrowcolor=self.COLORS['accent'],
                           padding=10,
                           font=('Segoe UI', 10))
        self.style.map('Modern.TCombobox',
                      fieldbackground=[('readonly', self.COLORS['bg_hover'])],
                      foreground=[('readonly', self.COLORS['text_bright'])],
                      selectbackground=[('readonly', self.COLORS['accent'])])

        # Progressbar Stili
        self.style.configure("Modern.Horizontal.TProgressbar",
                           background=self.COLORS['accent'],
                           troughcolor=self.COLORS['bg_card'],
                           borderwidth=0,
                           lightcolor=self.COLORS['accent'],
                           darkcolor=self.COLORS['accent'])

        # Scrollbar Stili
        self.style.configure("Modern.Vertical.TScrollbar",
                           background=self.COLORS['bg_hover'],
                           troughcolor=self.COLORS['bg_card'],
                           borderwidth=0,
                           arrowcolor=self.COLORS['text_primary'])

    def create_header(self):
        """Başlık paneli oluştur"""
        header = tk.Frame(self.root, bg=self.COLORS['bg_card'], height=70)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)

        # Logo ve Başlık
        title_frame = tk.Frame(header, bg=self.COLORS['bg_card'])
        title_frame.pack(side=tk.LEFT, padx=25, pady=15)

        logo_label = tk.Label(title_frame, 
                             text="◈", 
                             font=('Segoe UI', 24),
                             fg=self.COLORS['accent'],
                             bg=self.COLORS['bg_card'])
        logo_label.pack(side=tk.LEFT, padx=(0, 10))

        title_label = tk.Label(title_frame, 
                              text="Git Analiz Pro",
                              font=('Segoe UI', 18, 'bold'),
                              fg=self.COLORS['text_bright'],
                              bg=self.COLORS['bg_card'])
        title_label.pack(side=tk.LEFT)

        subtitle_label = tk.Label(title_frame,
                                 text="v2.0",
                                 font=('Segoe UI', 10, 'bold'),
                                 fg=self.COLORS['accent_cyan'],
                                 bg=self.COLORS['bg_card'])
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0), pady=(8, 0))

    def create_control_panel(self):
        """Modern kontrol paneli oluştur"""
        # Ana kontrol çerçevesi
        control_wrapper = tk.Frame(self.root, bg=self.COLORS['bg_dark'])
        control_wrapper.pack(side=tk.TOP, fill=tk.X, padx=20, pady=20)

        # Sol Panel - Ayarlar Kartı
        settings_card = tk.Frame(control_wrapper, bg=self.COLORS['bg_card'], padx=25, pady=20)
        settings_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Kart başlığı
        card_title = tk.Label(settings_card,
                             text="⚙ Analiz Ayarları",
                             font=('Segoe UI', 12, 'bold'),
                             fg=self.COLORS['accent'],
                             bg=self.COLORS['bg_card'])
        card_title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 15))

        # 1. Klasör Seçimi
        self.create_label(settings_card, "Proje Klasörü", 1, 0)
        
        path_frame = tk.Frame(settings_card, bg=self.COLORS['bg_card'])
        path_frame.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5)
        
        self.entry_path = tk.Entry(path_frame, 
                                  width=45,
                                  font=('Consolas', 10),
                                  bg=self.COLORS['bg_hover'],
                                  fg=self.COLORS['text_bright'],
                                  insertbackground=self.COLORS['accent'],
                                  relief='flat',
                                  highlightthickness=2,
                                  highlightbackground=self.COLORS['border'],
                                  highlightcolor=self.COLORS['accent'])
        self.entry_path.pack(side=tk.LEFT, padx=(0, 10), ipady=8)
        
        btn_browse = self.create_button(path_frame, "📂 Gözat", self.select_folder_async, 'secondary')
        btn_browse.pack(side=tk.LEFT)

        # 2. Branch Seçimi
        self.create_label(settings_card, "Branch", 2, 0)
        self.branch_combo = ttk.Combobox(settings_card, 
                                        width=43, 
                                        state="readonly",
                                        style="Modern.TCombobox",
                                        font=('Segoe UI', 10))
        self.branch_combo.grid(row=2, column=1, columnspan=2, sticky="w", pady=5, ipady=5)
        self.branch_combo.set("Önce klasör seçiniz...")

        # 3. Tarih Aralığı
        today = datetime.now()

        self.create_label(settings_card, "Başlangıç", 3, 0)
        self.entry_start = DateEntry(settings_card, 
                                    width=18, 
                                    background=self.COLORS['accent'],
                                    foreground=self.COLORS['bg_dark'], 
                                    borderwidth=0, 
                                    date_pattern='yyyy-mm-dd',
                                    font=('Segoe UI', 10))
        self.entry_start.set_date(today) 
        self.entry_start.grid(row=3, column=1, sticky="w", pady=5, ipady=3)

        self.create_label(settings_card, "Bitiş", 4, 0)
        self.entry_end = DateEntry(settings_card, 
                                  width=18, 
                                  background=self.COLORS['accent'],
                                  foreground=self.COLORS['bg_dark'], 
                                  borderwidth=0, 
                                  date_pattern='yyyy-mm-dd',
                                  font=('Segoe UI', 10))
        self.entry_end.set_date(today)
        self.entry_end.grid(row=4, column=1, sticky="w", pady=5, ipady=3)

        # Sağ Panel - Analiz Butonu
        action_card = tk.Frame(control_wrapper, bg=self.COLORS['bg_card'], padx=30, pady=20)
        action_card.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))

        action_title = tk.Label(action_card,
                               text="🚀 Başlat",
                               font=('Segoe UI', 12, 'bold'),
                               fg=self.COLORS['accent_green'],
                               bg=self.COLORS['bg_card'])
        action_title.pack(pady=(0, 15))

        self.btn_analyze = self.create_button(action_card, "ANALİZ ET", self.start_analysis_thread, 'primary', large=True)
        self.btn_analyze.pack(pady=10, ipadx=25, ipady=12)

        # Progress Bar
        self.main_progress = ttk.Progressbar(action_card, 
                                            orient=tk.HORIZONTAL, 
                                            length=160, 
                                            mode='indeterminate',
                                            style="Modern.Horizontal.TProgressbar")
        self.main_progress.pack(pady=10)
        self.main_progress.pack_forget()

    def create_label(self, parent, text, row, col):
        """Stil uygulanmış etiket oluştur"""
        lbl = tk.Label(parent,
                      text=text,
                      font=('Segoe UI', 10, 'bold'),
                      fg=self.COLORS['text_primary'],
                      bg=self.COLORS['bg_card'])
        lbl.grid(row=row, column=col, sticky="e", padx=(0, 15), pady=5)
        return lbl

    def create_button(self, parent, text, command, style='primary', large=False):
        """Modern stil buton oluştur"""
        if style == 'primary':
            bg = self.COLORS['accent_green']
            fg = self.COLORS['bg_dark']
            hover_bg = '#a9db7a'
        elif style == 'secondary':
            bg = self.COLORS['accent']
            fg = self.COLORS['bg_dark']
            hover_bg = '#8fb4f8'
        elif style == 'danger':
            bg = self.COLORS['accent_red']
            fg = self.COLORS['text_bright']
            hover_bg = '#f8929f'
        else:
            bg = self.COLORS['bg_hover']
            fg = self.COLORS['text_primary']
            hover_bg = self.COLORS['border']

        font_size = 12 if large else 9
        
        btn = tk.Button(parent,
                       text=text,
                       command=command,
                       font=('Segoe UI', font_size, 'bold'),
                       bg=bg,
                       fg=fg,
                       activebackground=hover_bg,
                       activeforeground=fg,
                       relief='flat',
                       cursor='hand2',
                       padx=15,
                       pady=5)
        
        # Hover efekti
        btn.bind('<Enter>', lambda e: btn.configure(bg=hover_bg))
        btn.bind('<Leave>', lambda e: btn.configure(bg=bg))
        
        return btn

    # --- YARDIMCI: MODAL YÜKLEME PENCERESİ ---
    def show_loading_dialog(self, title="İşlem Yapılıyor..."):
        """Modern tasarımlı yükleme penceresi açar."""
        dialog = tk.Toplevel(self.root)
        dialog.title("")
        dialog.geometry("350x130")
        dialog.resizable(False, False)
        dialog.configure(bg=self.COLORS['bg_card'])
        dialog.overrideredirect(True)  # Kenarlıksız pencere
        
        # ESC ile kapatabilme
        dialog.bind('<Escape>', lambda e: dialog.destroy())

        try:
            x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 175
            y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 65
            dialog.geometry(f"+{x}+{y}")
        except:
            pass 
        
        # Kenarlık efekti
        border_frame = tk.Frame(dialog, bg=self.COLORS['accent'], padx=2, pady=2)
        border_frame.pack(fill=tk.BOTH, expand=True)
        
        inner_frame = tk.Frame(border_frame, bg=self.COLORS['bg_card'])
        inner_frame.pack(fill=tk.BOTH, expand=True)

        # Spinner ikonu
        spinner_lbl = tk.Label(inner_frame, 
                              text="⟳", 
                              font=("Segoe UI", 24),
                              fg=self.COLORS['accent'],
                              bg=self.COLORS['bg_card'])
        spinner_lbl.pack(pady=(20, 5))
        
        lbl = tk.Label(inner_frame, 
                      text=title, 
                      font=("Segoe UI", 11, "bold"),
                      fg=self.COLORS['text_primary'],
                      bg=self.COLORS['bg_card'])
        lbl.pack(pady=5)

        pb = ttk.Progressbar(inner_frame, 
                            orient=tk.HORIZONTAL, 
                            length=280, 
                            mode='indeterminate',
                            style="Modern.Horizontal.TProgressbar")
        pb.pack(pady=(5, 20))
        pb.start(10)

        # Pencereyi kitle (Modal)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.focus_force()
        return dialog

    def run_async_task(self, target_function, callback_function, loading_text="Yükleniyor..."):
        """Genel amaçlı Thread çalıştırıcı."""
        loading_dialog = self.show_loading_dialog(loading_text)
        
        def thread_target():
            try:
                result = target_function() 
                error = None
            except Exception as e:
                result = None
                error = str(e)
            
            self.root.after(0, lambda: self.finish_async_task(loading_dialog, callback_function, result, error))

        threading.Thread(target=thread_target, daemon=True).start()

    def finish_async_task(self, dialog, callback, result, error):
        """Thread bitince çalışır."""
        try:
            dialog.destroy()
        except:
            pass 

        if error:
            messagebox.showerror("Hata", error)
        else:
            callback(result) 

    # --- 1. GÖZAT & BRANCHLER (ASYNC) ---
    def select_folder_async(self):
        folder_selected = filedialog.askdirectory()
        if not folder_selected:
            return
            
        self.entry_path.delete(0, tk.END)
        self.entry_path.insert(0, folder_selected)
        self.current_repo_path = folder_selected

        self.run_async_task(
            target_function=self.load_branches_logic,
            callback_function=self.update_branches_ui,
            loading_text="Git Branchleri okunuyor..."
        )

    def load_branches_logic(self):
        if not os.path.exists(os.path.join(self.current_repo_path, ".git")):
            raise Exception("Bu klasörde '.git' bulunamadı!")

        cmd = ["git", "-C", self.current_repo_path, "branch", "--format=%(refname:short)"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            raise Exception(result.stderr)
        
        return [b.strip() for b in result.stdout.strip().split('\n') if b.strip()]

    def update_branches_ui(self, branches):
        if branches:
            self.branch_combo['values'] = branches
            if 'main' in branches: self.branch_combo.set('main')
            elif 'master' in branches: self.branch_combo.set('master')
            else: self.branch_combo.current(0)
            messagebox.showinfo("Bilgi", f"{len(branches)} adet branch yüklendi.")
        else:
            self.branch_combo.set("Branch bulunamadı")

    def get_turkish_date(self, dt_obj):
        months = {1: "Oca", 2: "Şub", 3: "Mar", 4: "Nis", 5: "May", 6: "Haz",
                  7: "Tem", 8: "Ağu", 9: "Eyl", 10: "Eki", 11: "Kas", 12: "Ara"}
        month_str = months.get(dt_obj.month, "")
        return f"{dt_obj.day} {month_str} {dt_obj.year} {dt_obj.strftime('%H:%M')}"

    # --- 2. ANALİZ İŞLEMİ ---
    def start_analysis_thread(self):
        self.main_progress.pack(pady=10)
        self.main_progress.start(10)
        self.btn_analyze.config(state=tk.DISABLED, 
                               text="Bekleyiniz...",
                               bg=self.COLORS['bg_hover'])
        
        for widget in self.frame_bottom.winfo_children():
            widget.destroy()

        threading.Thread(target=self.run_analysis_logic, daemon=True).start()

    def run_analysis_logic(self):
        repo_path = self.entry_path.get()
        start_date = self.entry_start.get()
        end_date = self.entry_end.get()
        selected_branch = self.branch_combo.get()

        error_msg = None
        log_data = None

        if not repo_path or not os.path.isdir(repo_path):
            self.root.after(0, self.finish_analysis, None, "Geçerli bir proje klasörü seçin.")
            return

        git_command = [
            "git", "-C", repo_path, "log", selected_branch,
            f"--since={start_date} 00:00",
            f"--until={end_date} 23:59",
            "--name-only",
            "--pretty=format:@@@COMMIT@@@%h|%an|%ad|%s",
            "--date=format:%Y-%m-%d %H:%M:%S"
        ]

        try:
            result = subprocess.run(git_command, capture_output=True, text=True, encoding='utf-8')
            if result.returncode != 0:
                error_msg = result.stderr
            else:
                log_data = result.stdout.strip()
        except Exception as e:
            error_msg = str(e)

        self.root.after(0, self.finish_analysis, log_data, error_msg)

    def finish_analysis(self, log_data, error_msg):
        self.main_progress.stop()
        self.main_progress.pack_forget()
        self.btn_analyze.config(state=tk.NORMAL, 
                               text="ANALİZ ET",
                               bg=self.COLORS['accent_green'])

        if error_msg:
            messagebox.showerror("Hata", error_msg)
            return

        if not log_data:
            # Modern "veri yok" mesajı
            no_data_frame = tk.Frame(self.frame_bottom, bg=self.COLORS['bg_card'], padx=50, pady=50)
            no_data_frame.pack(expand=True, pady=100)
            
            icon_lbl = tk.Label(no_data_frame, 
                               text="📭", 
                               font=("Segoe UI", 48),
                               bg=self.COLORS['bg_card'])
            icon_lbl.pack(pady=(0, 15))
            
            lbl_nodata = tk.Label(no_data_frame, 
                                 text="Bu tarih aralığında kayıt bulunamadı", 
                                 font=("Segoe UI", 14, "bold"), 
                                 fg=self.COLORS['text_primary'],
                                 bg=self.COLORS['bg_card'])
            lbl_nodata.pack()
            return
        
        self.create_tabs_and_content(log_data)

    def create_tabs_and_content(self, log_data):
        data = []
        commits = log_data.split('@@@COMMIT@@@')
        
        for c in commits:
            if not c.strip(): continue
            
            lines = c.strip().split('\n')
            header = lines[0]
            file_lines = lines[1:]
            
            try:
                parts = header.strip().split('|')
                if len(parts) >= 4:
                    files_str = " ".join([f.strip() for f in file_lines if f.strip()])
                    
                    data.append({
                        'Hash': parts[0],
                        'Author': parts[1],
                        'Date': parts[2],
                        'Message': "|".join(parts[3:]),
                        'Files': files_str
                    })
            except:
                continue

        self.df = pd.DataFrame(data)
        self.df['Date'] = pd.to_datetime(self.df['Date'], format='%Y-%m-%d %H:%M:%S')
        self.filtered_df = self.df.copy()

        # Özet bilgi kartı
        self.create_summary_card()

        self.notebook = ttk.Notebook(self.frame_bottom)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

        # Modern Tab Frameları
        tab_graph = tk.Frame(self.notebook, bg=self.COLORS['bg_dark'])
        self.notebook.add(tab_graph, text='  📊 Grafikler  ')

        tab_table = tk.Frame(self.notebook, bg=self.COLORS['bg_dark'])
        self.notebook.add(tab_table, text='  📋 Commit Geçmişi  ')

        tab_merges = tk.Frame(self.notebook, bg=self.COLORS['bg_dark'])
        self.notebook.add(tab_merges, text='  🔀 Merge İşlemleri  ')

        tab_daily = tk.Frame(self.notebook, bg=self.COLORS['bg_dark'])
        self.notebook.add(tab_daily, text='  📅 Günlük Analiz  ')

        tab_cicd = tk.Frame(self.notebook, bg=self.COLORS['bg_dark'])
        self.notebook.add(tab_cicd, text='  🚀 CI/CD & Deploy  ')

        self.setup_graph_tab(tab_graph, self.df)
        self.setup_table_tab(tab_table)
        self.setup_merges_tab(tab_merges, self.df)
        self.setup_daily_tab(tab_daily, self.df)
        self.setup_cicd_tab(tab_cicd, self.df)

    def create_summary_card(self):
        """Analiz özet kartı oluştur"""
        summary_frame = tk.Frame(self.frame_bottom, bg=self.COLORS['bg_card'])
        summary_frame.pack(fill=tk.X, pady=(0, 0))

        # CI/CD sayısını hesapla
        cicd_keywords = ['deploy', 'release', 'build', 'ci', 'cd', 'pipeline', 'hotfix']
        pattern = '|'.join(cicd_keywords)
        cicd_count = len(self.df[self.df['Message'].str.lower().str.contains(pattern, na=False, regex=True)])

        # İstatistikler
        stats = [
            ("📝", "Toplam Commit", str(len(self.df)), self.COLORS['accent']),
            ("👥", "Geliştirici", str(self.df['Author'].nunique()), self.COLORS['accent_purple']),
            ("📅", "Gün Sayısı", str(self.df['Date'].dt.date.nunique()), self.COLORS['accent_cyan']),
            ("🚀", "CI/CD", str(cicd_count), self.COLORS['accent_green']),
            ("🔥", "En Aktif", self.df['Author'].value_counts().index[0] if len(self.df) > 0 else "-", self.COLORS['accent_orange']),
        ]

        for i, (icon, label, value, color) in enumerate(stats):
            stat_frame = tk.Frame(summary_frame, bg=self.COLORS['bg_card'], padx=25, pady=15)
            stat_frame.pack(side=tk.LEFT, fill=tk.Y)

            tk.Label(stat_frame,
                    text=icon,
                    font=("Segoe UI", 16),
                    bg=self.COLORS['bg_card']).pack(side=tk.LEFT, padx=(0, 10))

            text_frame = tk.Frame(stat_frame, bg=self.COLORS['bg_card'])
            text_frame.pack(side=tk.LEFT)

            tk.Label(text_frame,
                    text=label,
                    font=("Segoe UI", 9, "bold"),
                    fg=self.COLORS['text_primary'],
                    bg=self.COLORS['bg_card']).pack(anchor='w')

            tk.Label(text_frame,
                    text=value,
                    font=("Segoe UI", 14, "bold"),
                    fg=color,
                    bg=self.COLORS['bg_card']).pack(anchor='w')

    # --- TAB 1: GRAFİKLER (DİNAMİK COMBOBOX EKLENDİ) ---
    def setup_graph_tab(self, parent_frame, df):
        # Üst Panel: Grafik Seçimi
        control_frame = tk.Frame(parent_frame, bg=self.COLORS['bg_card'], pady=15)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Label(control_frame, 
                text="📈 Grafik Türü:", 
                bg=self.COLORS['bg_card'], 
                fg=self.COLORS['text_primary'],
                font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=(20, 10))
        
        # Seçenekler
        graph_options = [
            "Genel Bakış (Bar + Çizgi)",
            "Yazar Dağılımı (Pasta Grafiği)",
            "Saatlik Yoğunluk (Bar Grafiği)",
            "Haftanın Günleri (Bar Grafiği)"
        ]
        
        self.graph_combo = ttk.Combobox(control_frame, 
                                       values=graph_options, 
                                       state="readonly", 
                                       width=32,
                                       style="Modern.TCombobox",
                                       font=("Segoe UI", 10))
        self.graph_combo.pack(side=tk.LEFT, padx=10)
        self.graph_combo.current(0)
        self.graph_combo.bind("<<ComboboxSelected>>", lambda e: self.update_graph_view(df))

        # Grafik Alanı
        self.graph_canvas_frame = tk.Frame(parent_frame, bg=self.COLORS['bg_dark'])
        self.graph_canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.update_graph_view(df)

    def update_graph_view(self, df):
        # Eski grafiği temizle
        for widget in self.graph_canvas_frame.winfo_children():
            widget.destroy()

        selection = self.graph_combo.get()
        
        # Modern koyu tema
        plt.style.use('dark_background')
        plt.rcParams.update({
            'figure.facecolor': self.COLORS['bg_dark'],
            'axes.facecolor': self.COLORS['bg_card'],
            'axes.edgecolor': self.COLORS['border'],
            'axes.labelcolor': self.COLORS['text_primary'],
            'text.color': self.COLORS['text_primary'],
            'xtick.color': self.COLORS['text_secondary'],
            'ytick.color': self.COLORS['text_secondary'],
            'grid.color': self.COLORS['border'],
            'grid.alpha': 0.3,
            'font.family': 'Segoe UI',
        })
        
        # 1. GENEL BAKIŞ
        if selection == "Genel Bakış (Bar + Çizgi)":
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
            fig.patch.set_facecolor(self.COLORS['bg_dark'])
            plt.subplots_adjust(hspace=0.4, top=0.92, bottom=0.08)

            author_counts = df['Author'].value_counts().head(10)
            bars = ax1.bar(range(len(author_counts)), author_counts.values, 
                          color=self.COLORS['accent'], alpha=0.85, edgecolor='none')
            ax1.set_xticks(range(len(author_counts)))
            ax1.set_xticklabels(author_counts.index, rotation=25, ha='right')
            ax1.set_title('En Çok Katkı Sağlayanlar', fontsize=12, fontweight='bold', color=self.COLORS['text_bright'])
            ax1.grid(axis='y', alpha=0.2)
            
            df['Day'] = df['Date'].dt.date
            daily_counts = df.groupby('Day').size()
            ax2.plot(range(len(daily_counts)), daily_counts.values, 
                    marker='o', color=self.COLORS['accent_green'], linewidth=2.5, markersize=6)
            ax2.fill_between(range(len(daily_counts)), daily_counts.values, 
                            color=self.COLORS['accent_green'], alpha=0.15)
            ax2.set_title('Günlük Commit Yoğunluğu', fontsize=12, fontweight='bold', color=self.COLORS['text_bright'])
            ax2.grid(axis='y', alpha=0.2)

        # 2. YAZAR DAĞILIMI (PASTA)
        elif selection == "Yazar Dağılımı (Pasta Grafiği)":
            fig, ax = plt.subplots(figsize=(9, 8))
            fig.patch.set_facecolor(self.COLORS['bg_dark'])
            author_counts = df['Author'].value_counts().head(8)
            colors = [self.COLORS['accent'], self.COLORS['accent_purple'], self.COLORS['accent_cyan'],
                     self.COLORS['accent_orange'], self.COLORS['accent_green'], self.COLORS['accent_red'],
                     self.COLORS['warning'], self.COLORS['success']]
            wedges, texts, autotexts = ax.pie(author_counts, autopct='%1.1f%%', 
                                             startangle=90, colors=colors[:len(author_counts)],
                                             wedgeprops={'edgecolor': self.COLORS['bg_dark'], 'linewidth': 2})
            for autotext in autotexts:
                autotext.set_color(self.COLORS['bg_dark'])
                autotext.set_fontweight('bold')
            ax.legend(author_counts.index, loc='lower right', facecolor=self.COLORS['bg_card'],
                     edgecolor=self.COLORS['border'], labelcolor=self.COLORS['text_primary'])
            ax.set_title("Geliştirici Dağılımı", fontsize=14, fontweight='bold', color=self.COLORS['text_bright'])

        # 3. SAATLİK YOĞUNLUK
        elif selection == "Saatlik Yoğunluk (Bar Grafiği)":
            fig, ax = plt.subplots(figsize=(12, 6))
            fig.patch.set_facecolor(self.COLORS['bg_dark'])
            hourly_counts = df['Date'].dt.hour.value_counts().sort_index()
            ax.bar(hourly_counts.index, hourly_counts.values, 
                  color=self.COLORS['accent_orange'], alpha=0.85, edgecolor='none')
            ax.set_xlabel("Saat (00-23)", fontsize=10)
            ax.set_ylabel("Commit Sayısı", fontsize=10)
            ax.set_title("Günün Hangi Saatlerinde Çalışılıyor?", fontsize=12, fontweight='bold', color=self.COLORS['text_bright'])
            ax.grid(axis='y', alpha=0.2)

        # 4. HAFTANIN GÜNLERİ
        elif selection == "Haftanın Günleri (Bar Grafiği)":
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor(self.COLORS['bg_dark'])
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            days_tr = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
            day_counts = df['Date'].dt.day_name().value_counts().reindex(days).fillna(0)
            ax.bar(range(len(days_tr)), day_counts.values, 
                  color=self.COLORS['accent_purple'], alpha=0.85, edgecolor='none')
            ax.set_xticks(range(len(days_tr)))
            ax.set_xticklabels(days_tr, rotation=0)
            ax.set_title("Haftanın Günlerine Göre Yoğunluk", fontsize=12, fontweight='bold', color=self.COLORS['text_bright'])
            ax.grid(axis='y', alpha=0.2)

        # Canvas'a yerleştir
        canvas = FigureCanvasTkAgg(fig, master=self.graph_canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        plt.close(fig)

    # --- TAB 2: TABLO & ARAMA ---
    def setup_table_tab(self, parent_frame):
        # Kontrol Paneli
        frame_controls = tk.Frame(parent_frame, pady=12, bg=self.COLORS['bg_card'])
        frame_controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 0))

        # Arama Alanı
        search_frame = tk.Frame(frame_controls, bg=self.COLORS['bg_card'])
        search_frame.pack(side=tk.LEFT, padx=15)

        tk.Label(search_frame, 
                text="🔍", 
                bg=self.COLORS['bg_card'],
                fg=self.COLORS['text_primary'],
                font=("Segoe UI", 14)).pack(side=tk.LEFT, padx=(0, 8))
        
        self.entry_search = tk.Entry(search_frame, 
                                    width=35, 
                                    font=("Segoe UI", 10),
                                    bg=self.COLORS['bg_hover'],
                                    fg=self.COLORS['text_bright'],
                                    insertbackground=self.COLORS['accent'],
                                    relief='flat',
                                    highlightthickness=2,
                                    highlightbackground=self.COLORS['border'],
                                    highlightcolor=self.COLORS['accent'])
        self.entry_search.pack(side=tk.LEFT, ipady=6)
        self.entry_search.bind('<Return>', lambda e: self.perform_search())
        self.entry_search.bind('<KeyRelease>', self.on_search_key_release)

        btn_search = self.create_button(search_frame, "Ara", self.perform_search, 'secondary')
        btn_search.pack(side=tk.LEFT, padx=(10, 0))

        # Export Butonu
        btn_export = self.create_button(frame_controls, "📥 Excel'e Aktar", self.export_to_excel, 'primary')
        btn_export.pack(side=tk.RIGHT, padx=15)

        # Tablo Alanı
        frame_table = tk.Frame(parent_frame, bg=self.COLORS['bg_dark'])
        frame_table.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tree_scroll = ttk.Scrollbar(frame_table, style="Modern.Vertical.TScrollbar")
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        cols = ("Date", "Author", "Hash", "Message")
        self.tree = ttk.Treeview(frame_table, columns=cols, show='headings', 
                                yscrollcommand=tree_scroll.set, style="Modern.Treeview")
        
        self.tree.heading("Date", text="📅 Tarih")
        self.tree.column("Date", minwidth=150, width=160)
        self.tree.heading("Author", text="👤 Geliştirici")
        self.tree.column("Author", minwidth=130, width=140)
        self.tree.heading("Hash", text="🔑 ID")
        self.tree.column("Hash", minwidth=90, width=100)
        self.tree.heading("Message", text="💬 Commit Mesajı (Detay için çift tıkla)")
        self.tree.column("Message", minwidth=400, width=550)

        tree_scroll.config(command=self.tree.yview)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.on_row_double_click_async)

        # Alternatif satır renkleri
        self.tree.tag_configure('oddrow', background=self.COLORS['bg_card'])
        self.tree.tag_configure('evenrow', background=self.COLORS['bg_hover'])

        self.populate_table(self.filtered_df)

    # --- TAB 3: MERGE İŞLEMLERİ ---
    def setup_merges_tab(self, parent_frame, df):
        # Filtreleme
        merge_df = df[df['Message'].str.contains("Merge", case=False, na=False)]

        # Bilgi Kartı
        info_frame = tk.Frame(parent_frame, bg=self.COLORS['bg_card'], pady=15)
        info_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 0))

        tk.Label(info_frame,
                text="🔀",
                font=("Segoe UI", 18),
                fg=self.COLORS['accent_cyan'],
                bg=self.COLORS['bg_card']).pack(side=tk.LEFT, padx=(20, 10))

        tk.Label(info_frame, 
                text=f"Bu tarih aralığında toplam {len(merge_df)} adet Merge işlemi bulundu", 
                font=("Segoe UI", 12, "bold"), 
                fg=self.COLORS['text_primary'],
                bg=self.COLORS['bg_card']).pack(side=tk.LEFT)

        # Tablo
        frame_table = tk.Frame(parent_frame, bg=self.COLORS['bg_dark'])
        frame_table.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scroll = ttk.Scrollbar(frame_table, style="Modern.Vertical.TScrollbar")
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        cols = ("Date", "Author", "Hash", "Message")
        merge_tree = ttk.Treeview(frame_table, columns=cols, show='headings', 
                                 yscrollcommand=scroll.set, style="Modern.Treeview")
        
        merge_tree.heading("Date", text="📅 Tarih")
        merge_tree.column("Date", width=160)
        merge_tree.heading("Author", text="👤 Birleştiren")
        merge_tree.column("Author", width=140)
        merge_tree.heading("Hash", text="🔑 ID")
        merge_tree.column("Hash", width=100)
        merge_tree.heading("Message", text="💬 Merge Mesajı")
        merge_tree.column("Message", width=600)
        
        scroll.config(command=merge_tree.yview)
        merge_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        merge_tree.bind("<Double-1>", lambda e: self.on_row_double_click_async(e, merge_tree))
        merge_tree.tag_configure('oddrow', background=self.COLORS['bg_card'])
        merge_tree.tag_configure('evenrow', background=self.COLORS['bg_hover'])

        # Veriyi doldur
        for index, row in merge_df.iterrows():
            date_str = self.get_turkish_date(row['Date'])
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            merge_tree.insert("", "end", values=(date_str, row['Author'], row['Hash'], row['Message']), tags=(tag,))

    def perform_search(self):
        query = self.entry_search.get().lower().strip()
        if not query:
            self.filtered_df = self.df.copy()
        else:
            self.filtered_df = self.df[
                self.df['Message'].str.lower().str.contains(query, na=False) | 
                self.df['Files'].str.lower().str.contains(query, na=False)
            ]
        self.populate_table(self.filtered_df)

    def on_search_key_release(self, event):
        if not self.entry_search.get():
            self.perform_search()

    def populate_table(self, dataframe):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for index, row in dataframe.iterrows():
            date_str = self.get_turkish_date(row['Date'])
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            self.tree.insert("", "end", values=(date_str, row['Author'], row['Hash'], row['Message']), tags=(tag,))

    # --- TAB 4: GÜNLÜK ANALİZ ---
    def setup_daily_tab(self, parent_frame, df):
        # Kontrol Paneli
        frame_select = tk.Frame(parent_frame, bg=self.COLORS['bg_card'], pady=15)
        frame_select.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 0))

        tk.Label(frame_select, 
                text="📅 Tarih Seçiniz:", 
                bg=self.COLORS['bg_card'],
                fg=self.COLORS['text_primary'],
                font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=20)

        start_date = pd.to_datetime(self.entry_start.get())
        end_date = pd.to_datetime(self.entry_end.get())
        
        date_list = []
        delta = end_date - start_date
        for i in range(delta.days + 1):
            day = start_date + timedelta(days=i)
            date_list.append(day.strftime("%Y-%m-%d"))
        date_list.sort(reverse=True)

        self.daily_combo = ttk.Combobox(frame_select, 
                                       values=date_list, 
                                       state="readonly", 
                                       font=("Segoe UI", 11),
                                       style="Modern.TCombobox",
                                       width=18)
        self.daily_combo.pack(side=tk.LEFT, padx=5)
        self.daily_combo.set("Tarih Seç...")
        self.daily_combo.bind("<<ComboboxSelected>>", lambda e: self.on_day_selected(df))

        self.lbl_daily_count = tk.Label(frame_select, 
                                       text="Henüz seçim yapılmadı.", 
                                       bg=self.COLORS['bg_card'],
                                       fg=self.COLORS['text_primary'],
                                       font=("Segoe UI", 11))
        self.lbl_daily_count.pack(side=tk.LEFT, padx=30)

        self.frame_daily_list = tk.Frame(parent_frame, bg=self.COLORS['bg_dark'])
        self.frame_daily_list.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=10, pady=10)

    def on_day_selected(self, df):
        selected_date_str = self.daily_combo.get()
        if not selected_date_str: return

        selected_date = pd.to_datetime(selected_date_str).date()
        daily_commits = df[df['Date'].dt.date == selected_date]
        count = len(daily_commits)

        self.lbl_daily_count.config(
            text=f"✅ {selected_date_str} tarihinde toplam {count} commit atıldı.", 
            fg=self.COLORS['accent_green'], 
            font=("Segoe UI", 11, "bold"))

        for widget in self.frame_daily_list.winfo_children():
            widget.destroy()

        if count > 0:
            cols = ("Time", "Author", "Message")
            tree = ttk.Treeview(self.frame_daily_list, columns=cols, show='headings', style="Modern.Treeview")
            
            tree.heading("Time", text="🕐 Saat")
            tree.heading("Author", text="👤 Yazar")
            tree.heading("Message", text="💬 Mesaj")
            tree.column("Time", width=100)
            tree.column("Author", width=180)
            tree.column("Message", width=550)
            
            tree.pack(fill=tk.BOTH, expand=True)
            tree.tag_configure('oddrow', background=self.COLORS['bg_card'])
            tree.tag_configure('evenrow', background=self.COLORS['bg_hover'])

            for idx, (_, row) in enumerate(daily_commits.iterrows()):
                time_str = row['Date'].strftime("%H:%M")
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                tree.insert("", "end", values=(time_str, row['Author'], row['Message']), tags=(tag,))
        else:
            empty_frame = tk.Frame(self.frame_daily_list, bg=self.COLORS['bg_card'], padx=40, pady=40)
            empty_frame.pack(expand=True, pady=50)
            
            tk.Label(empty_frame, 
                    text="😴", 
                    font=("Segoe UI", 36),
                    bg=self.COLORS['bg_card']).pack(pady=(0, 10))
            tk.Label(empty_frame, 
                    text="Bu tarihte hiç commit yok", 
                    font=("Segoe UI", 12, "bold"), 
                    fg=self.COLORS['text_primary'],
                    bg=self.COLORS['bg_card']).pack()

    # --- TAB 5: CI/CD & DEPLOY ---
    def setup_cicd_tab(self, parent_frame, df):
        """CI/CD ve Deploy süreçlerini gösteren tab"""
        
        # CI/CD anahtar kelimeleri
        cicd_keywords = [
            'deploy', 'deployment', 'deployed',
            'release', 'released',
            'build', 'ci', 'cd', 'pipeline',
            'publish', 'published',
            'prod', 'production', 'staging',
            'hotfix', 'patch',
            'version', 'v1', 'v2', 'v3', 'v4', 'v5',
            '[ci]', '[cd]', '[deploy]', '[release]',
            'ci:', 'cd:', 'deploy:', 'release:',
            'bump', 'upgrade'
        ]
        
        # CI/CD ile ilgili commit'leri filtrele
        pattern = '|'.join(cicd_keywords)
        cicd_df = df[df['Message'].str.lower().str.contains(pattern, na=False, regex=True)]
        
        # Ayrıca dosya adlarına göre de filtrele (CI/CD config dosyaları)
        cicd_files_pattern = r'\.github|jenkinsfile|\.gitlab-ci|azure-pipelines|dockerfile|docker-compose|\.circleci|bitbucket-pipelines'
        cicd_files_df = df[df['Files'].str.lower().str.contains(cicd_files_pattern, na=False, regex=True)]
        
        # Her iki sonucu birleştir
        combined_df = pd.concat([cicd_df, cicd_files_df]).drop_duplicates(subset=['Hash'])
        combined_df = combined_df.sort_values('Date', ascending=False)
        
        # Üst bilgi kartı
        header_frame = tk.Frame(parent_frame, bg=self.COLORS['bg_card'])
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        # Sol taraf - İstatistikler
        stats_frame = tk.Frame(header_frame, bg=self.COLORS['bg_card'])
        stats_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=15)
        
        tk.Label(stats_frame,
                text="🚀 CI/CD & Deploy Özeti",
                font=("Segoe UI", 14, "bold"),
                fg=self.COLORS['accent_green'],
                bg=self.COLORS['bg_card']).pack(anchor='w')
        
        # İstatistik sayıları
        deploy_count = len(cicd_df[cicd_df['Message'].str.lower().str.contains('deploy', na=False)])
        release_count = len(cicd_df[cicd_df['Message'].str.lower().str.contains('release', na=False)])
        build_count = len(cicd_df[cicd_df['Message'].str.lower().str.contains('build|pipeline|ci', na=False, regex=True)])
        
        stats_text = f"📦 Deploy: {deploy_count}  |  🏷️ Release: {release_count}  |  🔧 Build/CI: {build_count}  |  📊 Toplam: {len(combined_df)}"
        
        tk.Label(stats_frame,
                text=stats_text,
                font=("Segoe UI", 11),
                fg=self.COLORS['text_primary'],
                bg=self.COLORS['bg_card']).pack(anchor='w', pady=(10, 0))
        
        # Git Tags Butonu
        btn_frame = tk.Frame(header_frame, bg=self.COLORS['bg_card'])
        btn_frame.pack(side=tk.RIGHT, padx=20, pady=15)
        
        btn_tags = self.create_button(btn_frame, "🏷️ Git Tags Göster", self.show_git_tags, 'secondary')
        btn_tags.pack(side=tk.RIGHT)
        
        # Filtre seçenekleri
        filter_frame = tk.Frame(parent_frame, bg=self.COLORS['bg_hover'], pady=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        tk.Label(filter_frame,
                text="🔍 Filtre:",
                font=("Segoe UI", 10, "bold"),
                fg=self.COLORS['text_primary'],
                bg=self.COLORS['bg_hover']).pack(side=tk.LEFT, padx=(15, 10))
        
        filter_options = ["Tümü", "Deploy", "Release", "Build/CI", "Hotfix", "Config Değişiklikleri"]
        self.cicd_filter_combo = ttk.Combobox(filter_frame,
                                              values=filter_options,
                                              state="readonly",
                                              width=20,
                                              style="Modern.TCombobox",
                                              font=("Segoe UI", 10))
        self.cicd_filter_combo.pack(side=tk.LEFT, padx=5)
        self.cicd_filter_combo.current(0)
        self.cicd_filter_combo.bind("<<ComboboxSelected>>", 
                                   lambda e: self.filter_cicd_table(df, cicd_files_df))
        
        # Tablo
        self.cicd_table_frame = tk.Frame(parent_frame, bg=self.COLORS['bg_dark'])
        self.cicd_table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tabloyu oluştur
        self.populate_cicd_table(combined_df)
    
    def populate_cicd_table(self, dataframe):
        """CI/CD tablosunu doldur"""
        # Eski içeriği temizle
        for widget in self.cicd_table_frame.winfo_children():
            widget.destroy()
        
        if dataframe.empty:
            empty_frame = tk.Frame(self.cicd_table_frame, bg=self.COLORS['bg_card'], padx=40, pady=40)
            empty_frame.pack(expand=True, pady=50)
            
            tk.Label(empty_frame,
                    text="🔍",
                    font=("Segoe UI", 36),
                    bg=self.COLORS['bg_card']).pack(pady=(0, 10))
            tk.Label(empty_frame,
                    text="CI/CD ile ilgili commit bulunamadı",
                    font=("Segoe UI", 12, "bold"),
                    fg=self.COLORS['text_primary'],
                    bg=self.COLORS['bg_card']).pack()
            return
        
        scroll = ttk.Scrollbar(self.cicd_table_frame, style="Modern.Vertical.TScrollbar")
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        cols = ("Date", "Author", "Type", "Hash", "Message")
        cicd_tree = ttk.Treeview(self.cicd_table_frame, columns=cols, show='headings',
                                yscrollcommand=scroll.set, style="Modern.Treeview")
        
        cicd_tree.heading("Date", text="📅 Tarih")
        cicd_tree.column("Date", width=150)
        cicd_tree.heading("Author", text="👤 Deployer")
        cicd_tree.column("Author", width=130)
        cicd_tree.heading("Type", text="🏷️ Tür")
        cicd_tree.column("Type", width=100)
        cicd_tree.heading("Hash", text="🔑 ID")
        cicd_tree.column("Hash", width=90)
        cicd_tree.heading("Message", text="💬 Açıklama")
        cicd_tree.column("Message", width=550)
        
        scroll.config(command=cicd_tree.yview)
        cicd_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        cicd_tree.bind("<Double-1>", lambda e: self.on_row_double_click_async(e, cicd_tree))
        
        # Tür renkleri
        cicd_tree.tag_configure('deploy', background='#1a3d2e', foreground=self.COLORS['accent_green'])
        cicd_tree.tag_configure('release', background='#2e1a3d', foreground=self.COLORS['accent_purple'])
        cicd_tree.tag_configure('build', background='#1a2e3d', foreground=self.COLORS['accent_cyan'])
        cicd_tree.tag_configure('hotfix', background='#3d1a1a', foreground=self.COLORS['accent_red'])
        cicd_tree.tag_configure('config', background='#3d2e1a', foreground=self.COLORS['accent_orange'])
        cicd_tree.tag_configure('oddrow', background=self.COLORS['bg_card'])
        cicd_tree.tag_configure('evenrow', background=self.COLORS['bg_hover'])
        
        for idx, (_, row) in enumerate(dataframe.iterrows()):
            date_str = self.get_turkish_date(row['Date'])
            msg_lower = row['Message'].lower()
            
            # Tür belirleme
            if 'deploy' in msg_lower:
                cicd_type = "🚀 Deploy"
                tag = 'deploy'
            elif 'release' in msg_lower:
                cicd_type = "🏷️ Release"
                tag = 'release'
            elif 'hotfix' in msg_lower or 'patch' in msg_lower:
                cicd_type = "🔥 Hotfix"
                tag = 'hotfix'
            elif any(x in msg_lower for x in ['build', 'pipeline', 'ci', 'cd']):
                cicd_type = "🔧 Build"
                tag = 'build'
            else:
                cicd_type = "⚙️ Config"
                tag = 'config'
            
            cicd_tree.insert("", "end", 
                           values=(date_str, row['Author'], cicd_type, row['Hash'], row['Message']),
                           tags=(tag,))
        
        self.cicd_tree = cicd_tree
    
    def filter_cicd_table(self, df, cicd_files_df):
        """CI/CD tablosunu filtrele"""
        selected = self.cicd_filter_combo.get()
        
        cicd_keywords = [
            'deploy', 'deployment', 'deployed',
            'release', 'released',
            'build', 'ci', 'cd', 'pipeline',
            'publish', 'published',
            'prod', 'production', 'staging',
            'hotfix', 'patch',
            'version', 'v1', 'v2', 'v3', 'v4', 'v5',
            '[ci]', '[cd]', '[deploy]', '[release]',
            'ci:', 'cd:', 'deploy:', 'release:',
            'bump', 'upgrade'
        ]
        pattern = '|'.join(cicd_keywords)
        cicd_df = df[df['Message'].str.lower().str.contains(pattern, na=False, regex=True)]
        
        if selected == "Tümü":
            combined_df = pd.concat([cicd_df, cicd_files_df]).drop_duplicates(subset=['Hash'])
        elif selected == "Deploy":
            combined_df = df[df['Message'].str.lower().str.contains('deploy', na=False)]
        elif selected == "Release":
            combined_df = df[df['Message'].str.lower().str.contains('release', na=False)]
        elif selected == "Build/CI":
            combined_df = df[df['Message'].str.lower().str.contains('build|pipeline|ci|cd', na=False, regex=True)]
        elif selected == "Hotfix":
            combined_df = df[df['Message'].str.lower().str.contains('hotfix|patch', na=False, regex=True)]
        elif selected == "Config Değişiklikleri":
            combined_df = cicd_files_df
        else:
            combined_df = pd.concat([cicd_df, cicd_files_df]).drop_duplicates(subset=['Hash'])
        
        combined_df = combined_df.sort_values('Date', ascending=False)
        self.populate_cicd_table(combined_df)
    
    def show_git_tags(self):
        """Git tag'lerini göster"""
        self.run_async_task(
            target_function=self.get_git_tags_logic,
            callback_function=self.show_git_tags_ui,
            loading_text="Git Tags yükleniyor..."
        )
    
    def get_git_tags_logic(self):
        """Git tag'lerini al"""
        # Tag listesi ve tarihlerini al
        cmd = ["git", "-C", self.current_repo_path, "tag", "-l", "--sort=-creatordate", 
               "--format=%(refname:short)|%(creatordate:format:%Y-%m-%d %H:%M:%S)|%(subject)|%(taggername)"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode != 0:
            # Basit tag listesi dene
            cmd = ["git", "-C", self.current_repo_path, "tag", "-l", "--sort=-creatordate"]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            if result.returncode != 0:
                raise Exception("Tag listesi alınamadı")
            
            tags = []
            for tag in result.stdout.strip().split('\n'):
                if tag.strip():
                    tags.append({'tag': tag.strip(), 'date': '-', 'message': '-', 'author': '-'})
            return tags
        
        tags = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = line.split('|')
                tags.append({
                    'tag': parts[0] if len(parts) > 0 else '-',
                    'date': parts[1] if len(parts) > 1 else '-',
                    'message': parts[2] if len(parts) > 2 else '-',
                    'author': parts[3] if len(parts) > 3 else '-'
                })
        return tags
    
    def show_git_tags_ui(self, tags):
        """Git tag'lerini popup'ta göster"""
        popup = tk.Toplevel(self.root)
        popup.title("Git Tags (Releases)")
        popup.geometry("900x600")
        popup.configure(bg=self.COLORS['bg_dark'])
        
        popup.bind('<Escape>', lambda e: popup.destroy())
        popup.transient(self.root)
        popup.grab_set()
        popup.focus_force()
        
        # Başlık
        header = tk.Frame(popup, bg=self.COLORS['bg_card'], pady=15)
        header.pack(fill=tk.X)
        
        tk.Label(header,
                text="🏷️ Git Tags & Releases",
                font=("Segoe UI", 14, "bold"),
                fg=self.COLORS['accent_purple'],
                bg=self.COLORS['bg_card']).pack(side=tk.LEFT, padx=20)
        
        tk.Label(header,
                text=f"Toplam {len(tags)} tag bulundu",
                font=("Segoe UI", 10),
                fg=self.COLORS['text_primary'],
                bg=self.COLORS['bg_card']).pack(side=tk.RIGHT, padx=20)
        
        # Tag listesi
        if not tags:
            empty_frame = tk.Frame(popup, bg=self.COLORS['bg_card'], padx=40, pady=40)
            empty_frame.pack(expand=True, pady=50)
            
            tk.Label(empty_frame,
                    text="🏷️",
                    font=("Segoe UI", 36),
                    bg=self.COLORS['bg_card']).pack(pady=(0, 10))
            tk.Label(empty_frame,
                    text="Bu repository'de tag bulunamadı",
                    font=("Segoe UI", 12, "bold"),
                    fg=self.COLORS['text_primary'],
                    bg=self.COLORS['bg_card']).pack()
            return
        
        frame_table = tk.Frame(popup, bg=self.COLORS['bg_dark'])
        frame_table.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        scroll = ttk.Scrollbar(frame_table, style="Modern.Vertical.TScrollbar")
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        cols = ("Tag", "Date", "Author", "Message")
        tree = ttk.Treeview(frame_table, columns=cols, show='headings',
                           yscrollcommand=scroll.set, style="Modern.Treeview")
        
        tree.heading("Tag", text="🏷️ Tag")
        tree.column("Tag", width=150)
        tree.heading("Date", text="📅 Tarih")
        tree.column("Date", width=150)
        tree.heading("Author", text="👤 Oluşturan")
        tree.column("Author", width=150)
        tree.heading("Message", text="💬 Açıklama")
        tree.column("Message", width=400)
        
        scroll.config(command=tree.yview)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tree.tag_configure('oddrow', background=self.COLORS['bg_card'])
        tree.tag_configure('evenrow', background=self.COLORS['bg_hover'])
        
        for idx, tag in enumerate(tags):
            tag_name = 'evenrow' if idx % 2 == 0 else 'oddrow'
            tree.insert("", "end", 
                       values=(tag['tag'], tag['date'], tag['author'], tag['message']),
                       tags=(tag_name,))

    def export_to_excel(self):
        if self.filtered_df is None or self.filtered_df.empty:
            messagebox.showwarning("Uyarı", "Dışa aktarılacak veri yok!")
            return
            
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if file_path:
            try:
                export_df = self.filtered_df.copy()
                export_df['Date'] = export_df['Date'].apply(self.get_turkish_date)
                export_df.to_excel(file_path, index=False)
                messagebox.showinfo("Başarılı", f"Dosya kaydedildi.")
            except Exception as e:
                messagebox.showerror("Hata", str(e))

    # --- 3. COMMIT DETAYI (ASYNC & TABLO) ---
    def on_row_double_click_async(self, event, tree_widget=None):
        # Hangi treeview'dan tıklandığını anlamak için (Ana tablo mu, Merge tablosu mu?)
        if tree_widget is None:
            # Eğer event.widget kullanılabiliyorsa oradan al, yoksa self.tree varsay
            try:
                tree_widget = event.widget
            except:
                tree_widget = self.tree

        sel = tree_widget.selection()
        if not sel: return
        item = tree_widget.item(sel[0])
        commit_hash = item['values'][2]
        message = item['values'][3]

        self.run_async_task(
            target_function=lambda: self.get_commit_files_logic(commit_hash),
            callback_function=lambda files: self.show_commit_details_ui(commit_hash, message, files),
            loading_text="Dosya listesi hazırlanıyor..."
        )

    def get_commit_files_logic(self, commit_hash):
        cmd = ["git", "-C", self.current_repo_path, "show", "--name-only", "--pretty=", commit_hash]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0: raise Exception("Hata oluştu")
        return result.stdout.strip().split('\n')

    def show_commit_details_ui(self, commit_hash, message, files):
        popup = tk.Toplevel(self.root)
        popup.title(f"Commit: {commit_hash}")
        popup.geometry("900x650")
        popup.configure(bg=self.COLORS['bg_dark'])

        popup.bind('<Escape>', lambda e: popup.destroy())
        popup.transient(self.root)
        popup.grab_set()
        popup.focus_force()

        # Başlık Kartı
        header_frame = tk.Frame(popup, bg=self.COLORS['bg_card'], pady=15)
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 0))

        tk.Label(header_frame,
                text="🔍",
                font=("Segoe UI", 18),
                fg=self.COLORS['accent'],
                bg=self.COLORS['bg_card']).pack(side=tk.LEFT, padx=(15, 10))

        info_frame = tk.Frame(header_frame, bg=self.COLORS['bg_card'])
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(info_frame,
                text=f"Commit: {commit_hash}",
                font=("Consolas", 11, "bold"),
                fg=self.COLORS['accent_cyan'],
                bg=self.COLORS['bg_card']).pack(anchor='w')

        tk.Label(info_frame,
                text=message,
                font=("Segoe UI", 10),
                fg=self.COLORS['text_primary'],
                bg=self.COLORS['bg_card'],
                wraplength=700,
                justify="left").pack(anchor='w', pady=(5, 0))

        # Dosya Sayısı Bilgisi
        file_count = len([f for f in files if f.strip()])
        tk.Label(popup,
                text=f"📁 Değişen {file_count} dosya (Diff için çift tıklayın)",
                font=("Segoe UI", 10, "bold"),
                fg=self.COLORS['text_primary'],
                bg=self.COLORS['bg_dark']).pack(anchor='w', padx=20, pady=(15, 5))

        # Dosya Listesi
        frame_list = tk.Frame(popup, bg=self.COLORS['bg_dark'])
        frame_list.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        tree_scroll = ttk.Scrollbar(frame_list, style="Modern.Vertical.TScrollbar")
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        cols = ("Filename",)
        files_tree = ttk.Treeview(frame_list, columns=cols, show='headings', 
                                 yscrollcommand=tree_scroll.set, style="Modern.Treeview")
        files_tree.heading("Filename", text="📄 Dosya Yolu")
        files_tree.column("Filename", width=800)
        
        files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.config(command=files_tree.yview)

        files_tree.tag_configure('oddrow', background=self.COLORS['bg_card'])
        files_tree.tag_configure('evenrow', background=self.COLORS['bg_hover'])

        for idx, f in enumerate(files):
            if f.strip():
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                files_tree.insert("", "end", values=(f.strip(),), tags=(tag,))

        files_tree.bind("<Double-1>", lambda e: self.on_file_double_click_async(e, files_tree, commit_hash))

    # --- 4. DIFF GÖRÜNTÜLEME (ASYNC) ---
    def on_file_double_click_async(self, event, tree, commit_hash):
        sel = tree.selection()
        if not sel: return
        file_path = tree.item(sel[0])['values'][0]

        self.run_async_task(
            target_function=lambda: self.get_file_diff_logic(commit_hash, file_path),
            callback_function=lambda diff_content: self.show_diff_ui(file_path, diff_content),
            loading_text="Değişiklikler okunuyor..."
        )

    def get_file_diff_logic(self, commit_hash, file_path):
        cmd = ["git", "-C", self.current_repo_path, "show", commit_hash, "--", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0: raise Exception("Diff alınamadı")
        return result.stdout

    def show_diff_ui(self, file_path, diff_content):
        diff_win = tk.Toplevel(self.root)
        diff_win.title(f"Diff: {file_path}")
        diff_win.geometry("1100x750")
        diff_win.configure(bg=self.COLORS['bg_dark'])

        diff_win.bind('<Escape>', lambda e: diff_win.destroy())
        diff_win.transient(self.root)
        diff_win.grab_set()
        diff_win.focus_force()

        # Başlık
        header = tk.Frame(diff_win, bg=self.COLORS['bg_card'], pady=12)
        header.pack(fill=tk.X)

        tk.Label(header,
                text="📝 Değişiklikler",
                font=("Segoe UI", 12, "bold"),
                fg=self.COLORS['text_bright'],
                bg=self.COLORS['bg_card']).pack(side=tk.LEFT, padx=15)

        tk.Label(header,
                text=file_path,
                font=("Consolas", 10),
                fg=self.COLORS['accent_cyan'],
                bg=self.COLORS['bg_card']).pack(side=tk.LEFT, padx=10)

        # İstatistik
        added_count = sum(1 for line in diff_content.splitlines() if line.startswith('+') and not line.startswith('+++'))
        removed_count = sum(1 for line in diff_content.splitlines() if line.startswith('-') and not line.startswith('---'))
        
        stats_frame = tk.Frame(header, bg=self.COLORS['bg_card'])
        stats_frame.pack(side=tk.RIGHT, padx=15)
        
        tk.Label(stats_frame,
                text=f"+{added_count}",
                font=("Consolas", 10, "bold"),
                fg=self.COLORS['accent_green'],
                bg=self.COLORS['bg_card']).pack(side=tk.LEFT, padx=5)
        
        tk.Label(stats_frame,
                text=f"-{removed_count}",
                font=("Consolas", 10, "bold"),
                fg=self.COLORS['accent_red'],
                bg=self.COLORS['bg_card']).pack(side=tk.LEFT, padx=5)

        # Diff İçerik Alanı
        text_frame = tk.Frame(diff_win, bg=self.COLORS['bg_dark'])
        text_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        text_area = tk.Text(text_frame, 
                           font=("Consolas", 11), 
                           wrap=tk.NONE,
                           bg=self.COLORS['bg_card'],
                           fg=self.COLORS['text_primary'],
                           insertbackground=self.COLORS['accent'],
                           selectbackground=self.COLORS['accent'],
                           selectforeground=self.COLORS['bg_dark'],
                           relief='flat',
                           padx=15,
                           pady=10)
        
        ys = ttk.Scrollbar(text_frame, command=text_area.yview, style="Modern.Vertical.TScrollbar")
        xs = ttk.Scrollbar(text_frame, command=text_area.xview, orient=tk.HORIZONTAL)
        text_area.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        
        ys.pack(side=tk.RIGHT, fill=tk.Y)
        xs.pack(side=tk.BOTTOM, fill=tk.X)
        text_area.pack(fill=tk.BOTH, expand=True)

        # Modern renk şeması
        text_area.tag_config("added", foreground=self.COLORS['accent_green'], background="#1a2e1a")
        text_area.tag_config("removed", foreground=self.COLORS['accent_red'], background="#2e1a1a")
        text_area.tag_config("info", foreground=self.COLORS['accent_cyan'])
        text_area.tag_config("header", foreground=self.COLORS['accent_purple'], font=("Consolas", 11, "bold"))

        for line in diff_content.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                text_area.insert(tk.END, line + "\n", "added")
            elif line.startswith("-") and not line.startswith("---"):
                text_area.insert(tk.END, line + "\n", "removed")
            elif line.startswith("@@"):
                text_area.insert(tk.END, line + "\n", "header")
            elif line.startswith("diff") or line.startswith("index"):
                text_area.insert(tk.END, line + "\n", "info")
            else:
                text_area.insert(tk.END, line + "\n")
        
        text_area.config(state=tk.DISABLED)

    def on_closing(self):
        """Uygulama kapatma onayı"""
        if messagebox.askokcancel("Çıkış", "Uygulamayı kapatmak istiyor musunuz?"):
            plt.close('all')  # Tüm matplotlib figürlerini kapat
            self.root.destroy()
            sys.exit()

if __name__ == "__main__":
    root = tk.Tk()
    app = GitAnalyzerApp(root)
    root.mainloop()