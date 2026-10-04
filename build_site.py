import os
import yaml
import re

docs_dir = "docs"
aktuelles_dir = os.path.join(docs_dir, "aktuelles")
nav = []

def parse_markdown_file(file_path):
    title = ""
    teaser_words = []
    tags = []
    in_frontmatter = False
    frontmatter_lines = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
            # Frontmatter (YAML) parsen
            if lines and lines[0].strip() == "---":
                in_frontmatter = True
                for line in lines[1:]:
                    if line.strip() == "---":
                        in_frontmatter = False
                        break
                    frontmatter_lines.append(line)
            
            # Tags aus Frontmatter extrahieren (unterstützt YAML-Listen und Inline-Arrays)
            fm_content = "".join(frontmatter_lines)
            tag_match = re.search(r"tags:\s*\[(.*?)\]", fm_content)
            if tag_match:
                tags = [t.strip().strip("'\"") for t in tag_match.group(1).split(",")]
            else:
                is_tag_section = False
                for line in frontmatter_lines:
                    if line.strip().startswith("tags:"):
                        is_tag_section = True
                        continue
                    if is_tag_section:
                        if line.strip().startswith("- "):
                            tags.append(line.strip()[2:].strip().strip("'\""))
                        elif line.strip() and not line.startswith(" "):
                            is_tag_section = False

            # Titel und Teaser ermitteln
            for line in lines:
                clean_line = line.strip()

                if not title and clean_line.startswith("# "):
                    title = clean_line[2:].strip()
                    continue

                if not title:
                    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", clean_line, re.IGNORECASE)
                    if h1_match:
                        title = re.sub(r"<br\s*/?>", " ", h1_match.group(1), flags=re.IGNORECASE)
                        title = re.sub(r"<[^>]+>", "", title).strip()
                        continue

                if title and clean_line and not clean_line.startswith("#") and not clean_line.startswith("---"):
                    if re.match(r"^\d+\.", clean_line):
                        continue
                    words = re.findall(r"\b\w+\b", clean_line)
                    teaser_words.extend(words)
                    if len(teaser_words) >= 10:
                        break

    except Exception:
        pass

    teaser = " ".join(teaser_words[:10]) + "..." if teaser_words else "Keine Vorschau verfügbar..."
    return title, teaser, tags


# ============================================================
# AKTUELLES
# ============================================================

news_items = []

if os.path.exists(aktuelles_dir):

    md_files = sorted(
        [
            f for f in os.listdir(aktuelles_dir)
            if f.endswith(".md") and f != "index.md"
        ],
        reverse=True
    )

    for filename in md_files:
        file_path = os.path.join(aktuelles_dir, filename)
        base_name = os.path.splitext(filename)[0]
        default_title = base_name

        title, teaser, tags = parse_markdown_file(file_path)

        if not title:
            title = default_title.replace("-", " ").capitalize()

        date_match = re.match(r"(\d{4})-(\d{2})-(\d{2})", base_name)
        if date_match:
            year, month, day = date_match.groups()
            formatted_date = f"{day}.{month}.{year}"
        else:
            formatted_date = ""

        img_folder = os.path.join(aktuelles_dir, base_name)
        images = []
        if os.path.exists(img_folder) and os.path.isdir(img_folder):
            valid_exts = (".png", ".jpg", ".jpeg", ".gif", ".webp")
            images = sorted([img for img in os.listdir(img_folder) if img.lower().endswith(valid_exts)])

        news_items.append({
            "filename": filename,
            "base_name": base_name,
            "title": title,
            "teaser": teaser,
            "date": formatted_date,
            "images": images,
            "tags": tags
        })


    # ========================================================
    # GALERIEN IN BEITRÄGEN AKTUALISIEREN
    # ========================================================

    for item in news_items:
        file_path = os.path.join(aktuelles_dir, item["filename"])
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if "\n\n## Bilder zum Beitrag\n" in content:
            content = content.split("\n\n## Bilder zum Beitrag\n")[0]

        if item["images"]:
            content += "\n\n## Bilder zum Beitrag\n\n"
            content += '<div class="gallery" markdown>\n\n'
            for img in item["images"]:
                content += f'<a class="glightbox" href="{img}"><img src="{img}" width="300" style="border-radius: 8px; margin: 8px;" /></a>\n'
            content += "\n</div>\n"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)


    # ========================================================
    # AKTUELLES INDEX AKTUALISIEREN (Mit klickbaren Tag-Badges oben)
    # ========================================================

    index_path = os.path.join(aktuelles_dir, "index.md")
    existing_index_content = ""

    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            existing_index_content = f.read()

        if "\n\n## Beiträge\n" in existing_index_content:
            existing_index_content = existing_index_content.split("\n\n## Beiträge\n")[0]
        if "## Nach Themen filtern" in existing_index_content:
            existing_index_content = existing_index_content.split("## Nach Themen filtern")[0]

    if existing_index_content.strip():
        index_content = existing_index_content.strip()
    else:
        index_content = "# Aktuelles aus der Schachabteilung\n\nHier findest du alle Neuigkeiten."

    # Alle einzigartigen Tags aus den News-Items sammeln
    all_tags = sorted(list(set(tag for item in news_items for tag in item["tags"])))

    # Klickbare Tag-Leiste vor den Beiträgen einfügen (verlinkt auf die MkDocs-Tag-Seiten)
    if all_tags:
        index_content += "\n\n## Nach Themen filtern\n\n"
        badge_html = " ".join([f'<a href="../tags/#{tag.lower()}" class="md-tag" style="display: inline-block; padding: 4px 10px; margin: 4px; background-color: var(--md-primary-fg-color); color: var(--md-primary-bg-color); border-radius: 4px; text-decoration: none; font-size: 0.85rem;">{tag}</a>' for tag in all_tags])
        index_content += f'<div class="tag-cloud" style="margin-bottom: 20px;">\n{badge_html}\n</div>\n'

    index_content += "\n\n## Beiträge\n\n"

    for item in news_items:
        d_str = f"**[{item['date']}]** " if item['date'] else ""
        index_content += f"* {d_str}**[{item['title']}]({item['filename']})** – {item['teaser']} [weiterlesen]({item['filename']})\n"

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)


# ============================================================
# RESTLICHE ORDNER SCANNEN
# ============================================================
def scan_folder(path):
    items = []
    entries = sorted(os.listdir(path), reverse=True)
    for entry in entries:
        full_path = os.path.join(path, entry)
        rel_path = os.path.relpath(full_path, docs_dir)

        if os.path.isdir(full_path):
            if any(item["base_name"] == entry for item in news_items):
                continue
            sub_items = scan_folder(full_path)
            if sub_items:
                sub_index = os.path.join(full_path, "index.md")
                folder_title = ""
                if os.path.exists(sub_index):
                    folder_title, _, _ = parse_markdown_file(sub_index)
                if not folder_title:
                    folder_title = entry.replace("_", " ").replace("-", " ").capitalize()
                
                sub_index_rel = os.path.relpath(sub_index, docs_dir).replace(os.sep, "/")
                sub_nav_list = [{"Übersicht": sub_index_rel}] + [i for i in sub_items if list(i.values())[0] != sub_index_rel]
                items.append({folder_title: sub_nav_list})

        elif entry.endswith(".md"):
            if entry == "index.md":
                continue
            name_without_ext = os.path.splitext(entry)[0]
            default_title = name_without_ext.replace("-", " ").capitalize()
            title, _, _ = parse_markdown_file(full_path)
            if not title:
                title = default_title
            items.append({title: rel_path.replace(os.sep, "/")})
    return items

# Startseite & Navigation zusammenbauen
start_index = os.path.join(docs_dir, "index.md")
if os.path.exists(start_index):
    start_title, _, _ = parse_markdown_file(start_index)
    if not start_title:
      start_title = "Startseite"
    nav.append({start_title: "index.md"})

aktuelles_items = scan_folder(aktuelles_dir)
if aktuelles_items:
    akt_index = os.path.join(aktuelles_dir, "index.md")
    akt_title, _, _ = parse_markdown_file(akt_index)
    if not akt_title:
      akt_title = "Aktuelles"
    aktuelles_nav_list = [{"Übersicht": "aktuelles/index.md"}] + [i for i in aktuelles_items if list(i.values())[0] != "aktuelles/index.md"]
    nav.append({akt_title: aktuelles_nav_list})

for entry in sorted(os.listdir(docs_dir)):
    full_path = os.path.join(docs_dir, entry)
    if os.path.isdir(full_path) and entry != "aktuelles":
        sub_items = scan_folder(full_path)
        if sub_items:
            sub_index = os.path.join(full_path, "index.md")
            folder_title = ""
            sub_index_rel = f"{entry}/index.md"
            if os.path.exists(sub_index):
                folder_title, _, _ = parse_markdown_file(sub_index)
            if not folder_title:
                folder_title = entry.replace("_", " ").replace("-", " ").capitalize()
            folder_nav_list = [{"Übersicht": sub_index_rel}] + [i for i in sub_items if list(i.values())[0] != sub_index_rel]
            nav.append({folder_title: folder_nav_list})

with open("mkdocs.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

config["nav"] = nav

with open("mkdocs.yml", "w", encoding="utf-8") as f:
    yaml.dump(config, f, allow_unicode=True, sort_keys=False)
    
