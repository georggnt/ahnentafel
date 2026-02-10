# Ahnentafel Optimaldruck 
Sehr geehrte Chronisten und Archivare, ich präsentiere das Projekt „Ahnentafel Optimaldruck“. Dieses Werkzeug wurde entwickelt, um Porträts für Ahnentafeln so aufzubereiten, dass sie in Serie ein konsistentes Bild zum Druck ergeben.
## Vorschau

### Hauptanwendung
![Portrait-Pro-Tool Hauptfenster](screenshots/Screenshot%202026-02-10%20121150.png)

### Ergebnis
*Druckfertiges Ergebnis für den Fotodruck (z.B. dm). **Wichtig:** Beim Druckauftrag darauf achten, dass kein Rand abgeschnitten wird, da sich sonst die Verhältnisse ändern.*

![Beispiel-Output: Musterbruder, Max](screenshots/Musterbruder%20Max%20rec.%2010.02.2026.jpg)

<details>
<summary>Weitere Screenshots anzeigen</summary>

![Einstellungen 1](screenshots/Screenshot%202026-02-10%20130230.png)
![Einstellungen 2](screenshots/Screenshot%202026-02-10%20130240.png)
![Einstellungen 3](screenshots/Screenshot%202026-02-10%20133346.png)

</details>
## Die Highlights
Individuelle Rahmengrößen: Das Tool ist exakt auf spezifische Rahmenmaße anpassbar.

Coleur-Rahmen:  Option, Fotos mit einem Rahmen in Coleur des Bundes zu versehen.

## Installation & Nutzung
Python & Pillow: Installieren Sie Python und die Bildbibliothek mit pip install Pillow.

Start: Starten Sie die main.py. Ein Assistent führt Sie durch die Erstkonfiguration.

## kein Python gewünscht
EXE-Erstellung: Falls gewünscht, können Sie mit pip install pyinstaller und dem Befehl pyinstaller --onefile --noconsole --name "Ahnentafel_Optimaldruck" main.py eine eigenständige Windows-Datei erstellen.

## KI-Hinweis
Dieses Projekt entstand hauptsächlich mit Gemini (Google). Das Tool liefert druckfertige JPEGs in 300 DPI (konzipiert für 10x15 cm Drucke). Die Nutzung des Tools erfolgt ausschließlich lokal und ist von jeder KI entkoppelt.

## erweiterte Einstellungen
Präzise Farbanteile: Über die Funktion „Farbanteile verändern“ können die Bandmaße auf den Prozentpunkt genau definiert werden. (bspw. 33%,33%,33% für dreifarbige Bünde)

Vollständige Maße-Freiheit: Das Tool ist exakt auf individuelle Archivmaße anpassbar (H x B in mm).

Perfekte Konsistenz: Einmal eingestellt, bleiben Textplatzierung und Bildproportionen bei jedem Porträt identisch.




nec timide nec temere
Georg Wk!