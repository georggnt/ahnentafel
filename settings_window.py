import os
import re
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

from config_handler import ConfigHandler, MAX_MM_LIMIT

try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except Exception:
    DND_FILES = None
    DND_AVAILABLE = False

class SettingsWindow(tk.Toplevel):
    FRAME_PRESETS = {
        "Neuer Holzrahmen": {
            "photo_h_mm": 100.0,
            "photo_w_mm": 69.5,
            "canvas_h_mm": 130.0,
            "canvas_w_mm": 90.0,
            "border_default_mm": 3.0,
            "fixed_bottom_mm": 7.0,
            "fixed_distance_mm": 5.0,
        },
        "Alter Holzrahmen": {
            "photo_h_mm": 100.0,
            "photo_w_mm": 71.0,
            "canvas_h_mm": 130.0,
            "canvas_w_mm": 90.0,
            "border_default_mm": 1.7,
            "fixed_bottom_mm": 5.0,
            "fixed_distance_mm": 4.0,
        },
    }

    def __init__(self, parent, callback, is_initial=False):
        super().__init__(parent)
        self.title("Initial-Konfiguration v1.1.1")
        self.callback = callback
        self.is_initial = is_initial
        self.config = ConfigHandler.load() or ConfigHandler.get_default()
        if "background_source" not in self.config:
            self.config["background_source"] = "file" if self.config.get("use_background_image", False) else "colors"
        
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
        # Position window towards the top of the screen
        self.update_idletasks()
        screen_height = self.winfo_screenheight()
        screen_width = self.winfo_screenwidth()
        win_width = max(self.winfo_reqwidth(), 650)
        win_height = max(self.winfo_height(), 500)
        x_pos = (screen_width - win_width) // 2
        y_pos = max(50, int(screen_height * 0.1))  # 10% from top, min 50px
        self.geometry(f"{win_width}x{win_height}+{x_pos}+{y_pos}")

    def init_ui(self):
        outer = tk.Frame(self, padx=20, pady=20)
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        container = tk.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=container, anchor="nw")

        def _on_frame_configure(_e):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(e):
            canvas.itemconfigure(window_id, width=e.width)

        container.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        def _make_dim_row(row, label, ent_a, ent_b, val_a, val_b):
            tk.Label(container, text=label, font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky="w")
            ent_a.insert(0, f"{val_a:.2f}")
            ent_a.grid(row=row, column=1, pady=5)
            tk.Label(container, text=" H x B ").grid(row=row, column=2)
            ent_b.insert(0, f"{val_b:.2f}")
            ent_b.grid(row=row, column=3, pady=5)

        # Maße (H x B with tighter spacing)
        self.ent_ph = tk.Entry(container, width=8)
        self.ent_pw = tk.Entry(container, width=8)
        _make_dim_row(0, "Druck-Größe exakt für Rahmen (mm):", self.ent_ph, self.ent_pw, self.config["photo_h_mm"], self.config["photo_w_mm"])

        self.ent_ch = tk.Entry(container, width=8)
        self.ent_cw = tk.Entry(container, width=8)
        _make_dim_row(1, "Fotogröße (dm, Übergröße) (mm):", self.ent_ch, self.ent_cw, self.config["canvas_h_mm"], self.config["canvas_w_mm"])

        tk.Label(container, text="Farbanzahl:", font=('Arial', 9, 'bold')).grid(row=2, column=0, sticky="w", pady=10)
        self.mode_var = tk.IntVar(value=self.config["bund_mode"])
        self.dropdown = ttk.Combobox(container, textvariable=self.mode_var, values=[2, 3, 4, 5, 6], state="readonly", width=5)
        self.dropdown.grid(row=2, column=1, sticky="w")
        self.dropdown.bind("<<ComboboxSelected>>", self.update_color_rows)

        self.custom_pct_var = tk.BooleanVar(value=self.config.get("custom_pct", False))
        chk = tk.Checkbutton(container, text="Farbanteile manuell bearbeiten", variable=self.custom_pct_var, command=self.update_color_rows)
        chk.grid(row=2, column=2)

        self.show_advanced_var = tk.BooleanVar(value=self.config.get("show_advanced", self.is_initial))
        tk.Checkbutton(container, text="Erweiterte Einstellungen", variable=self.show_advanced_var, command=self._update_advanced_visibility).grid(row=2, column=3, sticky="w")

        self.color_frame = tk.LabelFrame(container, text="Farb-Stapel (Oben -> Unten)", padx=10, pady=10)
        self.color_frame.grid(row=3, column=0, columnspan=4, sticky="ew", pady=10)
        
        # Single source for background rendering (colors or file)
        self.bg_source_var = tk.StringVar(value=self.config.get("background_source", "colors"))
        
        self.color_rows = []
        self.update_color_rows()
        tk.Label(container, text="Hintergrundquelle:").grid(row=4, column=0, sticky="w", pady=(4, 2))
        tk.Radiobutton(container, text="Farben", variable=self.bg_source_var, value="colors", command=self._on_bg_toggle).grid(row=4, column=1, sticky="w", pady=(4, 2))
        tk.Radiobutton(container, text="Fahnen-Datei", variable=self.bg_source_var, value="file", command=self._on_bg_toggle).grid(row=4, column=2, sticky="w", pady=(4, 2))
        tk.Label(container, text="Datei:").grid(row=5, column=0, sticky="w")
        self.bg_path_var = tk.StringVar(value=self.config.get("background_image", ""))
        self.bg_entry = tk.Entry(container, textvariable=self.bg_path_var, width=42)
        self.bg_entry.grid(row=5, column=1, columnspan=2, sticky="w")
        self.bg_btn = tk.Button(container, text="Auswählen...", command=self._choose_background)
        self.bg_btn.grid(row=5, column=3, sticky="w")
        self._on_bg_toggle()

        if DND_AVAILABLE:
            try:
                self.drop_target_register(DND_FILES)
                self.dnd_bind('<<Drop>>', self._on_bg_drop)
            except Exception:
                pass

        # Advanced settings frame (hidden unless checkbox enabled)
        self.adv_frame = tk.LabelFrame(container, text="Erweiterte Einstellungen", padx=10, pady=8)
        self._build_advanced_frame()

        self._update_advanced_visibility()

        tk.Button(container, text="Einstellungen speichern", bg="#28a745", fg="white", font=("Arial", 10, "bold"), command=self.save_and_close).grid(row=7, column=0, columnspan=4, pady=10, sticky="ew")

    def update_color_rows(self, event=None):
        for widget in self.color_frame.winfo_children(): widget.destroy()
        self.color_rows = []
        num = self.mode_var.get()
        
        if not self.custom_pct_var.get():
            defaults = ConfigHandler.get_default_percentages(num)
            for i, val in enumerate(defaults): self.config["percentages"][i] = val

        use_bg_file = self.bg_source_var.get() == "file"

        # file background forces fixed, non-editable percentages
        if use_bg_file:
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
            
            if use_bg_file or not self.custom_pct_var.get():
                ent.config(state="disabled")

            if use_bg_file:
                btn.config(state="disabled")

            self.color_rows.append({"btn": btn, "ent": ent})

        self._update_advanced_visibility()

    def _update_advanced_visibility(self):
        try:
            if self.show_advanced_var.get():
                self.adv_frame.grid(row=6, column=0, columnspan=4, sticky="ew", pady=6)
            else:
                self.adv_frame.grid_forget()
        except Exception:
            pass

    @staticmethod
    def _set_entry(entry, value, digits=2):
        entry.delete(0, tk.END)
        entry.insert(0, f"{value:.{digits}f}")

    def _apply_preset(self, name):
        preset = self.FRAME_PRESETS.get((name or "").strip())
        if not preset:
            return

        self._set_entry(self.ent_ph, preset["photo_h_mm"], 2)
        self._set_entry(self.ent_pw, preset["photo_w_mm"], 2)
        self._set_entry(self.ent_ch, preset["canvas_h_mm"], 2)
        self._set_entry(self.ent_cw, preset["canvas_w_mm"], 2)

        # Advanced values controlled by the preset
        self._set_entry(self.ent_bottom, preset["fixed_bottom_mm"], 2)
        self._set_entry(self.ent_side, preset["fixed_distance_mm"], 2)

        # Keep border default in config; slider uses this at runtime.
        self.config["border_default_mm"] = preset["border_default_mm"]
        self.config["photo_h_mm"] = preset["photo_h_mm"]
        self.config["photo_w_mm"] = preset["photo_w_mm"]
        self.config["canvas_h_mm"] = preset["canvas_h_mm"]
        self.config["canvas_w_mm"] = preset["canvas_w_mm"]
        self.config["fixed_bottom_mm"] = preset["fixed_bottom_mm"]
        self.config["fixed_distance_mm"] = preset["fixed_distance_mm"]

        # Ensure border range still includes preset default.
        try:
            bmin = float(self.ent_border_min.get().strip().replace(',', '.'))
            bmax = float(self.ent_border_max.get().strip().replace(',', '.'))
            bdef = float(preset["border_default_mm"])
            if bdef < bmin:
                bmin = bdef
                self._set_entry(self.ent_border_min, bmin, 1)
            if bdef > bmax:
                bmax = bdef
                self._set_entry(self.ent_border_max, bmax, 1)
            self.config["border_min_mm"] = bmin
            self.config["border_max_mm"] = bmax
        except Exception:
            pass
    
    def _build_advanced_frame(self):
        """Create all advanced settings controls in the advanced frame."""
        tk.Label(self.adv_frame, text="Rahmen-Presets:", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w")
        tk.Button(
            self.adv_frame,
            text="Neuer Holzrahmen",
            command=lambda: self._apply_preset("Neuer Holzrahmen")
        ).grid(row=0, column=1, sticky="w")
        tk.Button(
            self.adv_frame,
            text="Alter Holzrahmen",
            command=lambda: self._apply_preset("Alter Holzrahmen")
        ).grid(row=0, column=2, sticky="w")

        # Numeric entry fields mapping
        entries_map = {
            "side": (1, "Text-Einzug Seiten (mm, max 7):", "fixed_distance_mm", 6.0, ".2f"),
            "bottom": (2, "Text-Einzug unten (mm, max 7):", "fixed_bottom_mm", 6.0, ".2f"),
            "top": (3, "Text-Einzug oben (mm, max 7):", "fixed_top_p_mm", 1.0, ".2f"),
            "tri": (6, "Dreieck-Kathete (% der Bildbreite):", "triangle_percent", 50.0, ".1f"),
            "border_min": (7, "Rahmen min (mm):", "border_min_mm", 0.0, ".1f"),
            "border_max": (8, "Rahmen max (mm, max 7):", "border_max_mm", 7.0, ".1f"),
        }
        
        for attr_name, (row, label, key, default, fmt) in entries_map.items():
            tk.Label(self.adv_frame, text=label).grid(row=row, column=0, sticky="w")
            entry = tk.Entry(self.adv_frame, width=8)
            value = self.config.get(key, default)
            entry.insert(0, f"{value:{fmt}}")
            entry.grid(row=row, column=1, sticky="w")
            setattr(self, f"ent_{attr_name}", entry)

        self._adv_fields = [
            ("fixed_distance_mm", self.ent_side, 2),
            ("fixed_bottom_mm", self.ent_bottom, 2),
            ("fixed_top_p_mm", self.ent_top, 2),
            ("triangle_percent", self.ent_tri, 1),
            ("border_min_mm", self.ent_border_min, 1),
            ("border_max_mm", self.ent_border_max, 1),
        ]
        
        # Text background color button
        tk.Label(self.adv_frame, text="Text-Hintergrundfarbe:").grid(row=4, column=0, sticky="w")
        self.text_bg = tk.StringVar(value=self.config.get("text_bg_color", "#FFFFFF"))
        self.text_bg_btn = tk.Button(self.adv_frame, text="Farbe wählen", command=self._pick_text_bg)
        self.text_bg_btn.grid(row=4, column=1, sticky="w")
        
        # Text color button
        tk.Label(self.adv_frame, text="Textfarbe:").grid(row=4, column=2, sticky="w", padx=(10, 0))
        self.text_color = tk.StringVar(value=self.config.get("text_color", "#000000"))
        self.text_color_btn = tk.Button(self.adv_frame, text="Farbe wählen", command=self._pick_text_color)
        self.text_color_btn.grid(row=4, column=3, sticky="w")

        # Text font
        tk.Label(self.adv_frame, text="Schriftart:").grid(row=5, column=0, sticky="w")
        self.text_font = tk.StringVar(value=self.config.get("text_font", "arial.ttf"))
        self.text_font_entry = tk.Entry(self.adv_frame, width=24, textvariable=self.text_font)
        self.text_font_entry.grid(row=5, column=1, columnspan=2, sticky="w")
        tk.Button(self.adv_frame, text="Auswählen...", command=self._pick_text_font).grid(row=5, column=3, sticky="w")
        
        # Reset button
        tk.Button(self.adv_frame, text="Erweiterte Einstellung wiederherstellen", command=self._restore_advanced).grid(row=9, column=0, columnspan=4, pady=6)

    def pick_color(self, idx):
        color = colorchooser.askcolor(initialcolor=self.config["colors"][idx])[1]
        if color:
            self.config["colors"][idx] = color
            self.color_rows[idx]["btn"].config(bg=color)

    def _pick_text_bg(self):
        color = colorchooser.askcolor(initialcolor=self.text_bg.get())[1]
        if color:
            self.text_bg.set(color)
    
    def _pick_text_color(self):
        color = colorchooser.askcolor(initialcolor=self.text_color.get())[1]
        if color:
            self.text_color.set(color)

    def _pick_text_font(self):
        fonts_dir = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
        p = filedialog.askopenfilename(
            initialdir=fonts_dir if os.path.exists(fonts_dir) else None,
            filetypes=[("Schriftarten", "*.ttf *.otf *.ttc")]
        )
        if p:
            self.text_font.set(p)

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
        is_file = self.bg_source_var.get() == "file"
        self.bg_entry.config(state="normal" if is_file else "disabled")
        self.bg_btn.config(state="normal" if is_file else "disabled")
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
        for key, entry, digits in self._adv_fields:
            entry.delete(0, tk.END)
            entry.insert(0, f"{d.get(key):.{digits}f}")
        self.text_bg.set(d.get('text_bg_color', "#FFFFFF"))
        self.text_color.set(d.get('text_color', "#000000"))
        self.text_font.set(d.get('text_font', "arial.ttf"))

    def save_and_close(self):
        try:
            # 100% Check
            total_pct = sum(float(self.color_rows[i]["ent"].get()) for i in range(self.mode_var.get()))
            if abs(total_pct - 100.0) > 0.01:
                messagebox.showerror("Fehler", f"Die Summe der Anteile muss exakt 100% ergeben!\nAktuell: {total_pct:.2f}%")
                return

            base_fields = {
                "photo_h_mm": self.ent_ph,
                "photo_w_mm": self.ent_pw,
                "canvas_h_mm": self.ent_ch,
                "canvas_w_mm": self.ent_cw,
            }
            for key, entry in base_fields.items():
                self.config[key] = float(entry.get())

            # Prevent accidental cm input in mm fields (e.g. 10 x 7 instead of 100 x 70).
            if self.config["photo_h_mm"] < 30 or self.config["photo_w_mm"] < 20:
                messagebox.showerror(
                    "Fehler",
                    "Fotogröße ist zu klein. Bitte Werte in mm eingeben, z.B. 90 x 70."
                )
                return

            canvas_h_mm = self.config["canvas_h_mm"]
            canvas_w_mm = self.config["canvas_w_mm"]
            if canvas_h_mm <= 0 or canvas_w_mm <= 0:
                messagebox.showerror("Fehler", "Druck-Größe muss größer als 0 mm sein.")
                return
            if canvas_h_mm < self.config["photo_h_mm"] or canvas_w_mm < self.config["photo_w_mm"]:
                messagebox.showerror(
                    "Fehler",
                    "Fotogröße (Übergröße) muss mindestens so groß wie die Rahmen-Größe sein."
                )
                return

            # Remove legacy keys once mm-based settings are saved.
            self.config.pop("canvas_h_cm", None)
            self.config.pop("canvas_w_cm", None)

            self.config["bund_mode"] = self.mode_var.get()
            self.config["custom_pct"] = self.custom_pct_var.get()
            self.config["show_advanced"] = bool(self.show_advanced_var.get())
            bg_source = self.bg_source_var.get().strip().lower()
            if bg_source not in ("colors", "file"):
                bg_source = "colors"
            self.config["background_source"] = bg_source
            self.config["use_background_image"] = (bg_source == "file")  # legacy compatibility
            self.config["background_image"] = self.bg_path_var.get().strip()

            if bg_source == "file":
                pcts = self._get_bg_percentages(self.config["bund_mode"])
                for i, val in enumerate(pcts):
                    self.config["percentages"][i] = val
            else:
                for i in range(self.config["bund_mode"]):
                    self.config["percentages"][i] = float(self.color_rows[i]["ent"].get())

            # advanced spacing values (mm) with 2 decimal places
            try:
                adv_values = {}
                for key, entry, digits in self._adv_fields:
                    adv_values[key] = round(float(entry.get().strip().replace(',','.')), digits)
            except Exception:
                messagebox.showerror("Fehler", "Ungültige erweiterte Einstellungen. Bitte Zahlen im Format 0.00 verwenden.")
                return

            # Keep frame and text inset limits in a print-safe range.
            mm_keys = ["fixed_distance_mm", "fixed_bottom_mm", "fixed_top_p_mm", "border_min_mm", "border_max_mm"]
            for key in mm_keys:
                if not (0.0 <= adv_values[key] <= MAX_MM_LIMIT):
                    messagebox.showerror("Fehler", f"{key} muss zwischen 0 und {MAX_MM_LIMIT:.0f} mm liegen.")
                    return
            if adv_values["border_min_mm"] > adv_values["border_max_mm"]:
                messagebox.showerror("Fehler", "Rahmen min darf nicht größer als Rahmen max sein.")
                return

            self.config.update(adv_values)
            self.config["text_bg_color"] = self.text_bg.get()
            self.config["text_color"] = self.text_color.get()
            self.config["text_font"] = self.text_font.get().strip()

            ConfigHandler.save(self.config)
            self.callback()
            self.destroy()
        except ValueError:
            messagebox.showerror("Fehler", "Bitte nur Zahlen eingeben.")

    def on_close(self):
        if self.is_initial: self.master.destroy()
        self.destroy()


