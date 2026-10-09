# Schach in Welzheim<br>Website & Automatisierung

Dieses Repository enthält den Quellcode und die Automatisierung für die Website **„Schach in Welzheim“**, die alle Schachaktivitäten vor Ort – vom Vereinsleben über Mannschaften bis hin zu Schulschach-AGs – zentral bündelt. Die Seite basiert auf [MkDocs](https://www.mkdocs.org/) und dem [Material-Theme](https://squidfunk.github.io/mkdocs-material/) und wird über GitHub Pages automatisch gehostet und bereitgestellt.

## 🚀 Hauptfunktionen & Features

* **Umfassender Fokus:** Zentrale Plattform für alle Schachaktivitäten in Welzheim (Verein, Turniere, Jugendarbeit und Schulschach-AGs).
* **Modernes Design:** Verwendung des *MkDocs Material*-Themes mit automatischer Erkennung des hellen und dunklen Modus (Light/Dark Mode).
* **Individuelles Branding:** Angepasst an das lokale Design inklusive Logo und einer maßgeschneiderten Hauptfarbe (Sattes Vereinsgrün: `#106933`).
* **Symmetrisches 6er-Karten-Raster:** Eine moderne, übersichtliche Startseite mit 6 zentralen Einstiegspunkten (Schule, Mannschaften, Verein, Termine, interaktive Turnierkarte und Aktuelles).
* **Erweiterungen:** 
  * Aktivierte Volltextsuche (`search`-Plugin) für schnelles Finden von Informationen.
  * Unterstützung für erweiterte Attributlisten (`attr_list`), HTML-Einbettungen (`md_in_html`) und Makros (`mkdocs-macros-plugin`).
  * 
---

## 📰 Automatisches News- & Beitrags-Management (`/aktuelles/`)

Im Ordner `docs/aktuelles/` abgelegte Berichte (benannt nach dem Schema `YYYY-MM-DD-titel.md`) werden vom Build-Skript vollautomatisch verarbeitet:
* **Chronologische Sortierung & Teaser:** Artikel werden automatisch erkannt, mit formatiertem Datum versehen und mit automatischen Teaser-Texten auf der „Aktuelles“-Übersichtsseite aufgelistet.

### 🖼️ Automatische Bildzuordnung in Beiträgen
Passend zu den Berichten werden Bilder vollautomatisch über eine Ordnerstruktur eingebunden:
1. **Ordnerstruktur:** Zu jedem News-Artikel kann im selben Verzeichnis ein exakt gleichnamiger Unterordner angelegt werden (z. B. `docs/aktuelles/2026-10-02/`).
2. **Erkennung & Einbindung:** Das Skript sucht dort nach gängigen Bildformaten (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`) und generiert beim Build-Prozess vollautomatisch am Ende des Artikels den Bereich für die Bilder.
3. **Lightbox-Galerie:** Die Fotos werden als responsive Galerie (`glightbox`) eingebunden, sodass Besucher sie per Klick in einem großen Popup-Fenster betrachten können.

---

## ⚙️ Erklärung der Attributliste (`attr_list`)

Die in der `mkdocs.yml` aktivierte Erweiterung **`attr_list`** ist eine Markdown-Erweiterung, mit der man HTML-Attribute (wie CSS-Klassen oder IDs) direkt an Markdown-Elemente anhängen kann, ohne reines HTML schreiben zu müssen.

* **Wofür wird sie genutzt?** 
  * **Kachel-Grids:** Sie wird zusammen mit `md_in_html` verwendet, um Listen oder Container in moderne, responsive Kacheln zu verwandeln (z. B. für das 6er-Raster auf der Startseite mit der Klasse `class="grid cards"`).
  * **Element-Anpassung:** Man kann damit gezielt CSS-Klassen oder Formatierungen an Markdown-Blöcke übergeben, um das Layout ohne komplexe HTML-Workarounds flexibel zu steuern.

---

## 🛠️ Technische Struktur & Workflow

### 1. Konfiguration (`mkdocs.yml`)
Steuert die globalen Metadaten der Website (Titel, Beschreibung, Autor), das Layout, die Farbpalette und das *MkDocs Material*-Theme. 
Aktivierte Kern-Erweiterungen und Plugins:
* **`attr_list` & `md_in_html`**: Erlauben die direkte Einbettung von HTML-Strukturen (wie dem 2x3-Karten-Raster auf der Startseite) in Markdown.
* **`mkdocs-macros-plugin`**: Ermöglicht dynamische Makros (z. B. für automatische Unterseiten-Listen).
* **Volltextsuche (`search`)**: Schnelles Auffinden von Inhalten auf der gesamten Website.

### 2. Seitenstruktur (`docs/`)
Die Inhalte der Website sind logisch in Ordner unterteilt:
* `index.md`: Die Hauptseite mit dem 6er-Karten-Layout (Schule, Mannschaften, Verein, Termine, interaktive Karte, Aktuelles).
* `termine.md`: Zentrale Übersicht für anstehende Turniere, Mannschaftskämpfe und regelmäßige Termine.
* `aktuelles/`: Ordner für Berichte und Ankündigungen.
* `verein/` & `jugend/`: Unterseiten für den Ligabetrieb, das Training und offene Angebote („Schach für alle“).

### 3. GitHub Actions Deployment (`pages.yml`)
Ein automatisierter CI/CD-Workflow (`.github/workflows/pages.yml`), der bei jedem `push` auf den `main`-Branch folgendes ausführt:
1. Einrichtung einer sauberen Python-Umgebung inklusive Installation von `mkdocs-material`, `mkdocs-macros-plugin` und weiteren Abhängigkeiten.
2. Kompilierung der statischen Website aus den Markdown-Dateien.
3. Vollautomatische Veröffentlichung auf **GitHub Pages** (`mkdocs gh-deploy`): [Schach in Welzheim](https://schachwelzheim.github.io/schachwelzheim/)

