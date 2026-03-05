import json
import os

CONFIG_FILE = "config.json"
MAX_MM_LIMIT = 7.0


class ConfigHandler:
	@staticmethod
	def get_default_percentages(num):
		if num == 2:
			return [50.0, 50.0]
		if num == 3:
			return [33.33, 33.34, 33.33]
		if num == 4:
			return [25.0, 25.0, 25.0, 25.0]
		if num == 5:
			return [5.0, 30.0, 30.0, 30.0, 5.0]
		if num == 6:
			return [5.0, 22.5, 22.5, 22.5, 22.5, 5.0]
		return [100.0 / num] * num

	@staticmethod
	def get_default():
		return {
			"photo_h_mm": 90.0,
			"photo_w_mm": 70.0,
			"canvas_h_mm": 150.0,
			"canvas_w_mm": 70.0,
			"bund_mode": 4,
			"colors": ["#FFFFFF", "#008000", "#eb0000", "#FFFFFF", "#FFFFFF", "#FFFFFF"],
			"percentages": [25.0, 25.0, 25.0, 25.0, 0.0, 0.0],
			"custom_pct": False,
			"show_advanced": False,
			"background_source": "colors",
			"fixed_distance_mm": 6.0,
			"fixed_bottom_mm": 6.0,
			"fixed_top_p_mm": 1.0,
			"border_default_mm": 2.3,
			"border_min_mm": 0.0,
			"border_max_mm": 7.0,
			"text_bg_color": "#FFFFFF",
			"text_color": "#000000",
			"text_font": "arial.ttf",
			"triangle_percent": 50.0,
			"use_background_image": False,
			"background_image": "",
		}

	@staticmethod
	def load():
		if not os.path.exists(CONFIG_FILE):
			return None
		try:
			with open(CONFIG_FILE, "r", encoding="utf-8") as f:
				loaded = json.load(f)

			base = ConfigHandler.get_default()
			base.update(loaded)

			# Migrate legacy cm-based canvas keys to mm if mm keys are absent.
			if "canvas_h_mm" not in loaded and "canvas_h_cm" in loaded:
				base["canvas_h_mm"] = float(loaded["canvas_h_cm"]) * 10.0
			if "canvas_w_mm" not in loaded and "canvas_w_cm" in loaded:
				base["canvas_w_mm"] = float(loaded["canvas_w_cm"]) * 10.0
			return base
		except Exception:
			return None

	@staticmethod
	def save(config):
		with open(CONFIG_FILE, "w", encoding="utf-8") as f:
			json.dump(config, f, indent=4)


