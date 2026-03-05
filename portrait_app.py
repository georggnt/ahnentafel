import re
import math
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageDraw, ImageFont, ImageTk

from config_handler import ConfigHandler, MAX_MM_LIMIT
from settings_window import SettingsWindow

class PortraitProApp:
    PREVIEW_SCALE = 0.35
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

    def _get_text_font(self, size):
        font_name = self.config.get("text_font", "arial.ttf")
        if not font_name:
            font_name = "arial.ttf"
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            try:
                return ImageFont.truetype("arial.ttf", size)
            except Exception:
                return ImageFont.load_default()

    def _mm_to_px(self, mm_value, ceil_value=False):
        px = float(mm_value) * self.MM_TO_PX
        if ceil_value:
            return max(1, int(math.ceil(px - 1e-9)))
        return max(1, int(round(px)))

    @staticmethod
    def _is_near_int(value, tol=1e-7):
        return abs(value - round(value)) <= tol

    def _find_effective_dpi(self, width_mm, height_mm, min_dpi=300, max_dpi=1200):
        """Pick the smallest DPI >= min_dpi that maps both mm sides to integer pixels."""
        start = max(1, int(math.ceil(float(min_dpi))))
        w_mm = float(width_mm)
        h_mm = float(height_mm)
        if w_mm <= 0 or h_mm <= 0:
            return float(start)

        for dpi in range(start, max_dpi + 1):
            w_px = (w_mm / 25.4) * dpi
            h_px = (h_mm / 25.4) * dpi
            if self._is_near_int(w_px) and self._is_near_int(h_px):
                return float(dpi)
        return float(start)

    def _calc_text_font(self, text):
        if not text:
            return self._get_text_font(12)
        fs = 1
        font = self._get_text_font(fs)
        side_mm = max(0.0, min(MAX_MM_LIMIT, float(self.config.get("fixed_distance_mm", 6.0))))
        max_w = max(1, self.PHOTO_W - 2 * self._mm_to_px(side_mm) - 2)
        while font.getbbox(text)[2] - font.getbbox(text)[0] < max_w and fs < 400:
            fs += 1
            font = self._get_text_font(fs)
        return font

    def _calc_text_block(self, text):
        if not text:
            return None, 0, 0, 0, 0, 0, 0, 0, 0
        font = self._calc_text_font(text)
        bbox = font.getbbox(text)
        font_h = bbox[3] - bbox[1]
        text_w = bbox[2] - bbox[0]
        text_top = bbox[1]
        text_bottom = bbox[3]
        side_mm = max(0.0, min(MAX_MM_LIMIT, float(self.config.get("fixed_distance_mm", 6.0))))
        bottom_mm = max(0.0, min(MAX_MM_LIMIT, float(self.config.get("fixed_bottom_mm", 6.0))))
        top_mm = max(0.0, min(MAX_MM_LIMIT, float(self.config.get("fixed_top_p_mm", 1.0))))
        side_px = self._mm_to_px(side_mm)
        bottom_px = self._mm_to_px(bottom_mm)
        top_px = self._mm_to_px(top_mm)
        # Small safety padding prevents anti-aliased glyph pixels from being clipped.
        rect_h = font_h + bottom_px + top_px + 2
        return font, rect_h, font_h, side_px, bottom_px, top_px, text_w, text_top, text_bottom

    def _get_effective_border_px(self):
        req = int(float(self.border_val.get()) * self.MM_TO_PX)
        max_allowed = max(0, (min(self.PHOTO_W, self.PHOTO_H) - 2) // 2)
        return max(0, min(req, max_allowed))

    def _px_to_mm(self, px):
        return px / self.MM_TO_PX

    def _draw_dimension_info(self):
        if not hasattr(self, "dim_canvas"):
            return

        c = self.dim_canvas
        c.delete("all")

        # Motif/frame size (exact cut size)
        motif_w_mm = float(self.config.get("photo_w_mm", 70.0))
        motif_h_mm = float(self.config.get("photo_h_mm", 90.0))

        border_mm_req = float(self.border_val.get()) if hasattr(self, "border_val") else float(self.config.get("border_default_mm", 2.3))
        border_mm_max = max(0.0, (min(motif_w_mm, motif_h_mm) - 0.2) / 2.0)
        border_mm = min(border_mm_req, border_mm_max)
        inner_w_mm = max(0.0, motif_w_mm - 2 * border_mm)
        inner_h_mm = max(0.0, motif_h_mm - 2 * border_mm)

        side_mm = max(0.0, min(MAX_MM_LIMIT, float(self.config.get("fixed_distance_mm", 6.0))))
        bottom_mm = max(0.0, min(MAX_MM_LIMIT, float(self.config.get("fixed_bottom_mm", 6.0))))
        top_mm = max(0.0, min(MAX_MM_LIMIT, float(self.config.get("fixed_top_p_mm", 1.0))))

        text = self._get_effective_text() if hasattr(self, "entry_text") else ""
        _, text_h_px, font_h_px, _, _, _, _, _, _ = self._calc_text_block(text)
        has_text = bool(text) and text_h_px > 0
        text_h_mm = self._px_to_mm(text_h_px) if has_text else 0.0
        font_h_mm = self._px_to_mm(font_h_px) if has_text else 0.0
        image_h_mm = max(0.0, inner_h_mm - text_h_mm) if has_text else inner_h_mm

        text_block_top_mm_inner = max(0.0, inner_h_mm - text_h_mm) if has_text else 0.0
        text_block_top_mm_motif = border_mm + text_block_top_mm_inner if has_text else 0.0
        text_start_mm_motif = text_block_top_mm_motif + top_mm if has_text else 0.0

        cw = int(c.cget("width"))
        ch = int(c.cget("height"))

        # Technical drawing placement (motif only)
        pad_left = 78
        pad_top = 24
        max_w = max(20, cw - pad_left - 44)
        max_h = max(20, ch - pad_top - 72)
        scale = min(max_w / max(motif_w_mm, 0.1), max_h / max(motif_h_mm, 0.1))

        x0 = pad_left
        y0 = pad_top
        x1 = x0 + motif_w_mm * scale
        y1 = y0 + motif_h_mm * scale

        bi = border_mm * scale
        ix0, iy0 = x0 + bi, y0 + bi
        ix1, iy1 = x1 - bi, y1 - bi

        # Flag border zones (left/right): visualize where the colored border sits.
        mode = int(self.config.get("bund_mode", 4))
        cols = self.config.get("colors", ["#FFFFFF", "#008000", "#eb0000", "#FFFFFF"])
        pcts = self.config.get("percentages", [25.0, 25.0, 25.0, 25.0])
        if border_mm > 0:
            curr_y = y0
            for i in range(mode):
                pct = pcts[i] if i < len(pcts) else 0.0
                seg_h = (pct / 100.0) * (y1 - y0)
                y_end = curr_y + seg_h if i < mode - 1 else y1
                col = cols[i] if i < len(cols) else "#CCCCCC"
                c.create_rectangle(x0, curr_y, ix0, y_end, outline="", fill=col)
                c.create_rectangle(ix1, curr_y, x1, y_end, outline="", fill=col)
                curr_y = y_end

        # Motif and inner image bounds
        c.create_rectangle(x0, y0, x1, y1, outline="#111", width=2)

        # Inner image area inside frame border
        c.create_rectangle(ix0, iy0, ix1, iy1, outline="#1f77b4", width=1, dash=(4, 3))

        text_area_top = iy1 - (text_h_mm * scale)
        if has_text:
            c.create_rectangle(ix0, text_area_top, ix1, iy1, outline="#8c6d1f", fill="#fff3cd", width=1)
            text_start_y = text_area_top + top_mm * scale
            text_x_left = ix0 + side_mm * scale
            text_x_right = ix1 - side_mm * scale
            c.create_line(ix0, text_start_y, ix1, text_start_y, fill="#b35300", dash=(3, 2))
            c.create_line(text_x_left, text_area_top, text_x_left, iy1, fill="#b35300", dash=(3, 2))
            c.create_line(text_x_right, text_area_top, text_x_right, iy1, fill="#b35300", dash=(3, 2))
            c.create_text((text_x_left + text_x_right) / 2, text_start_y - 8, text="Schrift beginnt hier", fill="#b35300", font=("Arial", 8, "bold"))

        # Helper to draw extension lines + dimension arrow + centered label
        def dim_h(xa, xb, y, label):
            c.create_line(xa, y + 2, xa, y0, fill="#666")
            c.create_line(xb, y + 2, xb, y0, fill="#666")
            c.create_line(xa, y, xb, y, fill="#333", arrow=tk.BOTH)
            c.create_text((xa + xb) / 2, y - 10, text=label, fill="#111", font=("Arial", 8, "bold"))

        def dim_v(x, ya, yb, label):
            c.create_line(x + 2, ya, x0, ya, fill="#666")
            c.create_line(x + 2, yb, x0, yb, fill="#666")
            c.create_line(x, ya, x, yb, fill="#333", arrow=tk.BOTH)
            c.create_text(x - 20, (ya + yb) / 2, text=label, fill="#111", anchor="e", font=("Arial", 8, "bold"))

        # Motif overall size
        dim_h(x0, x1, y0 - 12, f"Motivbreite {motif_w_mm:.1f} mm")
        dim_v(x0 - 14, y0, y1, f"Motivhöhe {motif_h_mm:.1f} mm")

        # Inner image width
        c.create_line(ix0, y1, ix0, y1 + 30, fill="#666")
        c.create_line(ix1, y1, ix1, y1 + 30, fill="#666")
        c.create_line(ix0, y1 + 28, ix1, y1 + 28, fill="#1f77b4", arrow=tk.BOTH)
        c.create_text((ix0 + ix1) / 2, y1 + 40, text=f"Bildbreite innen {inner_w_mm:.1f} mm", fill="#1f77b4", font=("Arial", 8, "bold"))

        # border thickness on top edge
        if border_mm > 0:
            c.create_line(x0, y0 + 10, ix0, y0 + 10, fill="#444", arrow=tk.BOTH)
            c.create_text((x0 + ix0) / 2, y0 + 20, text=f"Rahmen {border_mm:.1f} mm", fill="#444", font=("Arial", 8))
            c.create_text((x0 + ix0) / 2, y0 + 34, text="Fahnen-Rahmen", fill="#444", font=("Arial", 8))

        # text area height (if present)
        if has_text:
            c.create_line(x1 + 8, text_area_top, x1 + 24, text_area_top, fill="#8c6d1f")
            c.create_line(x1 + 8, iy1, x1 + 24, iy1, fill="#8c6d1f")
            c.create_line(x1 + 22, text_area_top, x1 + 22, iy1, fill="#8c6d1f", arrow=tk.BOTH)
            c.create_text(x1 + 28, text_area_top - 6, text=f"Schriftfeld {text_h_mm:.1f} mm", fill="#8c6d1f", anchor="w", font=("Arial", 8, "bold"))

            # Side inset dimension
            tx0 = ix0 + side_mm * scale
            c.create_line(ix0, iy1 + 8, ix0, iy1 + 22, fill="#b35300")
            c.create_line(tx0, iy1 + 8, tx0, iy1 + 22, fill="#b35300")
            c.create_line(ix0, iy1 + 20, tx0, iy1 + 20, fill="#b35300", arrow=tk.BOTH)
            c.create_text((ix0 + tx0) / 2, iy1 + 32, text=f"Einzug {side_mm:.1f} mm", fill="#b35300", font=("Arial", 8))

        if hasattr(self, "dim_values_var"):
            lines = [
                f"Motivbreite:         {motif_w_mm:6.2f} mm",
                f"Motivhöhe:           {motif_h_mm:6.2f} mm",
                f"Fahnen-Rahmen je S.: {border_mm:6.2f} mm",
                f"Bildbreite innen:    {inner_w_mm:6.2f} mm",
                f"Bildhöhe innen:      {inner_h_mm:6.2f} mm",
                f"Bildhöhe Ausschnitt: {image_h_mm:6.2f} mm",
            ]
            if has_text:
                lines.extend([
                    f"Schriftfeld startet: {text_block_top_mm_motif:6.2f} mm von oben",
                    f"Schrift beginnt:     {text_start_mm_motif:6.2f} mm von oben",
                    f"Text-Einzug Seite:   {side_mm:6.2f} mm",
                    f"Text-Einzug oben:    {top_mm:6.2f} mm",
                    f"Text-Einzug unten:   {bottom_mm:6.2f} mm",
                    f"Schriftfeldhöhe:     {text_h_mm:6.2f} mm",
                    f"Schriftzeichenhöhe:  {font_h_mm:6.2f} mm",
                ])
            else:
                lines.append("Schrift:             kein Text gesetzt")
            self.dim_values_var.set("\n".join(lines))

    def _draw_stripes(self, draw, width, height, cols, pcts, border_px=None):
        curr_y = 0
        mode = self.config["bund_mode"]
        for i in range(mode):
            seg_h = int((pcts[i] / 100.0) * height)
            y_end = curr_y + seg_h if i < mode - 1 else height
            if border_px is None:
                draw.rectangle([0, curr_y, width, y_end], fill=cols[i])
            else:
                draw.rectangle([0, curr_y, border_px, y_end], fill=cols[i])
                draw.rectangle([width - border_px, curr_y, width, y_end], fill=cols[i])
            curr_y = y_end

    def _resize_cover(self, src_img, target_w, target_h):
        """Scale image to fully cover target area, then center-crop."""
        if target_w <= 0 or target_h <= 0:
            return src_img.copy()
        scale = max(target_w / src_img.width, target_h / src_img.height)
        new_w = max(1, int(src_img.width * scale))
        new_h = max(1, int(src_img.height * scale))
        resized = src_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = max(0, (new_w - target_w) // 2)
        top = max(0, (new_h - target_h) // 2)
        return resized.crop((left, top, left + target_w, top + target_h))

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

        self.MIN_DPI = 300
        self.DPI = self._find_effective_dpi(
            self.config.get("canvas_w_mm", 90.0),
            self.config.get("canvas_h_mm", 130.0),
            min_dpi=self.MIN_DPI,
        )
        self.MM_TO_PX = self.DPI / 25.4
        # Use ceil so physical print size is never smaller than configured mm values.
        self.PHOTO_W = self._mm_to_px(self.config["photo_w_mm"], ceil_value=True)
        self.PHOTO_H = self._mm_to_px(self.config["photo_h_mm"], ceil_value=True)
        self.CANVAS_W = self._mm_to_px(self.config["canvas_w_mm"], ceil_value=True)
        self.CANVAS_H = self._mm_to_px(self.config["canvas_h_mm"], ceil_value=True)

        # Make preview large enough to inspect image details on typical screens.
        self.preview_scale = max(0.30, min(3.00, 420 / max(1, self.PHOTO_H)))
        
        # Katheten auf 50% der kürzesten Seite
        tri_pct = float(self.config.get("triangle_percent", 50.0))
        self.TRI_SIZE = int(min(self.PHOTO_W, self.PHOTO_H) * (tri_pct / 100.0))
        
        self.raw_img, self.current_scale = None, 1.0
        self.pan_x = self.pan_y = 0
        self.last_x = self.last_y = 0
        self.debounce_id = None
        self._preview_error_shown = False

        # UI
        ctrl = tk.Frame(self.main_frame); ctrl.pack(pady=5)
        tk.Button(ctrl, text="Bild laden", command=self.load_image).grid(row=0, column=0, padx=10)
        tk.Label(ctrl, text="Rahmen (mm):").grid(row=0, column=1)
        min_b = max(0.0, min(MAX_MM_LIMIT, float(self.config.get("border_min_mm", 0.0))))
        max_b = max(min_b, min(MAX_MM_LIMIT, float(self.config.get("border_max_mm", 7.0))))
        default_b = max(min_b, min(max_b, float(self.config.get("border_default_mm", 2.3))))
        self.border_val = tk.DoubleVar(value=default_b)
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

        preview_wrap = tk.Frame(self.main_frame)
        preview_wrap.pack(pady=10)

        self.canvas = tk.Canvas(preview_wrap, width=int(self.PHOTO_W*self.preview_scale), height=int(self.PHOTO_H*self.preview_scale), bg="#eee", highlightthickness=0)
        self.canvas.pack(side="left", padx=(0, 12))
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<Button-1>", self.on_click)

        dim_frame = tk.LabelFrame(preview_wrap, text="Maß-Skizze (technisch)", padx=6, pady=6)
        dim_frame.pack(side="left", fill="y")
        self.dim_canvas = tk.Canvas(dim_frame, width=360, height=260, bg="#fcfcfc", highlightthickness=1, highlightbackground="#d2d2d2")
        self.dim_canvas.pack()
        self.dim_values_var = tk.StringVar(value="")
        tk.Label(dim_frame, textvariable=self.dim_values_var, justify="left", anchor="w", font=("Consolas", 9)).pack(fill="x", pady=(6, 0))

        try:
            self._draw_dimension_info()
        except Exception:
            pass

        tk.Button(self.main_frame, text="Druck-Datei speichern", bg="#007bff", fg="white", command=self.save_check).pack(fill="x")

    def on_drag(self, e):
        if not self.raw_img: return
        # Verschiebung berechnen
        dx = (e.x - self.last_x) / self.preview_scale
        dy = (e.y - self.last_y) / self.preview_scale
        
        # Neue Pan-Werte berechnen
        new_x = self.pan_x - dx
        new_y = self.pan_y - dy
        
        # --- CLAMPING LOGIK (v1.0.1) ---
        # Verhindert das Schieben über den Bildrand hinaus
        border_px = self._get_effective_border_px()
        eff_w = max(1, self.PHOTO_W - (2 * border_px))
        
        # Verfügbare Höhe für Foto-Ausschnitt ermitteln
        text = self._get_effective_text()
        rect_h = 0
        if self.text_pos_var.get() == "below" and text != "":
            _, rect_h, _, _, _, _, _, _, _ = self._calc_text_block(text)
        
        eff_h = max(1, self.PHOTO_H - (2 * border_px))
        avail_h = max(1, eff_h - rect_h)
        
        img_w_scaled = self.raw_img.width * self.current_scale
        img_h_scaled = self.raw_img.height * self.current_scale
        
        # Grenzwerte: 0 bis (Skaliertes Bild - Ausschnittgröße)
        self.pan_x = max(0, min(img_w_scaled - eff_w, new_x))
        self.pan_y = max(0, min(img_h_scaled - avail_h, new_y))
        
        self.last_x, self.last_y = e.x, e.y
        self.update_preview()

    def create_final_image(self):
        border_px = self._get_effective_border_px()
        eff_w = max(1, self.PHOTO_W - (2 * border_px))
        eff_h = max(1, self.PHOTO_H - (2 * border_px))
        bg_w = max(self.CANVAS_W, self.PHOTO_W)
        bg_h = max(self.CANVAS_H, self.PHOTO_H)
        text = self._get_effective_text()
        font, rect_h, _, side_px, bottom_px, _, text_w, _, text_bottom = self._calc_text_block(text)
        if font is None:
            font = self._get_text_font(12)

        is_below = self.text_pos_var.get() == "below"
        avail_h = max(1, eff_h - rect_h) if is_below else eff_h
        
        resized = self.raw_img.resize((int(self.raw_img.width * self.current_scale), int(self.raw_img.height * self.current_scale)), Image.Resampling.LANCZOS)
        crop = resized.crop((int(self.pan_x), int(self.pan_y), int(self.pan_x + eff_w), int(self.pan_y + avail_h)))
        
        # Rahmen
        mode = self.config["bund_mode"]; cols = self.config["colors"]; pcts = self.config["percentages"]
        bg_source = self.config.get("background_source")
        if bg_source not in ("colors", "file"):
            bg_source = "file" if self.config.get("use_background_image", False) else "colors"
        use_bg = (bg_source == "file")
        flag_img_photo = None
        if use_bg and self.config.get("background_image"):
            try:
                src = Image.open(self.config.get("background_image")).convert("RGB")
                flag_img_photo = self._resize_cover(src, self.PHOTO_W, self.PHOTO_H)
            except Exception:
                flag_img_photo = None

        # If using background image, paste it as the entire base; otherwise start with white
        if flag_img_photo:
            nutz = flag_img_photo.copy()
        else:
            nutz = Image.new("RGB", (self.PHOTO_W, self.PHOTO_H), "#FFFFFF")
        
        draw_n = ImageDraw.Draw(nutz)
        
        # Draw borders (left/right stripes for each color segment OR left/right from background)
        if not flag_img_photo:
            self._draw_stripes(draw_n, self.PHOTO_W, self.PHOTO_H, cols, pcts, border_px=border_px)
        
        cont = Image.new("RGB", (eff_w, eff_h), "#FFFFFF")
        cont.paste(crop, (0, 0)); draw_c = ImageDraw.Draw(cont)
        if text != "":
            ry0 = eff_h - rect_h
            draw_c.rectangle([0, ry0, eff_w, eff_h], fill=self.config.get("text_bg_color", "#FFFFFF"))
            avail_text_w = max(1, eff_w - 2 * side_px)
            text_left = font.getbbox(text)[0]
            text_x = side_px + ((avail_text_w - text_w) // 2) - text_left
            # Place text using actual bbox bottom so descenders are never cut.
            text_y = eff_h - bottom_px - text_bottom
            draw_c.text((text_x, text_y), text, fill=self.config.get("text_color", "#000000"), font=font)
        
        nutz.paste(cont, (border_px, border_px))
        if self.use_triangle_var.get():
            draw_n.polygon([(self.PHOTO_W, 0), (self.PHOTO_W-self.TRI_SIZE, 0), (self.PHOTO_W, self.TRI_SIZE)], fill="#000000")
            draw_n.line([(self.PHOTO_W-self.TRI_SIZE, 0), (self.PHOTO_W, self.TRI_SIZE)], fill="#FFFFFF", width=1)
        
        # Keep exact frame composition size and place it on oversized print canvas.
        bg = Image.new("RGB", (bg_w, bg_h), "#000000")
        bg.paste(nutz, (0, 0))
        return bg

    def recalc_image_fit(self):
        if not self.raw_img: return
        border_px = self._get_effective_border_px()
        text = self._get_effective_text()
        rect_h = 0
        if self.text_pos_var.get() == "below" and text != "":
            _, rect_h, _, _, _, _, _, _, _ = self._calc_text_block(text)
        
        avail_h = max(1, (self.PHOTO_H - 2*border_px) - rect_h)
        eff_w = max(1, self.PHOTO_W - 2*border_px)
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
        min_b = max(0.0, min(MAX_MM_LIMIT, float(self.config.get("border_min_mm", 0.0))))
        max_b = max(min_b, min(MAX_MM_LIMIT, float(self.config.get("border_max_mm", 7.0))))
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
        try:
            self._draw_dimension_info()
        except Exception:
            pass
        if not self.raw_img: return
        try:
            p = self.create_final_image().crop((0, 0, self.PHOTO_W, self.PHOTO_H))
            self._preview_error_shown = False
        except Exception as ex:
            # Fallback: show the raw image so preview stays usable even if rendering fails.
            p = self.raw_img.copy()
            if not self._preview_error_shown:
                messagebox.showwarning("Vorschau-Fehler", f"Die erweiterte Vorschau konnte nicht berechnet werden.\nEs wird eine Fallback-Vorschau angezeigt.\n\nDetails: {ex}")
                self._preview_error_shown = True

        self.tk_img = ImageTk.PhotoImage(p.resize((int(self.PHOTO_W*self.preview_scale), int(self.PHOTO_H*self.preview_scale)), Image.Resampling.LANCZOS))
        self.canvas.delete("all"); self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
    def save_check(self):
        if not self.raw_img: return
        t = self._get_effective_text(); fn = re.sub(r'[^\w\s\.-]', '', t).strip()[:150] or "druck"
        p = filedialog.asksaveasfilename(initialfile=fn, defaultextension=".jpg")
        if p:
            dpi_tuple = (int(round(self.DPI)), int(round(self.DPI)))
            self.create_final_image().save(p, quality=98, dpi=dpi_tuple)


