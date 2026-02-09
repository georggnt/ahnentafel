import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import re
import json
import os
import webbrowser

CONFIG_FILE = "config.json"

# Optional drag & drop support via tkinterdnd2 (if installed)
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except Exception:
    TkinterDnD = None
    DND_FILES = None
    DND_AVAILABLE = False

class ConfigHandler:
    @staticmethod
    def get_default_percentages(num):
        if num == 2: return [50.0, 50.0]
        if num == 3: return [33.33, 33.33, 33.34]
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
            "fixed_top_p_mm": 0.35, 
            "border_default_mm": 1.0
        }

    @staticmethod
    def load():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f: return json.load(f)
            except: return None
        return None

    @staticmethod
    def save(config):
        with open(CONFIG_FILE, "w") as f: json.dump(config, f, indent=4)

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, callback, is_initial=False):
        super().__init__(parent)
        self.title("Einstellungen v1.1.0")
        self.callback = callback
        self.is_initial = is_initial
        # Start from defaults and overlay any saved values (keeps missing keys)
        self.config = ConfigHandler.get_default()
        loaded = ConfigHandler.load()
        if loaded:
            self.config.update(loaded)
        
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.init_ui()

    def init_ui(self):
        container = tk.Frame(self, padx=20, pady=20)
        container.pack()

        # Fotomaße (mm)
        tk.Label(container, text="Fotomaße (mm):", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky="w")
        hb_frame = tk.Frame(container)
        hb_frame.grid(row=0, column=1, columnspan=2, pady=5, sticky="w")
        self.ent_ph = tk.Entry(hb_frame, width=8); self.ent_ph.insert(0, self.config["photo_h_mm"])
        self.ent_ph.pack(side="left")
        tk.Label(hb_frame, text=" H x B ").pack(side="left")
        self.ent_pw = tk.Entry(hb_frame, width=8); self.ent_pw.insert(0, self.config["photo_w_mm"])
        self.ent_pw.pack(side="left")

        # Druckformat (cm)
        tk.Label(container, text="Druckformat (cm):", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky="w")
        cb_frame = tk.Frame(container)
        cb_frame.grid(row=1, column=1, columnspan=2, pady=5, sticky="w")
        self.ent_ch = tk.Entry(cb_frame, width=8); self.ent_ch.insert(0, self.config["canvas_h_cm"])
        self.ent_ch.pack(side="left")
        tk.Label(cb_frame, text=" H x B ").pack(side="left")
        self.ent_cw = tk.Entry(cb_frame, width=8); self.ent_cw.insert(0, self.config["canvas_w_cm"])
        self.ent_cw.pack(side="left")

        # Farbanzahl Dropdown
        tk.Label(container, text="Farbanzahl:", font=('Arial', 9, 'bold')).grid(row=2, column=0, sticky="w", pady=10)
        self.mode_var = tk.IntVar(value=self.config["bund_mode"])
        self.dropdown = ttk.Combobox(container, textvariable=self.mode_var, values=[2, 3, 4, 5, 6], state="readonly", width=5)
        self.dropdown.grid(row=2, column=1, sticky="w")
        self.dropdown.bind("<<ComboboxSelected>>", self.update_advanced_ui)

        # Erweitert Checkbox
        self.custom_pct_var = tk.BooleanVar(value=self.config.get("custom_pct", False))
        tk.Checkbutton(container, text="Erweitert (Abstände & Prozente)", variable=self.custom_pct_var, command=self.update_advanced_ui).grid(row=2, column=2)

        # Container für Farben (Coleur) - stacked rows
        self.color_frame = tk.LabelFrame(container, text="Coleur (Oben -> Unten)", padx=10, pady=10)
        self.color_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)

        # Container für erweiterte Abstände (placed below the Coleur box)
        self.adv_spacing_frame = tk.Frame(container)
        self.adv_spacing_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=5)
        
        self.color_rows = []
        self.update_advanced_ui()

        tk.Button(container, text="Einstellungen speichern", bg="#28a745", fg="white", font=("Arial", 10, "bold"), command=self.save_and_close).grid(row=5, column=0, columnspan=3, pady=10, sticky="ew")

    def update_advanced_ui(self, event=None):
        # 1. Abstände aktualisieren
        for widget in self.adv_spacing_frame.winfo_children(): widget.destroy()
        if self.custom_pct_var.get():
            tk.Label(self.adv_spacing_frame, text="Einzug Außenkante (mm):").pack(side="left")
            self.ent_dist = tk.Entry(self.adv_spacing_frame, width=5); self.ent_dist.insert(0, self.config["fixed_distance_mm"])
            self.ent_dist.pack(side="left", padx=5)
            tk.Label(self.adv_spacing_frame, text="Puffer Oben (mm):").pack(side="left")
            self.ent_top_p = tk.Entry(self.adv_spacing_frame, width=5); self.ent_top_p.insert(0, self.config["fixed_top_p_mm"])
            self.ent_top_p.pack(side="left", padx=5)

        # 2. Farbreihen aktualisieren
        for widget in self.color_frame.winfo_children(): widget.destroy()
        self.color_rows = []
        num = self.mode_var.get()
        
        if not self.custom_pct_var.get():
            defaults = ConfigHandler.get_default_percentages(num)
            for i, val in enumerate(defaults): self.config["percentages"][i] = val

        for i in range(num):
            btn = tk.Button(self.color_frame, bg=self.config["colors"][i], width=12, text=f"Farbe {i+1}", relief="flat")
            btn.grid(row=i, column=0, padx=5, pady=2, sticky='w')
            ent = tk.Entry(self.color_frame, width=8)
            # ensure percentages list has enough entries
            try:
                ent.insert(0, f"{self.config['percentages'][i]:.2f}")
            except Exception:
                ent.insert(0, "0.00")
            ent.grid(row=i, column=1, padx=5)
            tk.Label(self.color_frame, text="%").grid(row=i, column=2)
            # bind click handler with button widget to avoid index races
            btn.config(command=(lambda b=btn, idx=i: self.pick_color(idx, b)))
            self.color_rows.append({"btn": btn, "ent": ent})

    def pick_color(self, idx, btn_widget=None):
        color = colorchooser.askcolor(initialcolor=self.config.get("colors", ["#FFFFFF"] * (idx+1))[idx])[1]
        if color:
            # ensure colors list is big enough
            while len(self.config.get("colors", [])) <= idx:
                self.config.setdefault("colors", []).append("#FFFFFF")
            self.config["colors"][idx] = color
            if btn_widget:
                try:
                    btn_widget.config(bg=color)
                    return
                except Exception:
                    pass
            if idx < len(self.color_rows):
                try:
                    self.color_rows[idx]["btn"].config(bg=color)
                except Exception:
                    pass

    def save_and_close(self):
        try:
            # Read percentage entries robustly (accept comma as decimal, empty->0)
            vals = []
            for i in range(self.mode_var.get()):
                s = self.color_rows[i]["ent"].get().strip()
                if not s:
                    s = "0"
                s = s.replace(',', '.')
                try:
                    v = float(s)
                except Exception:
                    messagebox.showerror("Fehler - Coleur", f"Ungültiger Prozentwert in Coleur #{i+1}: '{self.color_rows[i]['ent'].get()}'")
                    return
                vals.append(v)
            total_pct = sum(vals)
            if abs(total_pct - 100.0) > 0.01:
                messagebox.showerror("Fehler - Coleur", f"Die Summe der Coleur-Anteile muss 100% ergeben. Aktuell: {total_pct:.2f}%")
                return

            self.config["photo_h_mm"] = float(self.ent_ph.get())
            self.config["photo_w_mm"] = float(self.ent_pw.get())
            self.config["canvas_h_cm"] = float(self.ent_ch.get())
            self.config["canvas_w_cm"] = float(self.ent_cw.get())
            self.config["bund_mode"] = self.mode_var.get()
            self.config["custom_pct"] = self.custom_pct_var.get()
            
            if self.custom_pct_var.get():
                self.config["fixed_distance_mm"] = float(self.ent_dist.get())
                self.config["fixed_top_p_mm"] = float(self.ent_top_p.get())
            
            for i in range(self.config["bund_mode"]):
                # use already-parsed vals if available
                if i < len(vals):
                    self.config["percentages"][i] = vals[i]
                else:
                    s = self.color_rows[i]["ent"].get().strip().replace(',', '.') or '0'
                    self.config["percentages"][i] = float(s)

            ConfigHandler.save(self.config)
            self.callback(); self.destroy()
        except ValueError: messagebox.showerror("Fehler", "Bitte gültige Zahlenwerte eingeben.")

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
        else: self.init_main_ui()

    def on_initial_config_done(self):
        self.root.deiconify(); self.config = ConfigHandler.load(); self.init_main_ui()

    def show_settings_menu(self): SettingsWindow(self.root, self.refresh_config)

    def refresh_config(self):
        self.config = ConfigHandler.load()
        if hasattr(self, 'main_frame'): self.main_frame.destroy()
        self.init_main_ui()

    def init_main_ui(self):
        self.root.title(f"Ahnentafel Optimaldruck v1.1.0")
        # Top bar with Optionen + version + GitHub link on one line
        top_bar = tk.Frame(self.root)
        top_bar.pack(fill='x')
        tk.Button(top_bar, text="Optionen", command=self.show_settings_menu).pack(side='left', padx=6, pady=2)
        tk.Label(top_bar, text="v1.1.0").pack(side='left', padx=6)
        gh_link = tk.Label(top_bar, text="GitHub", fg="blue", cursor="hand2")
        gh_link.pack(side='left')
        gh_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/georggnt/ahnentafel"))

        self.main_frame = tk.Frame(self.root, padx=10, pady=10)
        self.main_frame.pack()

        self.DPI = 300
        self.MM_TO_PX = self.DPI / 25.4
        self.PHOTO_W = int(self.config["photo_w_mm"] * self.MM_TO_PX)
        self.PHOTO_H = int(self.config["photo_h_mm"] * self.MM_TO_PX)
        self.CANVAS_W = int(self.config["canvas_w_cm"] * 10 * self.MM_TO_PX)
        self.CANVAS_H = int(self.config["canvas_h_cm"] * 10 * self.MM_TO_PX)
        self.TRI_SIZE = int(min(self.PHOTO_W, self.PHOTO_H) * 0.50)
        self.raw_img, self.current_scale = None, 1.0
        self.pan_x = self.pan_y = self.last_x = self.last_y = 0

        ctrl = tk.Frame(self.main_frame); ctrl.pack(pady=5)
        tk.Button(ctrl, text="Bild laden", command=self.load_image).grid(row=0, column=0, padx=10)
        tk.Label(ctrl, text="Rahmen:").grid(row=0, column=1)
        self.border_val = tk.DoubleVar(value=self.config["border_default_mm"])
        tk.Scale(ctrl, from_=0, to=3.0, resolution=0.5, orient=tk.HORIZONTAL, variable=self.border_val, command=self.on_setting_change).grid(row=0, column=2, padx=5)
        self.use_triangle_var = tk.BooleanVar(value=False)
        tk.Checkbutton(ctrl, text="Dreieck", variable=self.use_triangle_var, command=self.update_preview).grid(row=0, column=3)

        # Placeholder suggestion (not actual text)
        self.placeholder = "Nachname, Vorname(n) rec. am TT.MM.YYYY"
        self.entry_text = tk.Entry(self.main_frame, width=65, fg='grey')
        self.entry_text.insert(0, self.placeholder)
        self.entry_text.bind("<FocusIn>", self.clear_placeholder)
        self.entry_text.bind("<FocusOut>", self.add_placeholder)
        self.entry_text.bind("<KeyRelease>", self.on_text_key_release)
        self.entry_text.pack(pady=5)

        pos_frame = tk.Frame(self.main_frame); pos_frame.pack()
        self.text_pos_var = tk.StringVar(value="below")
        tk.Radiobutton(pos_frame, text="Overlay", variable=self.text_pos_var, value="overlay", command=self.on_setting_change).pack(side="left")
        tk.Radiobutton(pos_frame, text="Darunter", variable=self.text_pos_var, value="below", command=self.on_setting_change).pack(side="left")

        self.canvas = tk.Canvas(self.main_frame, width=int(self.PHOTO_W*0.2), height=int(self.PHOTO_H*0.2), bg="#eee", highlightthickness=0)
        self.canvas.pack(pady=10); self.canvas.bind("<B1-Motion>", self.on_drag); self.canvas.bind("<Button-1>", self.on_click)

        # If tkinterdnd2 is available, register the root window to accept file drops
        if DND_AVAILABLE:
            try:
                self.root.drop_target_register(DND_FILES)
                self.root.dnd_bind('<<Drop>>', self.on_drop)
            except Exception:
                # Ignore if registration fails
                pass
        tk.Button(self.main_frame, text="Druck-Datei speichern", bg="#007bff", fg="white", command=self.save_check).pack(fill="x")

    def on_drag(self, e):
        if not self.raw_img: return
        dx = (e.x - self.last_x) / 0.2; dy = (e.y - self.last_y) / 0.2
        new_x = self.pan_x - dx; new_y = self.pan_y - dy
        border_px = int(self.border_val.get() * self.MM_TO_PX)
        eff_w = self.PHOTO_W - (2 * border_px)
        text = self.entry_text.get()
        if text == getattr(self, 'placeholder', None): text = ""
        rect_h = 0
        if self.text_pos_var.get() == "below" and text != "":
            cur_dist = self.config["fixed_distance_mm"] - self.border_val.get()
            fs = 1; font = ImageFont.truetype("arial.ttf", fs)
            target_w = self.PHOTO_W - 2*int(self.config["fixed_distance_mm"]*self.MM_TO_PX)
            while font.getbbox(text)[2] - font.getbbox(text)[0] < target_w and fs < 400:
                fs += 1; font = ImageFont.truetype("arial.ttf", fs)
            rect_h = (font.getbbox(text)[3]-font.getbbox(text)[1]) + int(cur_dist*self.MM_TO_PX) + int(self.config["fixed_top_p_mm"]*self.MM_TO_PX)
        avail_h = (self.PHOTO_H - 2*border_px) - rect_h
        img_w_scaled = self.raw_img.width * self.current_scale
        img_h_scaled = self.raw_img.height * self.current_scale
        self.pan_x = max(0, min(img_w_scaled - eff_w, new_x))
        self.pan_y = max(0, min(img_h_scaled - avail_h, new_y))
        self.last_x, self.last_y = e.x, e.y; self.update_preview()

    def create_final_image(self):
        border_px = int(self.border_val.get() * self.MM_TO_PX)
        cur_dist_px = int((self.config["fixed_distance_mm"] - self.border_val.get()) * self.MM_TO_PX)
        top_p_px = int(self.config["fixed_top_p_mm"] * self.MM_TO_PX)
        eff_w, eff_h = self.PHOTO_W - (2 * border_px), self.PHOTO_H - (2 * border_px)
        text = self.entry_text.get()
        if text == getattr(self, 'placeholder', None): text = ""
        # Try loading a TrueType font; fall back to default bitmap font if it fails
        fs = 1
        try:
            font = ImageFont.truetype("arial.ttf", fs)
            target_w = self.PHOTO_W - 2*int(self.config["fixed_distance_mm"]*self.MM_TO_PX)
            while font.getbbox(text)[2] - font.getbbox(text)[0] < target_w and fs < 400:
                fs += 1; font = ImageFont.truetype("arial.ttf", fs)
            font_h = font.getbbox(text)[3]-font.getbbox(text)[1]
        except Exception:
            font = ImageFont.load_default()
            try:
                font_h = font.getbbox(text)[3]-font.getbbox(text)[1]
            except Exception:
                font_h = 10
        rect_h = font_h + cur_dist_px + top_p_px 
        is_below = self.text_pos_var.get() == "below"
        avail_h = eff_h - rect_h if is_below else eff_h
        resized = self.raw_img.resize((int(self.raw_img.width * self.current_scale), int(self.raw_img.height * self.current_scale)), Image.Resampling.LANCZOS)
        crop = resized.crop((int(self.pan_x), int(self.pan_y), int(self.pan_x + eff_w), int(self.pan_y + avail_h)))
        nutz = Image.new("RGB", (self.PHOTO_W, self.PHOTO_H), "#FFFFFF")
        draw_n = ImageDraw.Draw(nutz)
        mode = self.config["bund_mode"]; cols = self.config["colors"]; pcts = self.config["percentages"]
        curr_y = 0
        for i in range(mode):
            seg_h = int((pcts[i] / 100.0) * self.PHOTO_H)
            y_end = curr_y + seg_h if i < mode-1 else self.PHOTO_H
            draw_n.rectangle([0, curr_y, border_px, y_end], fill=cols[i])
            draw_n.rectangle([self.PHOTO_W-border_px, curr_y, self.PHOTO_W, y_end], fill=cols[i])
            curr_y = y_end
        cont = Image.new("RGB", (eff_w, eff_h), "#FFFFFF")
        cont.paste(crop, (0, 0)); draw_c = ImageDraw.Draw(cont)
        if text != "":
            ry0 = eff_h - rect_h
            if not is_below: draw_c.rectangle([0, ry0, eff_w, eff_h], fill="#FFFFFF")
            tw = font.getbbox(text)[2] - font.getbbox(text)[0]
            draw_c.text((cur_dist_px + ((eff_w - 2*cur_dist_px - tw)//2), eff_h - cur_dist_px - font_h), text, fill="#000000", font=font)
        nutz.paste(cont, (border_px, border_px))
        if self.use_triangle_var.get():
            draw_n.polygon([(self.PHOTO_W, 0), (self.PHOTO_W-self.TRI_SIZE, 0), (self.PHOTO_W, self.TRI_SIZE)], fill="#000000")
            draw_n.line([(self.PHOTO_W-self.TRI_SIZE, 0), (self.PHOTO_W, self.TRI_SIZE)], fill="#FFFFFF", width=1)
        bg = Image.new("RGB", (self.CANVAS_W, self.CANVAS_H), "#000000"); draw_bg = ImageDraw.Draw(bg)
        curr_y = 0
        for i in range(mode):
            seg_h = int((pcts[i] / 100.0) * self.PHOTO_H)
            y_end = curr_y + seg_h if i < mode-1 else self.PHOTO_H
            draw_bg.rectangle([0, curr_y, self.CANVAS_W, y_end], fill=cols[i]); curr_y = y_end
        bg.paste(nutz, (0, 0)); return bg

    def recalc_image_fit(self):
        if not self.raw_img: return
        border_px = int(self.border_val.get() * self.MM_TO_PX)
        text = self.entry_text.get()
        if text == getattr(self, 'placeholder', None): text = ""
        rect_h = 0
        if self.text_pos_var.get() == "below" and text != "":
            # choose font size, but be tolerant if no TTF font available
            fs = 1
            try:
                font = ImageFont.truetype("arial.ttf", fs)
                target_w = self.PHOTO_W - 2*int(self.config["fixed_distance_mm"]*self.MM_TO_PX)
                while font.getbbox(text)[2] - font.getbbox(text)[0] < target_w and fs < 400:
                    fs += 1; font = ImageFont.truetype("arial.ttf", fs)
                txt_h = font.getbbox(text)[3] - font.getbbox(text)[1]
            except Exception:
                font = ImageFont.load_default()
                try:
                    txt_h = font.getbbox(text)[3] - font.getbbox(text)[1]
                except Exception:
                    txt_h = 10
            rect_h = txt_h + int((self.config["fixed_distance_mm"]-self.border_val.get())*self.MM_TO_PX) + int(self.config["fixed_top_p_mm"]*self.MM_TO_PX)
        avail_h = (self.PHOTO_H - 2*border_px) - rect_h; eff_w = self.PHOTO_W - 2*border_px
        ratio_t, ratio_i = eff_w / avail_h, self.raw_img.width / self.raw_img.height
        self.current_scale = avail_h / self.raw_img.height if ratio_i > ratio_t else eff_w / self.raw_img.width
        self.pan_x = max(0, min(self.raw_img.width * self.current_scale - eff_w, self.pan_x))
        self.pan_y = max(0, min(self.raw_img.height * self.current_scale - avail_h, self.pan_y))

    def on_setting_change(self, *a): self.recalc_image_fit(); self.update_preview()
    def on_text_key_release(self, e):
        if self.debounce_id: self.root.after_cancel(self.debounce_id)
        self.debounce_id = self.root.after(1000, lambda: [self.recalc_image_fit(), self.update_preview()])
    def clear_placeholder(self, event):
        if self.entry_text.get() == getattr(self, 'placeholder', None):
            self.entry_text.delete(0, tk.END)
            self.entry_text.config(fg='black')

    def add_placeholder(self, event):
        if not self.entry_text.get():
            self.entry_text.insert(0, getattr(self, 'placeholder', ''))
            self.entry_text.config(fg='grey')
    def load_image(self):
        p = filedialog.askopenfilename(filetypes=[("Bilder", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff")])
        if p: self.load_image_path(p)

    def load_image_path(self, path):
        try:
            img = Image.open(path).convert("RGB")
            self.raw_img = img
            self.recalc_image_fit(); self.update_preview()
        except Exception as ex:
            messagebox.showerror("Fehler beim Laden", f"Bild konnte nicht geladen werden:\n{ex}")

    def on_drop(self, event):
        # event.data may contain one or more file paths; handle typical formats
        data = event.data
        if not data: return
        # paths can be in form '{C:/path/to/file}' or 'C:/path/to/file'
        paths = re.findall(r"\{([^}]+)\}|([^\s]+)", data)
        files = []
        for a, b in paths:
            if a: files.append(a)
            elif b: files.append(b)
        if files:
            self.load_image_path(files[0])
    def on_click(self, e): self.last_x, self.last_y = e.x, e.y
    def update_preview(self):
        if not self.raw_img: return
        p = self.create_final_image().crop((0, 0, self.PHOTO_W, self.PHOTO_H))
        self.tk_img = ImageTk.PhotoImage(p.resize((int(self.PHOTO_W*0.2), int(self.PHOTO_H*0.2)), Image.Resampling.LANCZOS))
        self.canvas.delete("all"); self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
    def save_check(self):
        if not self.raw_img: return
        t = self.entry_text.get()
        if t == getattr(self, 'placeholder', None): t = ""
        fn = re.sub(r'[^\w\s\.-]', '', t).strip()[:150] or "druck"
        p = filedialog.asksaveasfilename(initialfile=fn, defaultextension=".jpg")
        if p: self.create_final_image().save(p, quality=98, dpi=(300,300))

if __name__ == "__main__":
    root = tk.Tk(); app = PortraitProApp(root); root.mainloop()