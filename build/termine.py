from datetime import datetime
import os
import re

# Pfade definieren
INPUT_DIR = "content/termine"
OUTPUT_DIR = "docs/verein/termine"
GESAMT_FILE = os.path.join(OUTPUT_DIR, "index.md")


def log_debug(msg):
  """Hilfsfunktion für übersichtliche Debug-Ausgaben"""
  print(f"[DEBUG - TERMINE] {msg}")


def parse_date(date_str):
  """Sucht ein Datum im Format D.M.YY, DD.MM.YY oder DD.MM.YYYY"""
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
  return date_obj.strftime("%d.%m.%Y")


def parse_termine_file(filepath):
  log_debug(f"Lese Quelldatei: {filepath}")
  with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

  title = ""
  entries = []

  for line_idx, line in enumerate(lines, start=1):
    line_str = line.strip()
    if not line_str:
      continue

    if line_str.startswith("#"):
      title = line_str.lstrip("#").strip()
      log_debug(f"  -> Titel in Zeile {line_idx} gefunden: '{title}'")
      continue

    date_obj = parse_date(line_str)
    if date_obj:
      event_text = re.sub(
          r"^\s*\d{1,2}\.\d{1,2}\.\d{2,4}\s*", "", line_str
      ).strip()
      entries.append({
          "date": date_obj,
          "text": event_text,
      })
      log_debug(
          f"  -> Termin geparst (Zeile {line_idx}): {format_date_str(date_obj)}"
          f" | {event_text}"
      )
    else:
      log_debug(
          f"  [!] Zeile {line_idx} übersprungen (kein Datum erkannt):"
          f" '{line_str}'"
      )

  return title, entries


def build_termine():
  log_debug("=== Starte Termin-Build ===")
  log_debug(f"Arbeitsverzeichnis: {os.getcwd()}")
  log_debug(f"Input-Ordner:  {os.path.abspath(INPUT_DIR)}")
  log_debug(f"Output-Ordner: {os.path.abspath(OUTPUT_DIR)}")

  if not os.path.exists(INPUT_DIR):
    log_debug(
      f"FEHLER: Eingabe-Ordner '{INPUT_DIR}' existiert nicht!"
      " Abbruch."
    )
    return

  os.makedirs(OUTPUT_DIR, exist_ok=True)
  today = datetime.now().date()
  log_debug(f"Heute angewandtes Vergleichsdatum: {today}")

  all_events = []
  kategorien = []

  files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".md")]
  log_debug(f"Gefundene .md Dateien in '{INPUT_DIR}': {files}")

  if not files:
    log_debug(f"WARNUNG: Keine .md Dateien in '{INPUT_DIR}' gefunden!")

  # 1. Quelldateien einlesen
  for filename in sorted(files):
    filepath = os.path.join(INPUT_DIR, filename)
    title, entries = parse_termine_file(filepath)

    if not title:
      title = filename.replace(".md", "").capitalize()
      log_debug(
          f"  -> Kein Titel in Datei. Verwende Fallback-Titel: '{title}'"
      )

    entries.sort(key=lambda x: x["date"])
    kategorien.append({"slug": filename, "title": title, "entries": entries})

    for entry in entries:
      all_events.append({
          "date": entry["date"],
          "category": title,
          "text": entry["text"],
      })

  # 2. Einzelseiten in docs/verein/termine/ generieren
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
        date_formatted = format_date_str(entry["date"])
        is_past = entry["date"] < today

        if is_past:
          content += (
              f"| <del style='color: #888;'>{date_formatted}</del> | <del"
              f" style='color: #888;'>{entry['text']}</del> | 🛑 *Vergangen* |\n"
          )
        else:
          content += (
              f"| **{date_formatted}** | **{entry['text']}** | ⏳ *Anstehend* |\n"
          )

    with open(out_filepath, "w", encoding="utf-8") as f:
      f.write(content)

  # 3. Gesamtseite (docs/verein/termine/index.md) generieren
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
      date_formatted = format_date_str(ev["date"])
      is_past = ev["date"] < today

      if is_past:
        gesamt_content += (
            f"| <del style='color: #888;'>{date_formatted}</del> | <del"
            f" style='color: #888;'>{ev['category']}</del> | <del"
            f" style='color: #888;'>{ev['text']}</del> | 🛑 |\n"
        )
      else:
        gesamt_content += (
            f"| **{date_formatted}** | `{ev['category']}` |"
            f" **{ev['text']}** | ⏳ |\n"
        )

  with open(GESAMT_FILE, "w", encoding="utf-8") as f:
    f.write(gesamt_content)

  log_debug(f"Prüfe Existenz der erzeugten Datei '{GESAMT_FILE}':")
  if os.path.exists(GESAMT_FILE):
    log_debug(
        f"  [OK] '{GESAMT_FILE}' wurde erfolgreich mit"
        f" {os.path.getsize(GESAMT_FILE)} Bytes angelegt!"
    )
  else:
    log_debug(f"  [FEHLER] '{GESAMT_FILE}' konnte nicht angelegt werden!")

  log_debug("=== Termin-Build abgeschlossen ===")


if __name__ == "__main__":
  build_termine()
        
