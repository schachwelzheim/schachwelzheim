from datetime import datetime
import os
import re

# Dynamische Pfadermittlung (Projekt-Hauptverzeichnis)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_DIR = os.path.join(BASE_DIR, "content", "termine")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "verein", "termine")
GESAMT_FILE = os.path.join(OUTPUT_DIR, "index.md")
MATRIX_FILE = os.path.join(OUTPUT_DIR, "kalender-matrix.md")


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
  """Liest eine Termin-Quelldatei ein und verarbeitet Einzel- sowie Zeitraumingaben."""
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
  all_dates = set()
  events_by_date = {}  # { date_obj: { category_title: (event_text, is_past) } }

  files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".md")]
  log_debug(f"Gefundene Quell-Dateien in '{INPUT_DIR}': {files}")

  # 1. Quelldateien einlesen & parsen
  for filename in sorted(files):
    filepath = os.path.join(INPUT_DIR, filename)
    title, entries = parse_termine_file(filepath)

    if not title:
      title = filename.replace(".md", "").capitalize()

    entries.sort(key=lambda x: x["date"])
    kategorien.append({"slug": filename, "title": title, "entries": entries})

    for entry in entries:
      d = entry["date"]
      check_date = entry["end_date"] if entry["end_date"] else d
      is_past = check_date < today

      all_events.append({
          "date": d,
          "end_date": entry["end_date"],
          "display_date": entry["display_date"],
          "category": title,
          "text": entry["text"],
          "is_past": is_past,
      })

      # Für Matrix-Ansicht (alle Termine inkl. vergangene erfassen)
      all_dates.add(d)
      if d not in events_by_date:
        events_by_date[d] = {}
      events_by_date[d][title] = (entry["text"], is_past)

  # 2. Einzelseiten (z. B. docs/verein/termine/blitz.md) erzeugen
  # -> Alle Termine bleiben sichtbar, vergangene werden ausgegraut
  log_debug("--- Generiere Einzelseiten ---")
  for kat in kategorien:
    out_filepath = os.path.join(OUTPUT_DIR, kat["slug"])

    content = f"# {kat['title']}\n\n"

    if not kat["entries"]:
      content += "*Aktuell keine Termine eingetragen.*\n"
    else:
      content += "| Datum | Ereignis | Status |\n"
      content += "| :--- | :--- | :--- |\n"

      for entry in kat["entries"]:
        disp_date = entry["display_date"]
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
  # -> Nur anstehende / zukünftige Termine
  log_debug("--- Generiere Gesamtübersicht (nur anstehende Termine) ---")
  upcoming_events = [ev for ev in all_events if not ev["is_past"]]
  upcoming_events.sort(key=lambda x: (x["date"], x["category"]))

  gesamt_content = "# 📅 Anstehende Termine & Spielplan\n\n"
  gesamt_content += (
      "Hier findest Du alle anstehenden Termine in chronologischer"
      " Reihenfolge.\n\n"
  )

  if not upcoming_events:
    gesamt_content += "*Aktuell keine anstehenden Termine vorhanden.*\n"
  else:
    gesamt_content += "| Datum | Kategorie | Ereignis | Status |\n"
    gesamt_content += "| :--- | :--- | :--- | :--- |\n"

    for ev in upcoming_events:
      disp_date = ev["display_date"]
      gesamt_content += (
          f"| **{disp_date}** | `{ev['category']}` | **{ev['text']}** | ⏳ |\n"
      )

  with open(GESAMT_FILE, "w", encoding="utf-8") as f:
    f.write(gesamt_content)

  # 4. Matrix-Ansicht (docs/verein/termine/kalender-matrix.md) erzeugen
  # -> Alle Termine bleiben enthalten (vergangene ausgegraut & durchgestrichen)
  log_debug(
      "--- Generiere Matrix-Ansicht (alle Termine, vergangene ausgegraut) ---"
  )
  sorted_dates = sorted(list(all_dates))
  kat_titles = [k["title"] for k in kategorien]

  matrix_content = "# 📊 Terminplan - Matrix-Ansicht\n\n"
  matrix_content += (
      "| Datum | " + " | ".join(kat_titles) + " | Status |\n"
  )
  matrix_content += (
      "| :--- | " + " | ".join([":---"] * len(kat_titles)) + " | :--- |\n"
  )

  for d in sorted_dates:
    date_str = format_date_str(d)
    is_day_past = d < today

    row_cells = []
    has_event = False

    for kt in kat_titles:
      item = events_by_date.get(d, {}).get(kt)
      if item:
        has_event = True
        val, is_item_past = item
        if is_item_past or is_day_past:
          row_cells.append(f"<del style='color: #888;'>{val}</del>")
        else:
          row_cells.append(f"**{val}**")
      else:
        row_cells.append("")

    status = "🛑" if is_day_past else "⏳"
    d_display = (
        f"<del style='color: #888;'>{date_str}</del>"
        if is_day_past
        else f"**{date_str}**"
    )

    matrix_content += (
        f"| {d_display} | " + " | ".join(row_cells) + f" | {status} |\n"
    )

  with open(MATRIX_FILE, "w", encoding="utf-8") as f:
    f.write(matrix_content)

  log_debug("=== Termin-Build erfolgreich abgeschlossen ===")


if __name__ == "__main__":
  build_termine()
  
