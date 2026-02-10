import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import re
import json
import os
import webbrowser

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
            "fixed_distance_mm": 3.5, "fixed_bottom_mm": 3.5, "fixed_top_p_mm": 0.35, "border_default_mm": 1.0
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
        self.title("Initial-Konfiguration v1.0.1")
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
        self.ent_ph = tk.Entry(container, width=8); self.ent_ph.insert(0, f"{self.config['photo_h_mm']:.2f}")
        self.ent_ph.grid(row=0, column=1, pady=5)
        tk.Label(container, text=" H x B ").grid(row=0, column=2)
        self.ent_pw = tk.Entry(container, width=8); self.ent_pw.insert(0, f"{self.config['photo_w_mm']:.2f}")
        self.ent_pw.grid(row=0, column=3, pady=5)

        tk.Label(container, text="Druck-Format (cm):", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky="w")
        self.ent_ch = tk.Entry(container, width=8); self.ent_ch.insert(0, f"{self.config['canvas_h_cm']:.2f}")
        self.ent_ch.grid(row=1, column=1, pady=5)
        tk.Label(container, text=" H x B ").grid(row=1, column=2)
        self.ent_cw = tk.Entry(container, width=8); self.ent_cw.insert(0, f"{self.config['canvas_w_cm']:.2f}")
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
        self.color_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)
        
        self.color_rows = []
        self.update_color_rows()

        # Advanced settings frame (hidden unless checkbox enabled)
        self.adv_frame = tk.LabelFrame(container, text="Erweiterte Einstellungen", padx=10, pady=8)
        # entries: Einzug zu den Seiten, Einzug/Abstand nach unten, Puffer nach oben
        tk.Label(self.adv_frame, text="Einzug zu den Seiten (mm):").grid(row=0, column=0, sticky="w")
        self.ent_side = tk.Entry(self.adv_frame, width=8)
        self.ent_side.insert(0, f"{self.config.get('fixed_distance_mm', 3.5):.2f}")
        self.ent_side.grid(row=0, column=1, sticky="w")

        tk.Label(self.adv_frame, text="Einzug/Abstand nach unten (mm):").grid(row=1, column=0, sticky="w")
        self.ent_bottom = tk.Entry(self.adv_frame, width=8)
        self.ent_bottom.insert(0, f"{self.config.get('fixed_bottom_mm', 3.5):.2f}")
        self.ent_bottom.grid(row=1, column=1, sticky="w")

        tk.Label(self.adv_frame, text="Puffer nach oben (mm):").grid(row=2, column=0, sticky="w")
        self.ent_top = tk.Entry(self.adv_frame, width=8)
        self.ent_top.insert(0, f"{self.config.get('fixed_top_p_mm', 0.35):.2f}")
        self.ent_top.grid(row=2, column=1, sticky="w")

        tk.Button(self.adv_frame, text="Erweiterte Einstellung wiederherstellen", command=self._restore_advanced).grid(row=3, column=0, columnspan=2, pady=6)

        # show adv_frame only if custom_pct_var true
        if self.custom_pct_var.get():
            self.adv_frame.grid(row=5, column=0, columnspan=4, sticky="ew", pady=6)

        tk.Button(container, text="Einstellungen speichern", bg="#28a745", fg="white", font=("Arial", 10, "bold"), command=self.save_and_close).grid(row=4, column=0, columnspan=3, pady=10, sticky="ew")

    def update_color_rows(self, event=None):
        for widget in self.color_frame.winfo_children(): widget.destroy()
        self.color_rows = []
        num = self.mode_var.get()
        
        if not self.custom_pct_var.get():
            defaults = ConfigHandler.get_default_percentages(num)
            for i, val in enumerate(defaults): self.config["percentages"][i] = val

        for i in range(num):
            row = tk.Frame(self.color_frame)
            row.pack(fill="x", pady=2)
            
            btn = tk.Button(row, bg=self.config["colors"][i], width=12, text=f"Farbe {i+1}", relief="flat", command=lambda idx=i: self.pick_color(idx))
            btn.pack(side="left", padx=5)

            ent = tk.Entry(row, width=8)
            ent.insert(0, f"{self.config['percentages'][i]:.2f}")
            ent.pack(side="left")
            tk.Label(row, text="%").pack(side="left")
            
            if not self.custom_pct_var.get():
                ent.config(state="disabled")

            self.color_rows.append({"btn": btn, "ent": ent})

        # toggle advanced frame visibility
        try:
            if self.custom_pct_var.get():
                self.adv_frame.grid(row=5, column=0, columnspan=4, sticky="ew", pady=6)
            else:
                self.adv_frame.grid_forget()
        except Exception:
            pass

    def pick_color(self, idx):
        color = colorchooser.askcolor(initialcolor=self.config["colors"][idx])[1]
        if color:
            self.config["colors"][idx] = color
            self.color_rows[idx]["btn"].config(bg=color)

    def _restore_advanced(self):
        if not messagebox.askyesno("Wiederherstellen", "Erweiterte Einstellungen auf Standardwerte zurücksetzen?"):
            return
        d = ConfigHandler.get_default()
        self.ent_side.delete(0, tk.END); self.ent_side.insert(0, f"{d.get('fixed_distance_mm',3.5):.2f}")
        self.ent_bottom.delete(0, tk.END); self.ent_bottom.insert(0, f"{d.get('fixed_bottom_mm',3.5):.2f}")
        self.ent_top.delete(0, tk.END); self.ent_top.insert(0, f"{d.get('fixed_top_p_mm',0.35):.2f}")

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
            for i in range(self.config["bund_mode"]):
                self.config["percentages"][i] = float(self.color_rows[i]["ent"].get())
            if self.custom_pct_var.get():
                # advanced spacing values (mm) with 2 decimal places
                try:
                    side = round(float(self.ent_side.get().strip().replace(',','.')), 2)
                    bottom = round(float(self.ent_bottom.get().strip().replace(',','.')), 2)
                    top = round(float(self.ent_top.get().strip().replace(',','.')), 2)
                except Exception:
                    messagebox.showerror("Fehler", "Ungültige erweiterte Einstellungen. Bitte Zahlen im Format 0.00 verwenden.")
                    return
                self.config["fixed_distance_mm"] = side
                self.config["fixed_bottom_mm"] = bottom
                self.config["fixed_top_p_mm"] = top

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
        self.init_main_ui()

    def init_main_ui(self):
        VERSION = "v1.0.1"
        GITHUB_URL = "https://github.com/georggnt/ahnentafel"
        self.root.title(f"Portrait-Pro-Tool {VERSION}")
        # toolbar: direct Optionen button, version and GitHub link on same line
        toolbar = tk.Frame(self.root, padx=6, pady=4)
        toolbar.pack(fill="x")
        tk.Button(toolbar, text="Optionen", command=self.show_settings_menu).pack(side="left")
        tk.Label(toolbar, text=VERSION).pack(side="left", padx=8)
        gh = tk.Label(toolbar, text="GitHub", fg="blue", cursor="hand2")
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
        self.TRI_SIZE = int(min(self.PHOTO_W, self.PHOTO_H) * 0.50)
        
        self.raw_img, self.current_scale = None, 1.0
        self.pan_x = self.pan_y = 0
        self.last_x = self.last_y = 0
        self.debounce_id = None

        # UI
        ctrl = tk.Frame(self.main_frame); ctrl.pack(pady=5)
        tk.Button(ctrl, text="Bild laden", command=self.load_image).grid(row=0, column=0, padx=10)
        tk.Label(ctrl, text="Rahmen (mm):").grid(row=0, column=1)
        self.border_val = tk.DoubleVar(value=self.config["border_default_mm"])
        tk.Scale(ctrl, from_=0.0, to=5.0, resolution=0.1, orient=tk.HORIZONTAL, variable=self.border_val, command=self.on_setting_change).grid(row=0, column=2, padx=5)
        self.use_triangle_var = tk.BooleanVar(value=False)
        tk.Checkbutton(ctrl, text="Dreieck", variable=self.use_triangle_var, command=self.update_preview).grid(row=0, column=3)

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
            rect_h = font_h + cur_dist_px + top_p_px
        else:
            font = ImageFont.truetype("arial.ttf", 12)
            font_h = 0
            rect_h = 0

        is_below = self.text_pos_var.get() == "below"
        avail_h = eff_h - rect_h if is_below else eff_h
        
        resized = self.raw_img.resize((int(self.raw_img.width * self.current_scale), int(self.raw_img.height * self.current_scale)), Image.Resampling.LANCZOS)
        crop = resized.crop((int(self.pan_x), int(self.pan_y), int(self.pan_x + eff_w), int(self.pan_y + avail_h)))
        
        nutz = Image.new("RGB", (self.PHOTO_W, self.PHOTO_H), "#FFFFFF")
        draw_n = ImageDraw.Draw(nutz)
        
        # Rahmen
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
            draw_c.text((side_px + ((eff_w - 2*side_px - tw)//2), eff_h - bottom_px - font_h), text, fill="#000000", font=font)
        
        nutz.paste(cont, (border_px, border_px))
        if self.use_triangle_var.get():
            draw_n.polygon([(self.PHOTO_W, 0), (self.PHOTO_W-self.TRI_SIZE, 0), (self.PHOTO_W, self.TRI_SIZE)], fill="#000000")
            draw_n.line([(self.PHOTO_W-self.TRI_SIZE, 0), (self.PHOTO_W, self.TRI_SIZE)], fill="#FFFFFF", width=1)
        
        bg = Image.new("RGB", (self.CANVAS_W, self.CANVAS_H), "#000000")
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
    root = tk.Tk()
    app = PortraitProApp(root)
    root.mainloop()