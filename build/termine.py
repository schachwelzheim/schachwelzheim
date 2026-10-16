from datetime import datetime
import os
import re

INPUT_DIR = "content/termine"
OUTPUT_DIR = "docs/termine"


def parse_date(date_str):
  """Liest ein Datum im Format D.M.YY, DD.MM.YY oder DD.MM.YYYY"""
  match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{2,4})', date_str)
  if not match:
    return None

  day, month, year = match.groups()
  if len(year) == 2:
    year = '20' + year

  try:
    return datetime(int(year), int(month), int(day)).date()
  except ValueError:
    return None


def format_date_str(date_obj):
  return date_obj.strftime('%d.%m.%Y')


def parse_termine_file(filepath):
  with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

  title = ''
  entries = []

  for line in lines:
    line_str = line.strip()
    if not line_str:
      continue

    if line_str.startswith('#'):
      title = line_str.lstrip('#').strip()
      continue

    date_obj = parse_date(line_str)
    if date_obj:
      event_text = re.sub(
          r'^\s*\d{1,2}\.\d{1,2}\.\d{2,4}\s*', '', line_str
      ).strip()
      entries.append({
          'date': date_obj,
          'text': event_text,
      })

  return title, entries


def build_termine():
  if not os.path.exists(INPUT_DIR):
    print(f'Hinweis: Ordner "{INPUT_DIR}" nicht gefunden.')
    return

  os.makedirs(OUTPUT_DIR, exist_ok=True)
  today = datetime.now().date()

  all_events = []
  kategorien = []

  for filename in sorted(os.listdir(INPUT_DIR)):
    if not filename.endswith('.md'):
      continue

    filepath = os.path.join(INPUT_DIR, filename)
    title, entries = parse_termine_file(filepath)
    if not title:
      title = filename.replace('.md', '').capitalize()

    # Nach Datum sortieren (älteste zuerst)
    entries.sort(key=lambda x: x['date'])

    kategorien.append({'slug': filename, 'title': title, 'entries': entries})

    for entry in entries:
      all_events.append({
          'date': entry['date'],
          'category': title,
          'text': entry['text'],
      })

  # 1. Einzelseiten generieren
  for kat in kategorien:
    out_filepath = os.path.join(OUTPUT_DIR, kat['slug'])
    content = f'# {kat["title"]}\n\n'
    content += '| Datum | Event | Status |\n'
    content += '| :--- | :--- | :--- |\n'

    for entry in kat['entries']:
      date_formatted = format_date_str(entry['date'])
      is_past = entry['date'] < today

      if is_past:
        content += (
            f"| <del style='color: gray;'>{date_formatted}</del> | <del"
            f" style='color: gray;'>{entry['text']}</del> | 🛑 *Vergangen* |\n"
        )
      else:
        content += (
            f'| **{date_formatted}** | {entry["text"]} | ⏳ *Anstehend* |\n'
        )

    with open(out_filepath, 'w', encoding='utf-8') as f:
      f.write(content)

  # 2. Gesamte Übersichtsseite (docs/termine/index.md) generieren
  all_events.sort(key=lambda x: (x['date'], x['category']))

  index_filepath = os.path.join(OUTPUT_DIR, 'index.md')
  index_content = '# 📅 Gesamter Terminplan\n\n'
  index_content += '| Datum | Kategorie | Event | Status |\n'
  index_content += '| :--- | :--- | :--- | :--- |\n'

  for ev in all_events:
    date_formatted = format_date_str(ev['date'])
    is_past = ev['date'] < today

    if is_past:
      index_content += (
          f"| <del style='color: gray;'>{date_formatted}</del> | <del"
          f" style='color: gray;'>{ev['category']}</del> | <del"
          f" style='color: gray;'>{ev['text']}</del> | 🛑 |\n"
      )
    else:
      index_content += (
          f'| **{date_formatted}** | `{ev["category"]}` | **{ev["text"]}** | ⏳'
          ' |\n'
      )

  with open(index_filepath, 'w', encoding='utf-8') as f:
    f.write(index_content)

  print('Termin-Build erfolgreich durchgeführt!')


if __name__ == '__main__':
  build_termine()
  
