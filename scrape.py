import os
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import html2text
import requests

BASE_URL = "https://www.tsfwelzheim.de"
LIST_URL = f"{BASE_URL}/abteilungen/schach/aktuelles/"
OUTPUT_DIR = "docs/aktuelles"


def main():
  # Zielordner erstellen, falls nicht vorhanden
  os.makedirs(OUTPUT_DIR, exist_ok=True)

  headers = {"User-Agent": "Mozilla/5.0 (compatible; ChessNewsScraper/1.0)"}
  response = requests.get(LIST_URL, headers=headers)
  response.raise_for_status()

  soup = BeautifulSoup(response.text, "html.parser")

  # Beiträge auf der Übersichtsseite finden (unterstützt gängige CMS-Strukturen)
  items = soup.find_all(
      ["article", "div"], class_=re.compile(r"news|post|item|teaser|article", re.I)
  )
  if not items:
    items = soup.select("main > *, .content > *")

  processed_count = 0

  for item in items:
    # Nur Elemente verarbeiten, die Überschriften enthalten (verhindert das Erfassen von Containern ohne Inhalt)
    if not item.find(["h1", "h2", "h3", "h4"]):
      continue

    processed_count += 1
    file_number = f"{processed_count:05d}"
    md_filepath = os.path.join(OUTPUT_DIR, f"{file_number}.md")
    img_folder_path = os.path.join(OUTPUT_DIR, file_number)
    img_dir_created = False

    # Bilder im Beitrag finden und herunterladen
    images = item.find_all("img")
    for img in images:
      img_url = img.get("src")
      if not img_url:
        continue
      img_url = urljoin(BASE_URL, img_url)

      try:
        img_res = requests.get(img_url, headers=headers)
        if img_res.status_code == 200:
          if not img_dir_created:
            os.makedirs(img_folder_path, exist_ok=True)
            img_dir_created = True

          parsed_url = urlparse(img_url)
          img_name = os.path.basename(parsed_url.path) or "image.jpg"
          img_local_path = os.path.join(img_folder_path, img_name)

          with open(img_local_path, "wb") as f:
            f.write(img_res.content)

          # Pfad im Markdown auf den lokalen Ordner anpassen
          img["src"] = f"./{file_number}/{img_name}"
      except Exception as e:
        print(f"Fehler beim Herunterladen des Bildes {img_url}: {e}")

    # HTML in sauberes Markdown konvertieren
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.body_width = 0  # Kein automatisches Zeilenumbruch-Wrapping
    markdown_content = h.handle(str(item))

    with open(md_filepath, "w", encoding="utf-8") as f:
      f.write(markdown_content)

    print(f"Erstellt: {md_filepath}")


if __name__ == "__main__":
  main()
