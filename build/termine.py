from datetime import datetime
import os
import re

# Dynamische Pfadermittlung (Projekt-Hauptverzeichnis)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_DIR = os.path.join(BASE_DIR, "content", "termine")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "verein", "termine")
GESAMT_FILE = os.path.join(OUTPUT_DIR, "index.md")


def log_debug(msg):
  """Hilfsfunktion für übersichtliche Log-Ausgaben im Build-Prozess"""
  print(f"[DEBUG - TERMINE] {msg}")


def parse_date(date_str):
  """Liest ein Einzeldatum im Format D.M.YY, DD.MM.YY oder DD.MM.YYYY"""
  match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})", date_str)
  if not match:
    return None

  day, month, year = match.groups()
  if len(year) == 2:
    year = "20" + year

  try:
    return datetime(int(year), int(month), int(day)).date()
  except ValueError:
    return None


def format_date_str(date_obj):
  """Formatiert ein Date-Objekt zu DD.MM.YYYY"""
  return date_obj.strftime("%d.%m.%Y")


def parse_termine_file(filepath):
  """Liest eine Termin-Quelldatei ein und verarbeitet Einzel- sowie Zeitraumingaben (Ferien)."""
  log_debug(f"Lese Quelldatei: {filepath}")
  with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

  title = ""
  entries = []

  for line_idx, line in enumerate(lines, start=1):
    line_str = line.strip()
    if not line_str:
      continue

    # Überschrift auslesen
    if line_str.startswith("#"):
      title = line_str.lstrip("#").strip()
      log_debug(f"  -> Titel in Zeile {line_idx}: '{title}'")
      continue

    # 1. Fall: Datumsbereich (z. B. "1.8.26 - 13.9.26 Sommerferien")
    range_match = re.search(
        r"^(\d{1,2}\.\d{1,2}\.\d{2,4})\s*-\s*(\d{1,2}\.\d{1,2}\.\d{2,4})\s+(.*)$",
        line_str,
    )
    if range_match:
      start_str, end_str, event_text = range_match.groups()
      start_date = parse_date(start_str)
      end_date = parse_date(end_str)

      if start_date:
        disp_date = (
            f"{format_date_str(start_date)} – {format_date_str(end_date)}"
            if end_date
            else format_date_str(start_date)
        )
        entries.append({
            "date": start_date,
            "end_date": end_date,
            "display_date": disp_date,
            "text": event_text.strip(),
        })
        log_debug(
            f"  -> Zeitraum geparst (Zeile {line_idx}): {disp_date} |"
            f" {event_text.strip()}"
        )
        continue

    # 2. Fall: Einzeldatum (z. B. "6.11.26 Runde 1")
    date_obj = parse_date(line_str)
    if date_obj:
      event_text = re.sub(
          r"^\s*\d{1,2}\.\d{1,2}\.\d{2,4}\s*", "", line_str
      ).strip()
      entries.append({
          "date": date_obj,
          "end_date": None,
          "display_date": format_date_str(date_obj),
          "text": event_text,
      })
      log_debug(
          f"  -> Termin geparst (Zeile {line_idx}):"
          f" {format_date_str(date_obj)} | {event_text}"
      )
    else:
      log_debug(
          f"  [!] Zeile {line_idx} übersprungen (kein Datum erkannt):"
          f" '{line_str}'"
      )

  return title, entries


def build_termine():
  """Hauptfunktion zum Verarbeiten aller Termine und Generieren der Markdown-Seiten."""
  log_debug("=== Starte Termin-Build ===")
  log_debug(f"Projekt-Hauptverzeichnis: {BASE_DIR}")
  log_debug(f"Input-Ordner:  {INPUT_DIR}")
  log_debug(f"Output-Ordner: {OUTPUT_DIR}")

  if not os.path.exists(INPUT_DIR):
    log_debug(
        f"FEHLER: Eingabe-Ordner '{INPUT_DIR}' existiert nicht! Abbruch."
    )
    return

  os.makedirs(OUTPUT_DIR, exist_ok=True)
  today = datetime.now().date()
  log_debug(f"Vergleichsdatum für Vergangenheitscheck: {today}")

  all_events = []
  kategorien = []

  files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".md")]
  log_debug(f"Gefundene Quell-Dateien in '{INPUT_DIR}': {files}")

  if not files:
    log_debug(f"WARNUNG: Keine .md Dateien in '{INPUT_DIR}' gefunden!")

  # 1. Quelldateien einlesen & parsen
  for filename in sorted(files):
    filepath = os.path.join(INPUT_DIR, filename)
    title, entries = parse_termine_file(filepath)

    if not title:
      title = filename.replace(".md", "").capitalize()

    entries.sort(key=lambda x: x["date"])
    kategorien.append({"slug": filename, "title": title, "entries": entries})

    for entry in entries:
      all_events.append({
          "date": entry["date"],
          "end_date": entry["end_date"],
          "display_date": entry["display_date"],
          "category": title,
          "text": entry["text"],
      })

  # 2. Einzelseiten in docs/verein/termine/ erzeugen
  log_debug("--- Generiere Einzelseiten ---")
  for kat in kategorien:
    out_filepath = os.path.join(OUTPUT_DIR, kat["slug"])
    log_debug(
        f"Schreibe Einzelseite: {out_filepath} ({len(kat['entries'])} Termine)"
    )

    content = f"# {kat['title']}\n\n"

    if not kat["entries"]:
      content += "*Aktuell keine Termine eingetragen.*\n"
    else:
      content += "| Datum | Ereignis | Status |\n"
      content += "| :--- | :--- | :--- |\n"

      for entry in kat["entries"]:
        disp_date = entry["display_date"]

        # Bei Zeiträumen zählt das Enddatum für den Vergangenheits-Status
        check_date = (
            entry["end_date"] if entry["end_date"] else entry["date"]
        )
        is_past = check_date < today

        if is_past:
          content += (
              f"| <del style='color: #888;'>{disp_date}</del> | <del"
              f" style='color: #888;'>{entry['text']}</del> | 🛑 *Vergangen* |\n"
          )
        else:
          content += f"| **{disp_date}** | **{entry['text']}** | ⏳ *Anstehend* |\n"

    with open(out_filepath, "w", encoding="utf-8") as f:
      f.write(content)

  # 3. Gesamtübersicht (docs/verein/termine/index.md) erzeugen
  log_debug("--- Generiere Gesamtübersicht ---")
  all_events.sort(key=lambda x: (x["date"], x["category"]))
  log_debug(f"Gesamtanzahl aller Termine: {len(all_events)}")
  log_debug(f"Schreibe Gesamtdatei nach: {GESAMT_FILE}")

  gesamt_content = "# 📅 Gesamter Terminplan\n\n"
  gesamt_content += (
      "Hier findest Du alle Termine aller Kategorien in chronologischer"
      " Reihenfolge.\n\n"
  )

  if not all_events:
    gesamt_content += "*Keine Termine vorhanden.*\n"
  else:
    gesamt_content += "| Datum | Kategorie | Ereignis | Status |\n"
    gesamt_content += "| :--- | :--- | :--- | :--- |\n"

    for ev in all_events:
      disp_date = ev["display_date"]
      check_date = ev["end_date"] if ev["end_date"] else ev["date"]
      is_past = check_date < today

      if is_past:
        gesamt_content += (
            f"| <del style='color: #888;'>{disp_date}</del> | <del"
            f" style='color: #888;'>{ev['category']}</del> | <del"
            f" style='color: #888;'>{ev['text']}</del> | 🛑 |\n"
        )
      else:
        gesamt_content += (
            f"| **{disp_date}** | `{ev['category']}` | **{ev['text']}** | ⏳ |\n"
        )

  with open(GESAMT_FILE, "w", encoding="utf-8") as f:
    f.write(gesamt_content)

  log_debug("=== Termin-Build erfolgreich abgeschlossen ===")


if __name__ == "__main__":
  build_termine()
    
