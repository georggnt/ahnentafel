import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont
import re
import json
import os

CONFIG_FILE = "config.json"

class ConfigHandler:
    @staticmethod
    def get_default():
        return {
            "photo_h_mm": 90.0,
            "photo_w_mm": 70.0,
            "canvas_h_cm": 15.0,
            "canvas_w_cm": 10.0,
            "bund_mode": 4, # 3, 4, 5 oder 6
            "colors": ["#FFFFFF", "#008000", "#eb0000", "#FFFFFF", "#FFFFFF", "#FFFFFF"],
            "fixed_distance_mm": 3.5,
            "fixed_top_p_mm": 0.35,
            "border_default_mm": 1.0
        }

    @staticmethod
    def load():
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return None

    @staticmethod
    def save(config):
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Konfiguration")
        self.callback = callback
        self.config = ConfigHandler.load() or ConfigHandler.get_default()
        self.color_buttons = []
        self.init_ui()

    def init_ui(self):
        # Maße
        row = 0
        tk.Label(self, text="Foto-Größe (H x B in mm):").grid(row=row, column=0, sticky="w", padx=5)
        self.ent_ph = tk.Entry(self, width=10); self.ent_ph.insert(0, self.config["photo_h_mm"])
        self.ent_ph.grid(row=row, column=1)
        self.ent_pw = tk.Entry(self, width=10); self.ent_pw.insert(0, self.config["photo_w_mm"])
        self.ent_pw.grid(row=row, column=2, padx=5)

        row += 1
        tk.Label(self, text="Druck-Format (H x B in cm):").grid(row=row, column=0, sticky="w", padx=5)
        self.ent_ch = tk.Entry(self, width=10); self.ent_ch.insert(0, self.config["canvas_h_cm"])
        self.ent_ch.grid(row=row, column=1)
        self.ent_cw = tk.Entry(self, width=10); self.ent_cw.insert(0, self.config["canvas_w_cm"])
        self.ent_cw.grid(row=row, column=2, padx=5)

        row += 1
        tk.Label(self, text="Farben des Bundes:").grid(row=row, column=0, sticky="w", padx=5, pady=10)
        self.mode_var = tk.IntVar(value=self.config["bund_mode"])
        mode_frame = tk.Frame(self)
        mode_frame.grid(row=row, column=1, columnspan=2)
        for m in [3, 4, 5, 6]:
            tk.Radiobutton(mode_frame, text=str(m), variable=self.mode_var, value=m, command=self.update_color_ui).pack(side="left")

        row += 1
        self.color_container = tk.Frame(self)
        self.color_container.grid(row=row, column=0, columnspan=3, pady=5)
        self.update_color_ui()

        row += 1
        tk.Button(self, text="Speichern & Starten", bg="green", fg="white", command=self.save_and_close).grid(row=row, column=0, columnspan=3, pady=15)

    def update_color_ui(self):
        for widget in self.color_container.winfo_children():
            widget.destroy()
        self.color_buttons = []
        num = self.mode_var.get()
        for i in range(num):
            btn = tk.Button(self.color_container, bg=self.config["colors"][i], width=4, 
                            command=lambda idx=i: self.pick_color(idx))
            btn.pack(side="left", padx=2)
            self.color_buttons.append(btn)

    def pick_color(self, idx):
        color = colorchooser.askcolor(initialcolor=self.config["colors"][idx])[1]
        if color:
            self.config["colors"][idx] = color
            self.color_buttons[idx].config(bg=color)

    def save_and_close(self):
        try:
            self.config["photo_h_mm"] = float(self.ent_ph.get())
            self.config["photo_w_mm"] = float(self.ent_pw.get())
            self.config["canvas_h_cm"] = float(self.ent_ch.get())
            self.config["canvas_w_cm"] = float(self.ent_cw.get())
            self.config["bund_mode"] = self.mode_var.get()
            ConfigHandler.save(self.config)
            self.callback()
            self.destroy()
        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige Zahlen eingeben.")

class PortraitProApp:
    def __init__(self, root):
        self.root = root
        self.config = ConfigHandler.load()
        if not self.config:
            self.show_settings()
            return
        self.init_main_ui()

    def show_settings(self):
        SettingsWindow(self.root, self.on_config_done)

    def on_config_done(self):
        self.config = ConfigHandler.load()
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy()
        self.init_main_ui()

    def init_main_ui(self):
        self.root.title(f"Portrait-Pro-Tool v5.0 ({int(self.config['photo_w_mm']/10)}x{int(self.config['photo_h_mm']/10)})")
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # Menü
        menubar = tk.Menu(self.root)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Einstellungen bearbeiten", command=self.show_settings)
        menubar.add_cascade(label="Optionen", menu=settings_menu)
        self.root.config(menu=menubar)

        # DPI & Maße
        self.DPI = 300
        self.MM_TO_PX = self.DPI / 25.4
        self.PHOTO_W = int(self.config["photo_w_mm"] * self.MM_TO_PX)
        self.PHOTO_H = int(self.config["photo_h_mm"] * self.MM_TO_PX)
        self.CANVAS_W = int(self.config["canvas_w_cm"] * 10 * self.MM_TO_PX)
        self.CANVAS_H = int(self.config["canvas_h_cm"] * 10 * self.MM_TO_PX)
        
        self.TRI_SIZE = int(max(self.PHOTO_W, self.PHOTO_H) * 0.50) if "50%" in str(self.config.get("tri_mode","")) else int(min(self.PHOTO_W, self.PHOTO_H) * 0.50)
        
        self.raw_img, self.current_scale = None, 1.0
        self.pan_x = self.pan_y = 0
        self.debounce_id = None
        self.placeholder = "Nachname, Vorname(n) rec. am TT.MM.YYYY"

        # UI Komponenten
        ctrl_frame = tk.Frame(self.main_frame); ctrl_frame.pack(pady=5)
        tk.Button(ctrl_frame, text="Bild laden", command=self.load_image).grid(row=0, column=0, padx=10)
        
        tk.Label(ctrl_frame, text="Rahmen (mm):").grid(row=0, column=1)
        self.border_val = tk.DoubleVar(value=self.config["border_default_mm"])
        tk.Scale(ctrl_frame, from_=0, to=3.0, resolution=0.5, orient=tk.HORIZONTAL, variable=self.border_val, command=self.on_setting_change).grid(row=0, column=2, padx=5)

        self.use_triangle_var = tk.BooleanVar(value=False)
        tk.Checkbutton(ctrl_frame, text="schwarzes Dreieck", variable=self.use_triangle_var, command=self.update_preview).grid(row=0, column=3)

        self.entry_text = tk.Entry(self.main_frame, width=60, fg='grey')
        self.entry_text.insert(0, self.placeholder)
        self.entry_text.bind("<FocusIn>", self.clear_placeholder); self.entry_text.bind("<FocusOut>", self.add_placeholder)
        self.entry_text.bind("<KeyRelease>", self.on_text_key_release); self.entry_text.pack(pady=5)

        self.text_pos_var = tk.StringVar(value="below")
        radio_frame = tk.Frame(self.main_frame); radio_frame.pack()
        tk.Radiobutton(radio_frame, text="Overlay", variable=self.text_pos_var, value="overlay", command=self.on_setting_change).pack(side="left")
        tk.Radiobutton(radio_frame, text="Darunter", variable=self.text_pos_var, value="below", command=self.on_setting_change).pack(side="left")

        self.canvas = tk.Canvas(self.main_frame, width=int(self.PHOTO_W * 0.2), height=int(self.PHOTO_H * 0.2), bg="white", highlightthickness=0)
        self.canvas.pack(pady=10); self.canvas.bind("<B1-Motion>", self.on_drag); self.canvas.bind("<Button-1>", self.on_click)

        tk.Button(self.main_frame, text="Speichern für Druck", bg="green", fg="white", font=("Arial", 10, "bold"), command=self.save_check).pack(pady=5)

    # --- LOGIK ---
    def create_complex_background(self):
        bg = Image.new("RGB", (self.CANVAS_W, self.CANVAS_H), "#000000")
        draw = ImageDraw.Draw(bg)
        mode = self.config["bund_mode"]
        cols = self.config["colors"]
        h = self.PHOTO_H

        segments = [] # (y_start, y_end, color)
        if mode == 3:
            s = h // 3
            segments = [(0, s, cols[0]), (s, 2*s, cols[1]), (2*s, h, cols[2])]
        elif mode == 4:
            s = h // 4
            segments = [(0, s, cols[0]), (s, 2*s, cols[1]), (2*s, 3*s, cols[2]), (3*s, h, cols[3])]
        elif mode == 5:
            p5 = int(h * 0.05); p30 = int(h * 0.30)
            segments = [(0, p5, cols[0]), (p5, p5+p30, cols[1]), (p5+p30, p5+2*p30, cols[2]), (p5+2*p30, h-p5, cols[3]), (h-p5, h, cols[4])]
        elif mode == 6:
            p5 = int(h * 0.05); p22 = int(h * 0.225)
            segments = [(0, p5, cols[0]), (p5, p5+p22, cols[1]), (p5+p22, p5+2*p22, cols[2]), (p5+2*p22, p5+3*p22, cols[3]), (p5+3*p22, h-p5, cols[4]), (h-p5, h, cols[5])]

        for y0, y1, col in segments:
            draw.rectangle([0, y0, self.CANVAS_W, y1], fill=col)
        return bg

    def draw_colored_border(self, draw, w, h, thickness):
        if thickness <= 0: return
        mode = self.config["bund_mode"]
        cols = self.config["colors"]
        
        segments = []
        if mode == 3:
            s = h // 3; segments = [(s, 2*s, cols[1])]
        elif mode == 4:
            s = h // 4; segments = [(s, 2*s, cols[1]), (2*s, 3*s, cols[2])]
        elif mode == 5:
            p5 = int(h * 0.05); p30 = int(h * 0.30)
            segments = [(p5, p5+p30, cols[1]), (p5+p30, p5+2*p30, cols[2]), (p5+2*p30, h-p5, cols[3])]
        elif mode == 6:
            p5 = int(h * 0.05); p22 = int(h * 0.225)
            segments = [(p5, p5+p22, cols[1]), (p5+p22, p5+2*p22, cols[2]), (p5+2*p22, p5+3*p22, cols[3]), (p5+3*p22, h-p5, cols[4])]

        for y0, y1, col in segments:
            draw.rectangle([0, y0, thickness, y1], fill=col)
            draw.rectangle([w-thickness, y0, w, y1], fill=col)

    def recalc_image_fit(self):
        if not self.raw_img: return
        border_px = int(self.border_val.get() * self.MM_TO_PX / 10)
        eff_w, eff_h = self.PHOTO_W - (2 * border_px), self.PHOTO_H - (2 * border_px)
        text = self.entry_text.get()
        has_t = text and text != self.placeholder
        rect_h = 0
        if has_t and self.text_pos_var.get() == "below":
            cur_dist = self.config["fixed_distance_mm"] - self.border_val.get()
            bottom_p, top_p = int(cur_dist * self.MM_TO_PX), int(self.config["fixed_top_p_mm"] * self.MM_TO_PX)
            fs = 1; font = ImageFont.truetype("arial.ttf", fs)
            target_w = self.PHOTO_W - (2 * int(self.config["fixed_distance_mm"] * self.MM_TO_PX))
            while font.getbbox(text)[2] - font.getbbox(text)[0] < target_w and fs < 400:
                fs += 1; font = ImageFont.truetype("arial.ttf", fs)
            rect_h = (font.getbbox(text)[3] - font.getbbox(text)[1]) + bottom_p + top_p
        
        avail_h = eff_h - rect_h
        ratio_t, ratio_i = eff_w / avail_h, self.raw_img.width / self.raw_img.height
        self.current_scale = avail_h / self.raw_img.height if ratio_i > ratio_t else eff_w / self.raw_img.width
        self.pan_x = max(0, min(self.raw_img.width * self.current_scale - eff_w, self.pan_x))
        self.pan_y = max(0, min(self.raw_img.height * self.current_scale - avail_h, self.pan_y))

    def create_final_image(self):
        border_mm = self.border_val.get()
        border_px = int(border_mm * self.MM_TO_PX)
        cur_pad_px = int((self.config["fixed_distance_mm"] - border_mm) * self.MM_TO_PX)
        top_p_px = int(self.config["fixed_top_p_mm"] * self.MM_TO_PX)
        
        eff_w, eff_h = self.PHOTO_W - (2 * border_px), self.PHOTO_H - (2 * border_px)
        text = self.entry_text.get(); has_t = text and text != self.placeholder
        
        rect_h = 0
        if has_t:
            fs = 1; font = ImageFont.truetype("arial.ttf", fs)
            target_w = self.PHOTO_W - (2 * int(self.config["fixed_distance_mm"] * self.MM_TO_PX))
            while font.getbbox(text)[2] - font.getbbox(text)[0] < target_w and fs < 400:
                fs += 1; font = ImageFont.truetype("arial.ttf", fs)
            font_h = font.getbbox(text)[3] - font.getbbox(text)[1]
            rect_h = font_h + cur_pad_px + top_p_px 

        is_below = self.text_pos_var.get() == "below" and has_t
        avail_h = eff_h - rect_h if is_below else eff_h
        
        resized = self.raw_img.resize((int(self.raw_img.width * self.current_scale), int(self.raw_img.height * self.current_scale)), Image.Resampling.LANCZOS)
        crop = resized.crop((int(self.pan_x), int(self.pan_y), int(self.pan_x + eff_w), int(self.pan_y + avail_h)))
        
        nutz = Image.new("RGB", (self.PHOTO_W, self.PHOTO_H), "#FFFFFF")
        draw_n = ImageDraw.Draw(nutz)
        self.draw_colored_border(draw_n, self.PHOTO_W, self.PHOTO_H, border_px)
        
        cont = Image.new("RGB", (eff_w, eff_h), "#FFFFFF")
        cont.paste(crop, (0, 0)); draw_c = ImageDraw.Draw(cont)
        if has_t:
            ry0 = eff_h - rect_h
            if not is_below: draw_c.rectangle([0, ry0, eff_w, eff_h], fill="#FFFFFF")
            tw = font.getbbox(text)[2] - font.getbbox(text)[0]
            draw_c.text((cur_pad_px + ((eff_w - 2*cur_pad_px - tw)//2), eff_h - cur_pad_px - (font.getbbox(text)[3]-font.getbbox(text)[1])), text, fill="#000000", font=font)
        
        nutz.paste(cont, (border_px, border_px))
        if self.use_triangle_var.get():
            p1, p2, p3 = (self.PHOTO_W, 0), (self.PHOTO_W - self.TRI_SIZE, 0), (self.PHOTO_W, self.TRI_SIZE)
            draw_n.polygon([p1, p2, p3], fill="#000000")
            draw_n.line([p2, p3], fill="#FFFFFF", width=1)

        canvas = self.create_complex_background()
        canvas.paste(nutz, (0, 0))
        return canvas

    # --- UI HELPERS ---
    def on_setting_change(self, *args): self.recalc_image_fit(); self.update_preview()
    def on_text_key_release(self, event):
        if self.debounce_id: self.root.after_cancel(self.debounce_id)
        self.debounce_id = self.root.after(1000, lambda: [self.recalc_image_fit(), self.update_preview()])
    def clear_placeholder(self, e):
        if self.entry_text.get() == self.placeholder: self.entry_text.delete(0, tk.END); self.entry_text.config(fg='black')
    def add_placeholder(self, e):
        if not self.entry_text.get(): self.entry_text.insert(0, self.placeholder); self.entry_text.config(fg='grey')
    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Bilder", "*.jpg *.jpeg *.png")])
        if path: self.raw_img = Image.open(path).convert("RGB"); self.recalc_image_fit(); self.update_preview()
    def on_click(self, e): self.last_x, self.last_y = e.x, e.y
    def on_drag(self, e):
        if not self.raw_img: return
        self.pan_x -= (e.x - self.last_x) / 0.2; self.pan_y -= (e.y - self.last_y) / 0.2
        self.last_x, self.last_y = e.x, e.y; self.update_preview()
    def update_preview(self):
        if not self.raw_img: return
        final = self.create_final_image().crop((0, 0, self.PHOTO_W, self.PHOTO_H))
        self.tk_img = ImageTk.PhotoImage(final.resize((int(self.PHOTO_W * 0.2), int(self.PHOTO_H * 0.2)), Image.Resampling.LANCZOS))
        self.canvas.delete("all"); self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
    def save_check(self):
        if not self.raw_img: return
        text = self.entry_text.get(); init_n = re.sub(r'[^\w\s\.-]', '', text).strip()[:150] if text != self.placeholder else "druck"
        path = filedialog.asksaveasfilename(initialfile=init_n, defaultextension=".jpg")
        if path: self.create_final_image().save(path, quality=98, dpi=(300, 300))

if __name__ == "__main__":
    root = tk.Tk()
    app = PortraitProApp(root)
    root.mainloop()