import os
import re

from .markdown import (
    read_file,
    write_file,
    get_tags,
    get_title,
)


DOCS_DIR = "docs"
AKTUELLES_DIR = os.path.join(DOCS_DIR, "aktuelles")


def slugify(text):
    text = text.lower().strip()

    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
    }

    for old, new, in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")

    return text


def relative_link(source, target):
    source_dir = os.path.dirname(source)

    link = os.path.relpath(
        target,
        source_dir
    )

    return link.replace(os.sep, "/")


def collect_tagged_pages():
    pages = []

    for root, _, files in os.walk(DOCS_DIR):
        if "tags" in root.split(os.sep) or "themen" in root.split(os.sep):
            continue

        for filename in files:
            if not filename.endswith(".md"):
                continue

            if filename == "aktuelles-tags.md":
                continue

            path = os.path.join(root, filename)
            content = read_file(path)
            tags = get_tags(content)

            if not tags:
                continue

            relative_path = os.path.relpath(
                path,
                DOCS_DIR
            ).replace(os.sep, "/")

            title = get_title(content)

            if not title:
                title = os.path.splitext(filename)[0]

            pages.append({
                "path": relative_path,
                "title": title,
                "tags": tags,
            })

    return pages


def build_tags():
    pages = collect_tagged_pages()

    # Nach Themen gruppieren
    tags = {}
    for page in pages:
        for tag in page["tags"]:
            tags.setdefault(tag, []).append(page)

    path = os.path.join(
        AKTUELLES_DIR,
        "aktuelles-tags.md"
    )

    lines = [
        "# Beiträge nach Themen",
        "",
        "Hier findest du alle Beiträge nach Themen sortiert.",
        "",
        '<div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 2rem;">',
    ]

    # Obere Tag-Wolke mit Ankern (#slug)
    for tag in sorted(tags, key=str.lower):
        slug = slugify(tag)
        if not slug:
            continue
        lines.append(f'  <a href="#tag:{slug}" class="md-tag">{tag}</a>')

    lines.append('</div>')
    lines.append("")
    lines.append("---")
    lines.append("")


    write_file(path, "\n".join(lines))

    return tags
    
