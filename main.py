import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import re
import json
import os
import webbrowser

# Optional drag & drop support via tkinterdnd2 (if installed)
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except Exception:
    TkinterDnD = None
    DND_FILES = None
    DND_AVAILABLE = False

CONFIG_FILE = "config.json"

class ConfigHandler:
    @staticmethod
    def get_default_percentages(num):
        if num == 2: return [50.0, 50.0]
        if num == 3: return [33.33, 33.34, 33.33]
        if num == 4: return [25.0, 25.0, 25.0, 25.0]
        if num == 5: return [5.0, 30.0, 30.0, 30.0, 5.0]
        if num == 6: return [5.0, 22.5, 22.5, 22.5, 22.5, 5.0]
        return [100.0/num] * num

    @staticmethod
    def get_default():
        return {
            "photo_h_mm": 90.0, "photo_w_mm": 70.0,
            "canvas_h_cm": 15.0, "canvas_w_cm": 10.0,
            "bund_mode": 4,
            "colors": ["#FFFFFF", "#008000", "#eb0000", "#FFFFFF", "#FFFFFF", "#FFFFFF"],
            "percentages": [25.0, 25.0, 25.0, 25.0, 0.0, 0.0],
            "custom_pct": False,
            "fixed_distance_mm": 3.5,
            "fixed_bottom_mm": 3.5,
            "fixed_top_p_mm": 0.35,
            "border_default_mm": 1.0,
            "border_min_mm": 0.0,
            "border_max_mm": 3.5,
            "text_bg_color": "#FFFFFF",
            "triangle_percent": 50.0,
            "use_background_image": False,
            "background_image": ""
        }

    @staticmethod
    def load():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    loaded = json.load(f)
                base = ConfigHandler.get_default()
                base.update(loaded)
                return base
            except: return None
        return None

    @staticmethod
    def save(config):
        with open(CONFIG_FILE, "w") as f: json.dump(config, f, indent=4)

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, callback, is_initial=False):
        super().__init__(parent)
        self.title("Initial-Konfiguration v1.1.1")
        self.callback = callback
        self.is_initial = is_initial
        self.config = ConfigHandler.load() or ConfigHandler.get_default()
        
        self.grab_set()
        # ensure settings are in front on first-run
        if self.is_initial:
            try:
                self.transient(parent)
                self.attributes("-topmost", True)
            except Exception:
                pass
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.init_ui()

    def init_ui(self):
        container = tk.Frame(self, padx=20, pady=20)
        container.pack()

        # Maße (H x B with tighter spacing)
        tk.Label(container, text="Foto-Maß (mm):", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky="w")
        self.ent_ph = tk.Entry(container, width=8)
        self.ent_ph.insert(0, f"{self.config['photo_h_mm']:.2f}")
        self.ent_ph.grid(row=0, column=1, pady=5)
        tk.Label(container, text=" H x B ").grid(row=0, column=2)
        self.ent_pw = tk.Entry(container, width=8)
        self.ent_pw.insert(0, f"{self.config['photo_w_mm']:.2f}")
        self.ent_pw.grid(row=0, column=3, pady=5)

        tk.Label(container, text="Druck-Format (cm):", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky="w")
        self.ent_ch = tk.Entry(container, width=8)
        self.ent_ch.insert(0, f"{self.config['canvas_h_cm']:.2f}")
        self.ent_ch.grid(row=1, column=1, pady=5)
        tk.Label(container, text=" H x B ").grid(row=1, column=2)
        self.ent_cw = tk.Entry(container, width=8)
        self.ent_cw.insert(0, f"{self.config['canvas_w_cm']:.2f}")
        self.ent_cw.grid(row=1, column=3, pady=5)

        tk.Label(container, text="Farbanzahl:", font=('Arial', 9, 'bold')).grid(row=2, column=0, sticky="w", pady=10)
        self.mode_var = tk.IntVar(value=self.config["bund_mode"])
        self.dropdown = ttk.Combobox(container, textvariable=self.mode_var, values=[2, 3, 4, 5, 6], state="readonly", width=5)
        self.dropdown.grid(row=2, column=1, sticky="w")
        self.dropdown.bind("<<ComboboxSelected>>", self.update_color_rows)

        self.custom_pct_var = tk.BooleanVar(value=self.config.get("custom_pct", False))
        # renamed checkbox with wrap
        chk = tk.Checkbutton(container, text="erweiterte Einstellungen\nund Farbanteile", variable=self.custom_pct_var, command=self.update_color_rows)
        chk.grid(row=2, column=2)

        self.color_frame = tk.LabelFrame(container, text="Farb-Stapel (Oben -> Unten)", padx=10, pady=10)
        self.color_frame.grid(row=3, column=0, columnspan=4, sticky="ew", pady=10)
        
        # Initialize background and custom vars early for update_color_rows
        self.use_bg_var = tk.BooleanVar(value=self.config.get("use_background_image", False))
        
        self.color_rows = []
        self.update_color_rows()
        tk.Checkbutton(container, text="Fahnen-Datei als Hintergrund verwenden", variable=self.use_bg_var, command=self._on_bg_toggle).grid(row=4, column=0, columnspan=4, sticky="w", pady=(4, 2))
        tk.Label(container, text="Datei:").grid(row=5, column=0, sticky="w")
        self.bg_path_var = tk.StringVar(value=self.config.get("background_image", ""))
        self.bg_entry = tk.Entry(container, textvariable=self.bg_path_var, width=42)
        self.bg_entry.grid(row=5, column=1, columnspan=2, sticky="w")
        tk.Button(container, text="Auswählen...", command=self._choose_background).grid(row=5, column=3, sticky="w")

        if DND_AVAILABLE:
            try:
                self.drop_target_register(DND_FILES)
                self.dnd_bind('<<Drop>>', self._on_bg_drop)
            except Exception:
                pass

        # Advanced settings frame (hidden unless checkbox enabled)
        self.adv_frame = tk.LabelFrame(container, text="Erweiterte Einstellungen", padx=10, pady=8)
        self._build_advanced_frame()

        # show adv_frame only if custom_pct_var true
        if self.custom_pct_var.get():
            self.adv_frame.grid(row=6, column=0, columnspan=4, sticky="ew", pady=6)

        tk.Button(container, text="Einstellungen speichern", bg="#28a745", fg="white", font=("Arial", 10, "bold"), command=self.save_and_close).grid(row=7, column=0, columnspan=4, pady=10, sticky="ew")

    def update_color_rows(self, event=None):
        for widget in self.color_frame.winfo_children(): widget.destroy()
        self.color_rows = []
        num = self.mode_var.get()
        
        if not self.custom_pct_var.get():
            defaults = ConfigHandler.get_default_percentages(num)
            for i, val in enumerate(defaults): self.config["percentages"][i] = val

        # background image forces fixed, non-editable percentages
        if self.use_bg_var.get():
            defaults = self._get_bg_percentages(num)
            for i, val in enumerate(defaults):
                self.config["percentages"][i] = val

        for i in range(num):
            row = tk.Frame(self.color_frame)
            row.pack(fill="x", pady=2)
            
            btn = tk.Button(row, bg=self.config["colors"][i], width=12, text=f"Farbe {i+1}", relief="flat", command=lambda idx=i: self.pick_color(idx))
            btn.pack(side="left", padx=5)

            ent = tk.Entry(row, width=8)
            ent.insert(0, f"{self.config['percentages'][i]:.2f}")
            ent.pack(side="left")
            tk.Label(row, text="%").pack(side="left")
            
            if self.use_bg_var.get() or not self.custom_pct_var.get():
                ent.config(state="disabled")

            if self.use_bg_var.get():
                btn.config(state="disabled")

            self.color_rows.append({"btn": btn, "ent": ent})

        # toggle advanced frame visibility
        try:
            if self.custom_pct_var.get():
                self.adv_frame.grid(row=6, column=0, columnspan=4, sticky="ew", pady=6)
            else:
                self.adv_frame.grid_forget()
        except Exception:
            pass
    
    def _build_advanced_frame(self):
        """Create all advanced settings controls in the advanced frame."""
        # Numeric entry fields mapping
        entries_map = {
            "side": (0, "Einzug zu den Seiten (mm):", "fixed_distance_mm", 3.5, ".2f"),
            "bottom": (1, "Einzug/Abstand nach unten (mm):", "fixed_bottom_mm", 3.5, ".2f"),
            "top": (2, "Puffer nach oben (mm):", "fixed_top_p_mm", 0.35, ".2f"),
            "tri": (4, "Dreieck-Hypotenuse (%):", "triangle_percent", 50.0, ".1f"),
            "border_min": (5, "Rahmen min (mm):", "border_min_mm", 0.0, ".1f"),
            "border_max": (6, "Rahmen max (mm):", "border_max_mm", 3.5, ".1f"),
        }
        
        for attr_name, (row, label, key, default, fmt) in entries_map.items():
            tk.Label(self.adv_frame, text=label).grid(row=row, column=0, sticky="w")
            entry = tk.Entry(self.adv_frame, width=8)
            value = self.config.get(key, default)
            entry.insert(0, f"{value:{fmt}}")
            entry.grid(row=row, column=1, sticky="w")
            setattr(self, f"ent_{attr_name}", entry)
        
        # Text background color button (row 3)
        tk.Label(self.adv_frame, text="Text-Hintergrundfarbe:").grid(row=3, column=0, sticky="w")
        self.text_bg = tk.StringVar(value=self.config.get("text_bg_color", "#FFFFFF"))
        self.text_bg_btn = tk.Button(self.adv_frame, text="Farbe wählen", command=self._pick_text_bg)
        self.text_bg_btn.grid(row=3, column=1, sticky="w")
        
        # Reset button
        tk.Button(self.adv_frame, text="Erweiterte Einstellung wiederherstellen", command=self._restore_advanced).grid(row=7, column=0, columnspan=2, pady=6)

    def pick_color(self, idx):
        color = colorchooser.askcolor(initialcolor=self.config["colors"][idx])[1]
        if color:
            self.config["colors"][idx] = color
            self.color_rows[idx]["btn"].config(bg=color)

    def _pick_text_bg(self):
        color = colorchooser.askcolor(initialcolor=self.text_bg.get())[1]
        if color:
            self.text_bg.set(color)

    def _get_bg_percentages(self, num):
        # percent values (sum to 100)
        if num == 2:
            return [50.0, 50.0]
        if num == 3:
            return [33.0, 33.0, 34.0]
        if num == 4:
            return [25.0, 25.0, 25.0, 25.0]
        if num == 5:
            return [5.0, 30.0, 30.0, 30.0, 5.0]
        if num == 6:
            return [5.0, 22.5, 22.5, 22.5, 22.5, 5.0]
        return ConfigHandler.get_default_percentages(num)

    def _on_bg_toggle(self):
        self.update_color_rows()

    def _choose_background(self):
        p = filedialog.askopenfilename(filetypes=[("Bilder", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff")])
        if p:
            self.bg_path_var.set(p)

    def _on_bg_drop(self, event):
        data = event.data
        if not data:
            return
        paths = re.findall(r"\{([^}]+)\}|([^\s]+)", data)
        files = [a or b for a, b in paths if (a or b)]
        if files:
            self.bg_path_var.set(files[0])

    def _restore_advanced(self):
        if not messagebox.askyesno("Wiederherstellen", "Erweiterte Einstellungen auf Standardwerte zurücksetzen?"):
            return
        d = ConfigHandler.get_default()
        self.ent_side.delete(0, tk.END); self.ent_side.insert(0, f"{d.get('fixed_distance_mm',3.5):.2f}")
        self.ent_bottom.delete(0, tk.END); self.ent_bottom.insert(0, f"{d.get('fixed_bottom_mm',3.5):.2f}")
        self.ent_top.delete(0, tk.END); self.ent_top.insert(0, f"{d.get('fixed_top_p_mm',0.35):.2f}")
        self.text_bg.set(d.get('text_bg_color', "#FFFFFF"))
        self.ent_tri.delete(0, tk.END); self.ent_tri.insert(0, f"{d.get('triangle_percent',50.0):.1f}")
        self.ent_border_min.delete(0, tk.END); self.ent_border_min.insert(0, f"{d.get('border_min_mm',0.0):.1f}")
        self.ent_border_max.delete(0, tk.END); self.ent_border_max.insert(0, f"{d.get('border_max_mm',3.5):.1f}")

    def save_and_close(self):
        try:
            # 100% Check
            total_pct = sum(float(self.color_rows[i]["ent"].get()) for i in range(self.mode_var.get()))
            if abs(total_pct - 100.0) > 0.01:
                messagebox.showerror("Fehler", f"Die Summe der Anteile muss exakt 100% ergeben!\nAktuell: {total_pct:.2f}%")
                return

            self.config["photo_h_mm"] = float(self.ent_ph.get())
            self.config["photo_w_mm"] = float(self.ent_pw.get())
            self.config["canvas_h_cm"] = float(self.ent_ch.get())
            self.config["canvas_w_cm"] = float(self.ent_cw.get())
            self.config["bund_mode"] = self.mode_var.get()
            self.config["custom_pct"] = self.custom_pct_var.get()
            self.config["use_background_image"] = bool(self.use_bg_var.get())
            self.config["background_image"] = self.bg_path_var.get().strip()

            if self.use_bg_var.get():
                pcts = self._get_bg_percentages(self.config["bund_mode"])
                for i, val in enumerate(pcts):
                    self.config["percentages"][i] = val
            else:
                for i in range(self.config["bund_mode"]):
                    self.config["percentages"][i] = float(self.color_rows[i]["ent"].get())

            if self.custom_pct_var.get():
                # advanced spacing values (mm) with 2 decimal places
                try:
                    side = round(float(self.ent_side.get().strip().replace(',','.')), 2)
                    bottom = round(float(self.ent_bottom.get().strip().replace(',','.')), 2)
                    top = round(float(self.ent_top.get().strip().replace(',','.')), 2)
                    tri = round(float(self.ent_tri.get().strip().replace(',','.')), 1)
                    bmin = round(float(self.ent_border_min.get().strip().replace(',','.')), 1)
                    bmax = round(float(self.ent_border_max.get().strip().replace(',','.')), 1)
                except Exception:
                    messagebox.showerror("Fehler", "Ungültige erweiterte Einstellungen. Bitte Zahlen im Format 0.00 verwenden.")
                    return
                self.config["fixed_distance_mm"] = side
                self.config["fixed_bottom_mm"] = bottom
                self.config["fixed_top_p_mm"] = top
                self.config["triangle_percent"] = tri
                self.config["border_min_mm"] = bmin
                self.config["border_max_mm"] = bmax
                self.config["text_bg_color"] = self.text_bg.get()

            ConfigHandler.save(self.config)
            self.callback()
            self.destroy()
        except ValueError:
            messagebox.showerror("Fehler", "Bitte nur Zahlen eingeben.")

    def on_close(self):
        if self.is_initial: self.master.destroy()
        self.destroy()

class PortraitProApp:
    def __init__(self, root):
        self.root = root
        self.config = ConfigHandler.load()
        if not self.config:
            self.root.withdraw()
            SettingsWindow(self.root, self.on_initial_config_done, is_initial=True)
        else:
            self.init_main_ui()

    def on_initial_config_done(self):
        self.root.deiconify()
        self.config = ConfigHandler.load()
        self.init_main_ui()

    def show_settings_menu(self):
        SettingsWindow(self.root, self.refresh_config)

    def refresh_config(self):
        self.config = ConfigHandler.load()
        if hasattr(self, 'main_frame'): self.main_frame.destroy()
        if hasattr(self, 'toolbar'): self.toolbar.destroy()
        self.init_main_ui()

    def init_main_ui(self):
        VERSION = "v1.1.1"
        GITHUB_URL = "https://github.com/georggnt/ahnentafel"
        self.root.title(f"Portrait-Pro-Tool {VERSION}")
        # toolbar: direct Optionen button, version and GitHub link on same line
        self.toolbar = tk.Frame(self.root, padx=6, pady=4)
        self.toolbar.pack(fill="x")
        tk.Button(self.toolbar, text="Optionen", command=self.show_settings_menu).pack(side="left")
        tk.Label(self.toolbar, text=VERSION).pack(side="left", padx=8)
        gh = tk.Label(self.toolbar, text="GitHub", fg="blue", cursor="hand2")
        gh.pack(side="left")
        gh.bind("<Button-1>", lambda e: webbrowser.open(GITHUB_URL))

        self.main_frame = tk.Frame(self.root, padx=10, pady=10)
        self.main_frame.pack(fill="both", expand=True)

        self.DPI = 300
        self.MM_TO_PX = self.DPI / 25.4
        self.PHOTO_W = int(self.config["photo_w_mm"] * self.MM_TO_PX)
        self.PHOTO_H = int(self.config["photo_h_mm"] * self.MM_TO_PX)
        self.CANVAS_W = int(self.config["canvas_w_cm"] * 10 * self.MM_TO_PX)
        self.CANVAS_H = int(self.config["canvas_h_cm"] * 10 * self.MM_TO_PX)
        
        # Katheten auf 50% der kürzesten Seite
        tri_pct = float(self.config.get("triangle_percent", 50.0))
        self.TRI_SIZE = int(min(self.PHOTO_W, self.PHOTO_H) * (tri_pct / 100.0))
        
        self.raw_img, self.current_scale = None, 1.0
        self.pan_x = self.pan_y = 0
        self.last_x = self.last_y = 0
        self.debounce_id = None

        # UI
        ctrl = tk.Frame(self.main_frame); ctrl.pack(pady=5)
        tk.Button(ctrl, text="Bild laden", command=self.load_image).grid(row=0, column=0, padx=10)
        tk.Label(ctrl, text="Rahmen (mm):").grid(row=0, column=1)
        self.border_val = tk.DoubleVar(value=self.config["border_default_mm"])
        min_b = float(self.config.get("border_min_mm", 0.0))
        max_b = float(self.config.get("border_max_mm", 3.5))
        self.border_scale = tk.Scale(ctrl, from_=min_b, to=max_b, resolution=0.1, orient=tk.HORIZONTAL, variable=self.border_val, command=self.on_setting_change)
        self.border_scale.grid(row=0, column=2, padx=5)
        self.border_entry_var = tk.StringVar(value=f"{self.border_val.get():.1f}")
        self.border_entry = tk.Entry(ctrl, width=5, textvariable=self.border_entry_var)
        self.border_entry.grid(row=0, column=3, padx=4)
        self.border_entry.bind("<Return>", self._on_border_entry)
        self.border_entry.bind("<FocusOut>", self._on_border_entry)
        self.use_triangle_var = tk.BooleanVar(value=False)
        tk.Checkbutton(ctrl, text="Dreieck", variable=self.use_triangle_var, command=self.update_preview).grid(row=0, column=4)

        # suggestion placeholder for name text
        self.entry_text = tk.Entry(self.main_frame, width=65)
        self._placeholder_text = "Nachname, Vorname(n) rec. am TT.MM.YYYY"
        self.entry_text.insert(0, self._placeholder_text)
        self.entry_text.config(fg="grey")
        self.entry_text.bind("<FocusIn>", lambda e: self._clear_placeholder())
        self.entry_text.bind("<FocusOut>", lambda e: self._add_placeholder())
        self.entry_text.bind("<KeyRelease>", self.on_text_key_release)
        self.entry_text.pack(pady=5)

        pos_frame = tk.Frame(self.main_frame); pos_frame.pack()
        self.text_pos_var = tk.StringVar(value="below")
        tk.Radiobutton(pos_frame, text="Overlay", variable=self.text_pos_var, value="overlay", command=self.on_setting_change).pack(side="left")
        tk.Radiobutton(pos_frame, text="Darunter", variable=self.text_pos_var, value="below", command=self.on_setting_change).pack(side="left")

        self.canvas = tk.Canvas(self.main_frame, width=int(self.PHOTO_W*0.2), height=int(self.PHOTO_H*0.2), bg="#eee", highlightthickness=0)
        self.canvas.pack(pady=10); self.canvas.bind("<B1-Motion>", self.on_drag); self.canvas.bind("<Button-1>", self.on_click)

        tk.Button(self.main_frame, text="Druck-Datei speichern", bg="#007bff", fg="white", command=self.save_check).pack(fill="x")

    def on_drag(self, e):
        if not self.raw_img: return
        # Verschiebung berechnen
        dx = (e.x - self.last_x) / 0.2
        dy = (e.y - self.last_y) / 0.2
        
        # Neue Pan-Werte berechnen
        new_x = self.pan_x - dx
        new_y = self.pan_y - dy
        
        # --- CLAMPING LOGIK (v1.0.1) ---
        # Verhindert das Schieben über den Bildrand hinaus
        border_px = int(self.border_val.get() * self.MM_TO_PX)
        eff_w = self.PHOTO_W - (2 * border_px)
        
        # Verfügbare Höhe für Foto-Ausschnitt ermitteln
        text = self._get_effective_text()
        rect_h = 0
        if self.text_pos_var.get() == "below" and text != "":
            side_px = int(self.config.get("fixed_distance_mm", 3.5) * self.MM_TO_PX)
            bottom_p = int(self.config.get("fixed_bottom_mm", 3.5) * self.MM_TO_PX)
            top_p = int(self.config.get("fixed_top_p_mm", 0.35) * self.MM_TO_PX)
            fs = 1; font = ImageFont.truetype("arial.ttf", fs)
            while font.getbbox(text)[2] - font.getbbox(text)[0] < (self.PHOTO_W - 2*int(self.config["fixed_distance_mm"]*self.MM_TO_PX)) and fs < 400:
                fs += 1; font = ImageFont.truetype("arial.ttf", fs)
            rect_h = (font.getbbox(text)[3] - font.getbbox(text)[1]) + bottom_p + top_p
        
        eff_h = self.PHOTO_H - (2 * border_px)
        avail_h = eff_h - rect_h
        
        img_w_scaled = self.raw_img.width * self.current_scale
        img_h_scaled = self.raw_img.height * self.current_scale
        
        # Grenzwerte: 0 bis (Skaliertes Bild - Ausschnittgröße)
        self.pan_x = max(0, min(img_w_scaled - eff_w, new_x))
        self.pan_y = max(0, min(img_h_scaled - avail_h, new_y))
        
        self.last_x, self.last_y = e.x, e.y
        self.update_preview()

    def create_final_image(self):
        border_px = int(self.border_val.get() * self.MM_TO_PX)
        side_px = int(self.config.get("fixed_distance_mm", 3.5) * self.MM_TO_PX)
        bottom_px = int(self.config.get("fixed_bottom_mm", 3.5) * self.MM_TO_PX)
        top_p_px = int(self.config.get("fixed_top_p_mm", 0.35) * self.MM_TO_PX)
        eff_w, eff_h = self.PHOTO_W - (2 * border_px), self.PHOTO_H - (2 * border_px)
        text = self._get_effective_text()
        
        if text != "":
            fs = 1; font = ImageFont.truetype("arial.ttf", fs)
            while font.getbbox(text)[2] - font.getbbox(text)[0] < (self.PHOTO_W - 2*int(self.config["fixed_distance_mm"]*self.MM_TO_PX)) and fs < 400:
                fs += 1; font = ImageFont.truetype("arial.ttf", fs)
            font_h = font.getbbox(text)[3] - font.getbbox(text)[1]
            rect_h = font_h + bottom_px + top_p_px
        else:
            font = ImageFont.truetype("arial.ttf", 12)
            font_h = 0
            rect_h = 0

        is_below = self.text_pos_var.get() == "below"
        avail_h = eff_h - rect_h if is_below else eff_h
        
        resized = self.raw_img.resize((int(self.raw_img.width * self.current_scale), int(self.raw_img.height * self.current_scale)), Image.Resampling.LANCZOS)
        crop = resized.crop((int(self.pan_x), int(self.pan_y), int(self.pan_x + eff_w), int(self.pan_y + avail_h)))
        
        # Rahmen
        mode = self.config["bund_mode"]; cols = self.config["colors"]; pcts = self.config["percentages"]
        use_bg = self.config.get("use_background_image", False)
        flag_img = None
        if use_bg and self.config.get("background_image"):
            try:
                src = Image.open(self.config.get("background_image")).convert("RGB")
                flag_img = src.resize((self.PHOTO_W, self.PHOTO_H), Image.Resampling.LANCZOS)
            except Exception:
                flag_img = None

        # If using background image, paste it as the entire base; otherwise start with white
        if flag_img:
            nutz = flag_img.copy()
        else:
            nutz = Image.new("RGB", (self.PHOTO_W, self.PHOTO_H), "#FFFFFF")
        
        draw_n = ImageDraw.Draw(nutz)
        
        # Draw borders (left/right stripes for each color segment OR left/right from background)
        curr_y = 0
        for i in range(mode):
            seg_h = int((pcts[i] / 100.0) * self.PHOTO_H)
            y_end = curr_y + seg_h if i < mode-1 else self.PHOTO_H
            if not flag_img:
                draw_n.rectangle([0, curr_y, border_px, y_end], fill=cols[i])
                draw_n.rectangle([self.PHOTO_W-border_px, curr_y, self.PHOTO_W, y_end], fill=cols[i])
            curr_y = y_end
        
        cont = Image.new("RGB", (eff_w, eff_h), "#FFFFFF")
        cont.paste(crop, (0, 0)); draw_c = ImageDraw.Draw(cont)
        if text != "":
            ry0 = eff_h - rect_h
            draw_c.rectangle([0, ry0, eff_w, eff_h], fill=self.config.get("text_bg_color", "#FFFFFF"))
            tw = font.getbbox(text)[2] - font.getbbox(text)[0]
            draw_c.text((side_px + ((eff_w - 2*side_px - tw)//2), eff_h - bottom_px - font_h), text, fill="#000000", font=font)
        
        nutz.paste(cont, (border_px, border_px))
        if self.use_triangle_var.get():
            draw_n.polygon([(self.PHOTO_W, 0), (self.PHOTO_W-self.TRI_SIZE, 0), (self.PHOTO_W, self.TRI_SIZE)], fill="#000000")
            draw_n.line([(self.PHOTO_W-self.TRI_SIZE, 0), (self.PHOTO_W, self.TRI_SIZE)], fill="#FFFFFF", width=1)
        
        bg = Image.new("RGB", (self.CANVAS_W, self.CANVAS_H), "#000000")
        if flag_img:
            bg.paste(flag_img, (0, 0))
        else:
            draw_bg = ImageDraw.Draw(bg)
            curr_y = 0
            for i in range(mode):
                seg_h = int((pcts[i] / 100.0) * self.PHOTO_H)
                y_end = curr_y + seg_h if i < mode-1 else self.PHOTO_H
                draw_bg.rectangle([0, curr_y, self.CANVAS_W, y_end], fill=cols[i])
                curr_y = y_end
        
        bg.paste(nutz, (0, 0))
        return bg

    def recalc_image_fit(self):
        if not self.raw_img: return
        border_px = int(self.border_val.get() * self.MM_TO_PX)
        text = self._get_effective_text()
        rect_h = 0
        if self.text_pos_var.get() == "below" and text != "":
            fs = 1; font = ImageFont.truetype("arial.ttf", fs)
            while font.getbbox(text)[2] - font.getbbox(text)[0] < (self.PHOTO_W - 2*int(self.config["fixed_distance_mm"]*self.MM_TO_PX)) and fs < 400:
                fs += 1; font = ImageFont.truetype("arial.ttf", fs)
            side_px = int(self.config.get("fixed_distance_mm", 3.5) * self.MM_TO_PX)
            bottom_px = int(self.config.get("fixed_bottom_mm", 3.5) * self.MM_TO_PX)
            top_px = int(self.config.get("fixed_top_p_mm", 0.35) * self.MM_TO_PX)
            rect_h = (font.getbbox(text)[3] - font.getbbox(text)[1]) + bottom_px + top_px
        
        avail_h = (self.PHOTO_H - 2*border_px) - rect_h
        eff_w = self.PHOTO_W - 2*border_px
        ratio_t, ratio_i = eff_w / avail_h, self.raw_img.width / self.raw_img.height
        self.current_scale = avail_h / self.raw_img.height if ratio_i > ratio_t else eff_w / self.raw_img.width
        self.pan_x = max(0, min(self.raw_img.width * self.current_scale - eff_w, self.pan_x))
        self.pan_y = max(0, min(self.raw_img.height * self.current_scale - avail_h, self.pan_y))

    def on_setting_change(self, *a): self.recalc_image_fit(); self.update_preview()
    def _on_border_entry(self, e=None):
        try:
            v = float(self.border_entry_var.get().strip().replace(',','.'))
        except Exception:
            v = self.border_val.get()
        min_b = float(self.config.get("border_min_mm", 0.0))
        max_b = float(self.config.get("border_max_mm", 3.5))
        v = max(min_b, min(max_b, v))
        self.border_val.set(v)
        self.border_entry_var.set(f"{v:.1f}")
        self.on_setting_change()
    def _clear_placeholder(self):
        if self.entry_text.get() == self._placeholder_text:
            self.entry_text.delete(0, tk.END)
            self.entry_text.config(fg="black")

    def _add_placeholder(self):
        if not self.entry_text.get().strip():
            self.entry_text.delete(0, tk.END)
            self.entry_text.insert(0, self._placeholder_text)
            self.entry_text.config(fg="grey")

    def _get_effective_text(self):
        t = self.entry_text.get()
        return "" if t == getattr(self, '_placeholder_text', '') else t

    def on_text_key_release(self, e):
        # debounce at 500ms to avoid slowdowns
        if self.debounce_id: self.root.after_cancel(self.debounce_id)
        self.debounce_id = self.root.after(500, lambda: [self.recalc_image_fit(), self.update_preview()])
    def load_image(self):
        p = filedialog.askopenfilename(); 
        if p: self.raw_img = Image.open(p).convert("RGB"); self.recalc_image_fit(); self.update_preview()
    def on_click(self, e): self.last_x, self.last_y = e.x, e.y
    def update_preview(self):
        if not self.raw_img: return
        p = self.create_final_image().crop((0, 0, self.PHOTO_W, self.PHOTO_H))
        self.tk_img = ImageTk.PhotoImage(p.resize((int(self.PHOTO_W*0.2), int(self.PHOTO_H*0.2)), Image.Resampling.LANCZOS))
        self.canvas.delete("all"); self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
    def save_check(self):
        if not self.raw_img: return
        t = self._get_effective_text(); fn = re.sub(r'[^\w\s\.-]', '', t).strip()[:150] or "druck"
        p = filedialog.asksaveasfilename(initialfile=fn, defaultextension=".jpg")
        if p: self.create_final_image().save(p, quality=98, dpi=(300,300))

if __name__ == "__main__":
    root = TkinterDnD.Tk() if DND_AVAILABLE else tk.Tk()
    app = PortraitProApp(root)
    root.mainloop()