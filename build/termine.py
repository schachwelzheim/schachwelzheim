from datetime import datetime
import os
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Dynamische Pfadermittlung (Projekt-Hauptverzeichnis)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_DIR = os.path.join(BASE_DIR, "content", "termine")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "verein", "termine")

GESAMT_FILE = os.path.join(OUTPUT_DIR, "index.md")
MATRIX_FILE = os.path.join(OUTPUT_DIR, "kalender-matrix.md")
PDF_FILE = os.path.join(OUTPUT_DIR, "terminplan.pdf")


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

  return title, entries


def generate_pdf_matrix(sorted_upcoming_dates, kat_titles, events_by_date):
  """Generiert ein DIN A4 Querformat-PDF mit allen anstehenden Terminen als Matrix-Tabelle."""
  doc = SimpleDocTemplate(
      PDF_FILE,
      pagesize=landscape(A4),
      rightMargin=20,
      leftMargin=20,
      topMargin=20,
      bottomMargin=20,
  )

  styles = getSampleStyleSheet()

  title_style = ParagraphStyle(
      "TitleStyle",
      parent=styles["Heading1"],
      fontSize=16,
      leading=20,
      textColor=colors.HexColor("#1b4332"),
      spaceAfter=10,
  )

  header_cell_style = ParagraphStyle(
      "HeaderCellStyle",
      parent=styles["Normal"],
      fontSize=8,
      leading=10,
      fontName="Helvetica-Bold",
      textColor=colors.white,
      alignment=1,
  )

  cell_style = ParagraphStyle(
      "BodyCellStyle",
      parent=styles["Normal"],
      fontSize=7,
      leading=9,
      textColor=colors.HexColor("#2b2b2b"),
      alignment=1,
  )

  date_cell_style = ParagraphStyle(
      "DateCellStyle",
      parent=styles["Normal"],
      fontSize=7,
      leading=9,
      fontName="Helvetica-Bold",
      textColor=colors.HexColor("#1b4332"),
      alignment=1,
  )

  elements = [
      Paragraph("Schach in Welzheim – Anstehende Termine", title_style),
      Spacer(1, 10),
  ]

  table_data = [[
      Paragraph("Datum", header_cell_style)
  ] + [Paragraph(title, header_cell_style) for title in kat_titles]]

  for d in sorted_upcoming_dates:
    row = [Paragraph(d.strftime("%d.%m.%Y"), date_cell_style)]
    for kt in kat_titles:
      item = events_by_date.get(d, {}).get(kt)
      val = item[0] if item else ""
      row.append(Paragraph(val, cell_style))
    table_data.append(row)

  if len(table_data) > 1:
    num_cols = len(kat_titles) + 1
    col_width = 800 / num_cols

    t = Table(table_data, colWidths=[col_width] * num_cols, repeatRows=1)
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d6a4f")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d3d3d3")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.HexColor("#f8f9fa"),
                colors.white,
            ]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    elements.append(t)
  else:
    elements.append(
        Paragraph(
            "Aktuell keine anstehenden Termine vorhanden.", styles["Normal"]
        )
    )

  doc.build(elements)


def build_termine():
  """Hauptfunktion zum Verarbeiten aller Termine und Generieren der Markdown-Seiten und des PDFs."""
  if not os.path.exists(INPUT_DIR):
    return

  os.makedirs(OUTPUT_DIR, exist_ok=True)
  today = datetime.now().date()

  all_events = []
  kategorien = []
  all_dates = set()
  events_by_date = {}

  files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".md")]

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

      all_dates.add(d)
      if d not in events_by_date:
        events_by_date[d] = {}
      events_by_date[d][title] = (entry["text"], is_past)

  # 2. Einzelseiten (z. B. docs/verein/termine/blitz.md) erzeugen
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
  upcoming_events = [ev for ev in all_events if not ev["is_past"]]
  upcoming_events.sort(key=lambda x: (x["date"], x["category"]))

  gesamt_content = "# 📅 Anstehende Termine & Spielplan\n\n"
  gesamt_content += (
      "[📄 Terminplan als DIN A4 PDF"
      " herunterladen](terminplan.pdf){: .md-button .md-button--primary }\n\n"
  )
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
  sorted_dates = sorted(list(all_dates))
  kat_titles = [k["title"] for k in kategorien]

  matrix_content = "# 📊 Terminplan - Matrix-Ansicht\n\n"
  matrix_content += (
      "[📄 Anstehende Termine als A4 PDF"
      " herunterladen](terminplan.pdf){: .md-button .md-button--primary }\n\n"
  )
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
    for kt in kat_titles:
      item = events_by_date.get(d, {}).get(kt)
      if item:
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

  # 5. DIN A4 PDF Matrix generieren (nur anstehende Termine)
  upcoming_dates = [d for d in sorted_dates if d >= today]
  generate_pdf_matrix(upcoming_dates, kat_titles, events_by_date)


if __name__ == "__main__":
  build_termine()
    
