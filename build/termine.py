from datetime import datetime
import os
import re
import time

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Dynamische Pfadermittlung
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_DIR = os.path.join(BASE_DIR, "content", "termine")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "verein", "termine")
TURNIERE_FILE = os.path.join(BASE_DIR, "docs", "verein", "turniere", "index.md")
JUGEND_TERMINE_FILE = os.path.join(BASE_DIR, "docs", "jugend", "termine.md")

GESAMT_FILE = os.path.join(OUTPUT_DIR, "index.md")
MATRIX_FILE = os.path.join(OUTPUT_DIR, "kalender-matrix.md")
PDF_FILE = os.path.join(OUTPUT_DIR, "terminplan.pdf")

EXCEL_ORDER = [
    "TSF Welzheim I",
    "Spraitbach",
    "Blitz",
    "Schnell",
    "Normal",
    "Theorie",
    "Jugendschach",
    "Turniere Aktive",
    "Ferien",
]


def clean_markdown_links(text):
  if not text:
    return ""
  return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)


def parse_date(date_str):
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


def format_weekday_date(date_obj):
  wochentage = [
      "Montag",
      "Dienstag",
      "Mittwoch",
      "Donnerstag",
      "Freitag",
      "Samstag",
      "Sonntag",
  ]
  tagname = wochentage[date_obj.weekday()]
  return f"{tagname}, {date_obj.strftime('%d.%m.%Y')}"


def parse_termine_file(filepath):
  with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

  title = ""
  entries = []

  for line in lines:
    line_str = line.strip()
    if not line_str:
      continue

    if line_str.startswith("#"):
      title = line_str.lstrip("#").strip()
      continue

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
        continue

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

  return title, entries


def sort_kategorien(kategorien):
  def get_sort_index(kat):
    title = kat["title"].lower()
    slug = kat["slug"].lower()

    for idx, key in enumerate(EXCEL_ORDER):
      k_lower = key.lower()
      if k_lower in title or k_lower in slug:
        return idx
    return 999

  return sorted(kategorien, key=get_sort_index)


def get_short_category(category_title):
  cat_lower = category_title.lower()

  if "welzheim 1" in cat_lower or "welzheim i" in cat_lower:
    return "Welzheim 1"
  if "jugend" in cat_lower:
    return "Jugend"
  if "spraitbach" in cat_lower:
    return "Spraitbach/Welzheim 2"

  return category_title


def generate_pdf_matrix(
    sorted_upcoming_dates, kat_titles, events_by_date, date_display_map
):
  doc = SimpleDocTemplate(
      PDF_FILE,
      pagesize=landscape(A4),
      rightMargin=15,
      leftMargin=15,
      topMargin=15,
      bottomMargin=15,
  )

  styles = getSampleStyleSheet()

  title_style = ParagraphStyle(
      "TitleStyle",
      parent=styles["Heading1"],
      fontSize=13,
      leading=16,
      textColor=colors.HexColor("#1b4332"),
      spaceAfter=6,
  )

  header_cell_style = ParagraphStyle(
      "HeaderCellStyle",
      parent=styles["Normal"],
      fontSize=7,
      leading=8,
      fontName="Helvetica-Bold",
      textColor=colors.white,
      alignment=1,
  )

  cell_style = ParagraphStyle(
      "BodyCellStyle",
      parent=styles["Normal"],
      fontSize=6,
      leading=7,
      textColor=colors.HexColor("#2b2b2b"),
      alignment=1,
  )

  span_cell_style = ParagraphStyle(
      "SpanCellStyle",
      parent=styles["Normal"],
      fontSize=7,
      leading=8,
      fontName="Helvetica-Bold",
      textColor=colors.HexColor("#1b4332"),
      alignment=1,
  )

  date_cell_style = ParagraphStyle(
      "DateCellStyle",
      parent=styles["Normal"],
      fontSize=6,
      leading=7,
      fontName="Helvetica-Bold",
      textColor=colors.HexColor("#1b4332"),
      alignment=1,
  )

  elements = [
      Paragraph("Schach in Welzheim – Anstehende Termine", title_style),
      Spacer(1, 4),
  ]

  table_data = [[
      Paragraph("Datum", header_cell_style)
  ] + [Paragraph(title, header_cell_style) for title in kat_titles]]

  t_styles = [
      ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d6a4f")),
      ("ALIGN", (0, 0), (-1, -1), "CENTER"),
      ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
      ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d3d3d3")),
      (
          "ROWBACKGROUNDS",
          (0, 1),
          (-1, -1),
          [colors.HexColor("#f8f9fa"), colors.white],
      ),
      ("TOPPADDING", (0, 0), (-1, -1), 2),
      ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
  ]

  for row_idx, d in enumerate(sorted_upcoming_dates, start=1):
    disp_date = date_display_map.get(d, format_date_str(d))

    is_span_event = False
    span_text = ""
    for kt in kat_titles:
      item = events_by_date.get(d, {}).get(kt)
      if item and "WAM/WJPT/SSGT in Welzheim" in item[0]:
        is_span_event = True
        span_text = clean_markdown_links(item[0])
        break

    if is_span_event:
      row = [Paragraph(disp_date, date_cell_style)]
      row.append(Paragraph(f"🏆 {span_text}", span_cell_style))
      row.extend([Paragraph("", cell_style)] * (len(kat_titles) - 1))

      t_styles.append(("SPAN", (1, row_idx), (-1, row_idx)))
      t_styles.append(
          ("BACKGROUND", (1, row_idx), (-1, row_idx), colors.HexColor("#d8f3dc"))
      )
    else:
      row = [Paragraph(disp_date, date_cell_style)]
      for kt in kat_titles:
        item = events_by_date.get(d, {}).get(kt)
        val = clean_markdown_links(item[0]) if item else ""
        row.append(Paragraph(val, cell_style))

    table_data.append(row)

  if len(table_data) > 1:
    num_cols = len(kat_titles) + 1
    col_width = 812 / num_cols

    t = Table(table_data, colWidths=[col_width] * num_cols, repeatRows=1)
    t.setStyle(TableStyle(t_styles))
    elements.append(t)
  else:
    elements.append(
        Paragraph(
            "Aktuell keine anstehenden Termine vorhanden.", styles["Normal"]
        )
    )

  doc.build(elements)


def generate_turniere_page(kategorien_by_slug):
  """Befüllt die Platzhalter-Kommentare in docs/verein/turniere/index.md mit aktuellen Terminen."""
  if not os.path.exists(TURNIERE_FILE):
    return

  with open(TURNIERE_FILE, "r", encoding="utf-8") as f:
    content = f.read()

  # 1. Blitztermine
  blitz_entries = kategorien_by_slug.get("blitz.md", {}).get("entries", [])
  blitz_lines = []
  for entry in blitz_entries:
    formatted_d = format_weekday_date(entry["date"])
    blitz_lines.append(f"    *   **{entry['text']}:** {formatted_d}")
  blitz_text = "\n".join(blitz_lines)

  # 2. Schnelltermine
  schnell_entries = kategorien_by_slug.get("schnell.md", {}).get("entries", [])
  schnell_lines = []
  for entry in schnell_entries:
    formatted_d = format_weekday_date(entry["date"])
    schnell_lines.append(f"    *   **{entry['text']}:** {formatted_d}")
  schnell_text = "\n".join(schnell_lines)

  # 3. Stadtmeisterschaftstermine (normal.md)
  normal_entries = kategorien_by_slug.get("normal.md", {}).get("entries", [])
  normal_lines = []
  for entry in normal_entries:
    formatted_d = format_weekday_date(entry["date"])
    normal_lines.append(f"    *   **{entry['text']}:** {formatted_d}")
  normal_text = "\n".join(normal_lines)

  # Ersetzen der Platzhalter
  content = re.sub(
      r"<!--\s*Blitztermine.*?\s*-->",
      blitz_text,
      content,
      flags=re.IGNORECASE | re.DOTALL,
  )
  content = re.sub(
      r"<!--\s*Schnelltermine.*?\s*-->",
      schnell_text,
      content,
      flags=re.IGNORECASE | re.DOTALL,
  )
  content = re.sub(
      r"<!--\s*Stadtmeisterschaftstermine.*?\s*-->",
      normal_text,
      content,
      flags=re.IGNORECASE | re.DOTALL,
  )

  with open(TURNIERE_FILE, "w", encoding="utf-8") as f:
    f.write(content)


def build_termine():
  if not os.path.exists(INPUT_DIR):
    return

  os.makedirs(OUTPUT_DIR, exist_ok=True)
  today = datetime.now().date()
  cache_buster = int(time.time())

  all_events = []
  raw_kategorien = []
  kategorien_by_slug = {}
  all_dates = set()
  events_by_date = {}
  date_display_map = {}

  files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".md")]

  for filename in files:
    filepath = os.path.join(INPUT_DIR, filename)
    title, entries = parse_termine_file(filepath)

    if not title:
      title = filename.replace(".md", "").capitalize()

    entries.sort(key=lambda x: x["date"])
    kat_obj = {
        "slug": filename,
        "title": title,
        "entries": entries,
    }
    raw_kategorien.append(kat_obj)
    kategorien_by_slug[filename] = kat_obj

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

      if not is_past:
        all_dates.add(d)
        if d not in date_display_map or "–" in entry["display_date"]:
          date_display_map[d] = entry["display_date"]

        if d not in events_by_date:
          events_by_date[d] = {}
        events_by_date[d][title] = (entry["text"], is_past)

  kategorien = sort_kategorien(raw_kategorien)
  kat_titles = [k["title"] for k in kategorien]

  # 1. Einzelseiten
  for kat in kategorien:
    out_filepath = os.path.join(OUTPUT_DIR, kat["slug"])
    
    # Aufbau der Tabelle
    table_body = ""
    if not kat["entries"]:
      table_body = "*Aktuell keine Termine eingetragen.*\n"
    else:
      table_body = "| Datum | Ereignis | Status |\n"
      table_body += "| :--- | :--- | :--- |\n"

      for entry in kat["entries"]:
        disp_date = entry["display_date"]
        check_date = (
            entry["end_date"] if entry["end_date"] else entry["date"]
        )
        is_past = check_date < today

        if is_past:
          table_body += (
              f"| <del style='color: #888;'>{disp_date}</del> | <del"
              f" style='color: #888;'>{entry['text']}</del> | 🛑 *Vergangen* |\n"
          )
        else:
          table_body += f"| **{disp_date}** | **{entry['text']}** | ⏳ *Anstehend* |\n"

    # Schreiben der regulären Vereins-Kategorieseite
    with open(out_filepath, "w", encoding="utf-8") as f:
      f.write(f"# {kat['title']}\n\n" + table_body)

    # Wenn es Jugendschach ist, zusätzlich unter docs/jugend/termine.md mit Überschrift "# Termine" schreiben
    if kat["slug"].lower() == "jugendschach.md":
      os.makedirs(os.path.dirname(JUGEND_TERMINE_FILE), exist_ok=True)
      with open(JUGEND_TERMINE_FILE, "w", encoding="utf-8") as f:
        f.write("# Termine\n\n" + table_body)

  # 2. Gesamtübersicht (index.md)
  upcoming_events = [ev for ev in all_events if not ev["is_past"]]
  upcoming_events.sort(key=lambda x: (x["date"], x["category"]))

  gesamt_content = "# Termine\n\n"
  gesamt_content += (
      f"[📄 Terminplan als DIN A4 PDF herunterladen](terminplan.pdf?v={cache_buster}){{:"
      " .md-button .md-button--primary }\n\n"
  )
  gesamt_content += (
      "Hier findest Du alle anstehenden Termine in chronologischer"
      " Reihenfolge.\n\n"
  )

  if not upcoming_events:
    gesamt_content += "*Aktuell keine anstehenden Termine vorhanden.*\n"
  else:
    gesamt_content += "| Datum | Kategorie | Ereignis |\n"
    gesamt_content += "| :--- | :--- | :--- |\n"

    for ev in upcoming_events:
      disp_date = ev["display_date"]
      short_cat = get_short_category(ev["category"])
      gesamt_content += (
          f"| **{disp_date}** | `{short_cat}` | **{ev['text']}** |\n"
      )

  with open(GESAMT_FILE, "w", encoding="utf-8") as f:
    f.write(gesamt_content)

  # 3. Matrix-Ansicht (kalender-matrix.md)
  sorted_upcoming_dates = sorted(list(all_dates))

  matrix_content = "# 📊 Anstehende Termine - Matrix-Ansicht\n\n"
  matrix_content += (
      f"[📄 Anstehende Termine als A4 PDF herunterladen](terminplan.pdf?v={cache_buster}){{:"
      " .md-button .md-button--primary }\n\n"
  )
  matrix_content += "| Datum | " + " | ".join(kat_titles) + " |\n"
  matrix_content += (
      "| :--- | " + " | ".join([":---"] * len(kat_titles)) + " |\n"
  )

  for d in sorted_upcoming_dates:
    disp_date = date_display_map.get(d, format_date_str(d))
    row_cells = []
    for kt in kat_titles:
      item = events_by_date.get(d, {}).get(kt)
      val = item[0] if item else ""
      row_cells.append(f"**{val}**" if val else "")

    matrix_content += f"| **{disp_date}** | " + " | ".join(row_cells) + " |\n"

  with open(MATRIX_FILE, "w", encoding="utf-8") as f:
    f.write(matrix_content)

  # 4. DIN A4 PDF Matrix generieren
  generate_pdf_matrix(
      sorted_upcoming_dates, kat_titles, events_by_date, date_display_map
  )

  # 5. Platzhalter in docs/verein/turniere/index.md befüllen
  generate_turniere_page(kategorien_by_slug)


if __name__ == "__main__":
  build_termine()
      
