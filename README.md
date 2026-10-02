# Schach in Welzheim – Website & Automatisierung

Dieses Repository enthält den Quellcode und die Automatisierung für die Website **„Schach in Welzheim“**, die alle Schachaktivitäten vor Ort – vom Vereinsleben über Mannschaften bis hin zu Schulschach-AGs – zentral bündelt. Die Seite basiert auf [MkDocs](https://www.mkdocs.org/) und dem [Material-Theme](https://squidfunk.github.io/mkdocs-material/) und wird über GitHub Pages automatisch gehostet und bereitgestellt.

## 🚀 Hauptfunktionen & Features

* **Umfassender Fokus:** Zentrale Plattform für alle Schachaktivitäten in Welzheim (Verein, Turniere, Jugendarbeit und Schulschach-AGs).
* **Modernes Design:** Verwendung des *MkDocs Material*-Themes mit automatischer Erkennung des hellen und dunklen Modus (Light/Dark Mode).
* **Individuelles Branding:** Angepasst an das lokale Design inklusive Logo und einer maßgeschneiderten Hauptfarbe (Sattes Vereinsgrün: `#106933`).
* **Vollautomatische Navigation:** Ein integriertes GitHub-Actions-Skript scannt beim Build-Prozess vollautomatisch die Ordnerstruktur, liest Überschriften aus den Markdown-Dateien aus und baut daraus die gesamte Menüstruktur (`mkdocs.yml`).
* **Erweiterungen:** 
  * Aktivierte Volltextsuche (`search`-Plugin) für schnelles Finden von Informationen.
  * Unterstützung für erweiterte Attributlisten (`attr_list`).

---

## 📰 Automatisches News- & Beitrags-Management (`/aktuelles/`)

Im Ordner `docs/aktuelles/` abgelegte Berichte (benannt nach dem Schema `YYYY-MM-DD-titel.md`) werden vom Build-Skript vollautomatisch verarbeitet:
* **Chronologische Sortierung & Teaser:** Artikel werden automatisch erkannt, mit formatiertem Datum versehen und mit automatischen Teaser-Texten auf der „Aktuelles“-Übersichtsseite aufgelistet.

### 🖼️ Automatische Bildzuordnung in Beiträgen
Passend zu den Berichten werden Bilder vollautomatisch über eine Ordnerstruktur eingebunden:
1. **Ordnerstruktur:** Zu jedem News-Artikel (z. B. `2026-10-02-sieg-und-niederlage.md`) kann im selben Verzeichnis ein exakt gleichnamiger Unterordner angelegt werden (z. B. `docs/aktuelles/2026-10-02-sieg-und-niederlage/`).
2. **Erkennung & Einbindung:** Das Skript sucht dort nach gängigen Bildformaten (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`) und generiert beim Build-Prozess vollautomatisch am Ende des Artikels den Bereich `## Bilder zum Beitrag`.
3. **Lightbox-Galerie:** Die Fotos werden als responsive Galerie (`glightbox`) eingebunden, sodass Besucher sie per Klick in einem großen Popup-Fenster betrachten können.

---

## ⚙️ Erklärung der Attributliste (`attr_list`)

Die in der `mkdocs.yml` aktivierte Erweiterung **`attr_list`** ist eine Markdown-Erweiterung, mit der man HTML-Attribute (wie CSS-Klassen oder Styles) direkt an normale Markdown-Elemente anhängen kann, ohne reines HTML schreiben zu müssen.

* **Wofür wird sie genutzt?** 
  Man kann damit Markdown-Elemente wie Links gezielt mit Design-Klassen des Material-Themes versehen. Ein klassisches Anwendungsbeispiel sind Buttons: Aus einem normalen Link wie:
  ```markdown
  [Route öffnen](https://maps.google.com/?q=Welzheim){ .md-button .md-button--primary }
  
