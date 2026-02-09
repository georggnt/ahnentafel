import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import re

class FotoDruckTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Portrait-Pro-Tool v4.2")
        
        # --- KONFIGURATION ---
        self.DPI = 300
        self.CM_TO_PX = self.DPI / 2.54
        
        self.PHOTO_W_CM, self.PHOTO_H_CM = 7.0, 9.0
        self.CANVAS_W_CM, self.CANVAS_H_CM = 10.0, 15.0

        self.PHOTO_W, self.PHOTO_H = int(self.PHOTO_W_CM * self.CM_TO_PX), int(self.PHOTO_H_CM * self.CM_TO_PX)
        self.CANVAS_W, self.CANVAS_H = int(self.CANVAS_W_CM * self.CM_TO_PX), int(self.CANVAS_H_CM * self.CM_TO_PX)
        
        self.COL_WHITE, self.COL_BLACK = "#FFFFFF", "#000000"
        self.COL_GREEN, self.COL_RED = "#008000", "#eb0000"
        
        self.FIXED_DISTANCE_MM = 3.5   
        self.FIXED_TOP_P_MM = 1.0      
        
        # NEU: Katheten auf 50% der KÜRZESTEN Seite (7cm * 0.50 = 3.5cm)
        self.TRI_SIZE = int(min(self.PHOTO_W, self.PHOTO_H) * 0.50)
        self.LINE_WIDTH_PX = 1         
        
        self.placeholder = "Nachname, Vorname(n) rec. am TT.MM.YYYY"
        self.raw_img, self.current_scale = None, 1.0
        self.pan_x, self.pan_y = 0, 0
        self.debounce_id = None
        
        # UI Setup
        frame_controls = tk.Frame(root); frame_controls.pack(pady=5)
        tk.Button(frame_controls, text="Bild laden", command=self.load_image).grid(row=0, column=0, padx=5)
        
        tk.Label(frame_controls, text="Rahmen (mm):").grid(row=0, column=1)
        self.border_val = tk.DoubleVar(value=3.0)
        tk.Scale(frame_controls, from_=0, to=3.0, resolution=0.5, orient=tk.HORIZONTAL, variable=self.border_val, command=self.on_setting_change).grid(row=0, column=2, padx=5)

        self.use_triangle_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame_controls, text="schwarzes Dreieck", variable=self.use_triangle_var, command=self.update_preview).grid(row=0, column=3, padx=5)
        
        self.entry_text = tk.Entry(root, width=60, fg='grey')
        self.entry_text.insert(0, self.placeholder)
        self.entry_text.bind("<FocusIn>", self.clear_placeholder)
        self.entry_text.bind("<FocusOut>", self.add_placeholder)
        self.entry_text.bind("<KeyRelease>", self.on_text_key_release)
        self.entry_text.pack(pady=5)
        
        self.text_pos_var = tk.StringVar(value="below")
        frame_radio = tk.Frame(root); frame_radio.pack()
        tk.Radiobutton(frame_radio, text="Text im Bild (Overlay)", variable=self.text_pos_var, value="overlay", command=self.on_setting_change).pack(side=tk.LEFT)
        tk.Radiobutton(frame_radio, text="Text unter Bild", variable=self.text_pos_var, value="below", command=self.on_setting_change).pack(side=tk.LEFT)
        
        self.preview_scale = 0.2 
        self.canvas = tk.Canvas(root, width=self.PHOTO_W * self.preview_scale, height=self.PHOTO_H * self.preview_scale, bg=self.COL_WHITE, highlightthickness=1, highlightbackground="gray")
        self.canvas.pack(pady=10)
        self.canvas.bind("<B1-Motion>", self.on_drag); self.canvas.bind("<Button-1>", self.on_click)

        tk.Button(root, text="für Druck speichern", command=self.save_check, bg="green", fg="white", font=("Arial", 10, "bold")).pack(pady=5)

    def on_setting_change(self, *args):
        self.recalc_image_fit(); self.update_preview()

    def recalc_image_fit(self):
        if not self.raw_img: return
        border_px = int(self.border_val.get() / 10 * self.CM_TO_PX)
        eff_w, eff_h = self.PHOTO_W - (2 * border_px), self.PHOTO_H - (2 * border_px)
        
        text = self.entry_text.get()
        has_t = text and text != self.placeholder
        rect_h = 0
        if has_t and self.text_pos_var.get() == "below":
            current_bottom_mm = self.FIXED_DISTANCE_MM - self.border_val.get()
            bottom_p, top_p = int(current_bottom_mm / 10 * self.CM_TO_PX), int(self.FIXED_TOP_P_MM / 10 * self.CM_TO_PX)
            
            fs = 1; font = ImageFont.truetype("arial.ttf", fs)
            target_w = self.PHOTO_W - (2 * int(self.FIXED_DISTANCE_MM / 10 * self.CM_TO_PX))
            while font.getbbox(text)[2] - font.getbbox(text)[0] < target_w and fs < 400:
                fs += 1; font = ImageFont.truetype("arial.ttf", fs)
            rect_h = (font.getbbox(text)[3] - font.getbbox(text)[1]) + bottom_p + top_p
        
        avail_h = eff_h - rect_h
        ratio_t, ratio_i = eff_w / avail_h, self.raw_img.width / self.raw_img.height
        self.current_scale = avail_h / self.raw_img.height if ratio_i > ratio_t else eff_w / self.raw_img.width
        self.pan_x = max(0, min(self.raw_img.width * self.current_scale - eff_w, self.pan_x))
        self.pan_y = max(0, min(self.raw_img.height * self.current_scale - avail_h, self.pan_y))

    def create_complex_background(self):
        bg = Image.new("RGB", (self.CANVAS_W, self.CANVAS_H), self.COL_BLACK)
        draw = ImageDraw.Draw(bg)
        q1_y, q2_y, q3_y = self.PHOTO_H // 4, self.PHOTO_H // 2, 3 * (self.PHOTO_H // 4)
        draw.rectangle([0, 0, self.CANVAS_W, q1_y], fill=self.COL_WHITE)
        draw.rectangle([0, q1_y, self.CANVAS_W, q2_y], fill=self.COL_GREEN)
        draw.rectangle([0, q2_y, self.CANVAS_W, q3_y], fill=self.COL_RED)
        draw.rectangle([0, q3_y, self.CANVAS_W, self.PHOTO_H], fill=self.COL_WHITE)
        return bg

    def draw_colored_border(self, draw, w, h, thickness):
        if thickness <= 0: return
        q1_y, q2_y, q3_y = h // 4, h // 2, 3 * (h // 4)
        draw.rectangle([0, q1_y, thickness, q2_y], fill=self.COL_GREEN)
        draw.rectangle([0, q2_y, thickness, q3_y], fill=self.COL_RED)
        draw.rectangle([w - thickness, q1_y, w, q2_y], fill=self.COL_GREEN)
        draw.rectangle([w - thickness, q2_y, w, q3_y], fill=self.COL_RED)

    def on_text_key_release(self, event):
        if self.debounce_id: self.root.after_cancel(self.debounce_id)
        self.debounce_id = self.root.after(1000, lambda: [self.recalc_image_fit(), self.update_preview()])

    def clear_placeholder(self, event):
        if self.entry_text.get() == self.placeholder: self.entry_text.delete(0, tk.END); self.entry_text.config(fg='black')

    def add_placeholder(self, event):
        if not self.entry_text.get(): self.entry_text.insert(0, self.placeholder); self.entry_text.config(fg='grey')

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Bilder", "*.jpg *.jpeg *.png")])
        if not path: return
        self.raw_img = Image.open(path).convert("RGB")
        self.recalc_image_fit(); self.update_preview()

    def on_click(self, event): self.last_x, self.last_y = event.x, event.y

    def on_drag(self, event):
        if not self.raw_img: return
        self.pan_x -= (event.x - self.last_x) / self.preview_scale
        self.pan_y -= (event.y - self.last_y) / self.preview_scale
        self.last_x, self.last_y = event.x, event.y
        self.update_preview()

    def create_final_image(self):
        border_mm = self.border_val.get()
        border_px = int(border_mm / 10 * self.CM_TO_PX)
        current_pad_mm = self.FIXED_DISTANCE_MM - border_mm
        side_p, bottom_p = int(current_pad_mm / 10 * self.CM_TO_PX), int(current_pad_mm / 10 * self.CM_TO_PX)
        top_p = int(self.FIXED_TOP_P_MM / 10 * self.CM_TO_PX)
        
        eff_w, eff_h = self.PHOTO_W - (2 * border_px), self.PHOTO_H - (2 * border_px)
        text = self.entry_text.get(); has_t = text and text != self.placeholder
        
        font_h, rect_h = 0, 0
        if has_t:
            fs = 1; font = ImageFont.truetype("arial.ttf", fs)
            target_w = self.PHOTO_W - (2 * int(self.FIXED_DISTANCE_MM / 10 * self.CM_TO_PX))
            while font.getbbox(text)[2] - font.getbbox(text)[0] < target_w and fs < 400:
                fs += 1; font = ImageFont.truetype("arial.ttf", fs)
            font_h = font.getbbox(text)[3] - font.getbbox(text)[1]
            rect_h = font_h + bottom_p + top_p 
        
        is_below = self.text_pos_var.get() == "below" and has_t
        avail_h = eff_h - rect_h if is_below else eff_h
        
        s_w, s_h = int(self.raw_img.width * self.current_scale), int(self.raw_img.height * self.current_scale)
        resized = self.raw_img.resize((s_w, s_h), Image.Resampling.LANCZOS)
        self.pan_x = max(0, min(s_w - eff_w, self.pan_x))
        self.pan_y = max(0, min(s_h - avail_h, self.pan_y))
        
        crop = resized.crop((self.pan_x, self.pan_y, self.pan_x + eff_w, self.pan_y + avail_h))
        
        nutzbild = Image.new("RGB", (self.PHOTO_W, self.PHOTO_H), self.COL_WHITE)
        draw_nutz = ImageDraw.Draw(nutzbild)
        self.draw_colored_border(draw_nutz, self.PHOTO_W, self.PHOTO_H, border_px)
        
        content = Image.new("RGB", (eff_w, eff_h), self.COL_WHITE)
        content.paste(crop, (0, 0)); draw_cont = ImageDraw.Draw(content)
        
        if has_t:
            ry0 = eff_h - rect_h
            if not is_below: draw_cont.rectangle([0, ry0, eff_w, eff_h], fill=self.COL_WHITE)
            tw = font.getbbox(text)[2] - font.getbbox(text)[0]
            draw_cont.text((side_p + ((eff_w - 2*side_p - tw)//2), eff_h - bottom_p - font_h), text, fill=self.COL_BLACK, font=font)
        
        nutzbild.paste(content, (border_px, border_px))
        
        if self.use_triangle_var.get():
            p1, p2, p3 = (self.PHOTO_W, 0), (self.PHOTO_W - self.TRI_SIZE, 0), (self.PHOTO_W, self.TRI_SIZE)
            draw_nutz.polygon([p1, p2, p3], fill=self.COL_BLACK)
            draw_nutz.line([p2, p3], fill=self.COL_WHITE, width=self.LINE_WIDTH_PX)

        canvas = self.create_complex_background(); canvas.paste(nutzbild, (0, 0))
        return canvas

    def update_preview(self):
        if not self.raw_img: return
        final = self.create_final_image()
        crop_p = final.crop((0, 0, self.PHOTO_W, self.PHOTO_H))
        self.tk_img = ImageTk.PhotoImage(crop_p.resize((int(self.PHOTO_W * self.preview_scale), int(self.PHOTO_H * self.preview_scale)), Image.Resampling.LANCZOS))
        self.canvas.delete("all"); self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

    def save_check(self):
        if not self.raw_img: return
        text = self.entry_text.get(); init_n = re.sub(r'[^\w\s\.-]', '', text).strip()[:150] if (text and text != self.placeholder) else "foto_druck"
        path = filedialog.asksaveasfilename(initialfile=init_n, defaultextension=".jpg", filetypes=[("JPEG", "*.jpg")])
        if path: self.create_final_image().save(path, quality=98, dpi=(self.DPI, self.DPI)); messagebox.showinfo("Erfolg", "Druckdatei gespeichert.")

if __name__ == "__main__":
    root = tk.Tk(); app = FotoDruckTool(root); root.mainloop()