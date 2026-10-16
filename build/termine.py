def parse_date(date_str):
  """Liest ein Datum im Format D.M.YY, DD.MM.YY oder DD.MM.YYYY"""
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

    # 1. Prüfe zuerst, ob es ein Zeitraum ist (z. B. 1.8.26 - 13.9.26 Sommerferien)
    range_match = re.search(
        r"^(\d{1,2}\.\d{1,2}\.\d{2,4})\s*-\s*(\d{1,2}\.\d{1,2}\.\d{2,4})\s+(.*)$",
        line_str,
    )

    if range_match:
      start_str, end_str, event_text = range_match.groups()
      start_date = parse_date(start_str)
      end_date = parse_date(end_str)

      if start_date:
        entries.append({
            "date": start_date,
            "end_date": end_date,
            "display_date": (
                f"{format_date_str(start_date)} – {format_date_str(end_date)}"
                if end_date
                else format_date_str(start_date)
            ),
            "text": event_text.strip(),
        })
        continue

    # 2. Einzeldatum (z. B. 6.11.26 Runde 1)
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
  
