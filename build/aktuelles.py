import os
import re

from .markdown import (
    read_file,
    write_file,
    get_title,
    get_teaser,
)


DOCS_DIR = "docs"
AKTUELLES_DIR = os.path.join(DOCS_DIR, "aktuelles")

IGNORED_FILES = {
    "index.md",
    "aktuelles-tags.md",
}


def get_post_files():
    if not os.path.exists(AKTUELLES_DIR):
        return []

    files = [
        f for f in os.listdir(AKTUELLES_DIR)
        if f.endswith(".md") and f not in IGNORED_FILES
    ]

    date_files = []
    number_files = []
    other_files = []

    for filename in files:
        name = os.path.splitext(filename)[0]

        if re.match(r"^\d{4}-\d{2}-\d{2}$", name):
            date_files.append(filename)

        elif re.match(r"^\d+$", name):
            number_files.append(filename)

        else:
            other_files.append(filename)

    date_files.sort()
    number_files.sort(
        key=lambda x: int(os.path.splitext(x)[0])
    )
    other_files.sort()

    return date_files + number_files + other_files


def format_date(filename):
    match = re.match(
        r"^(\d{4})-(\d{2})-(\d{2})",
        os.path.splitext(filename)[0]
    )

    if not match:
        return ""

    year, month, day = match.groups()
    return f"{day}.{month}.{year}"


def get_images(post_name):
    folder = os.path.join(AKTUELLES_DIR, post_name)

    if not os.path.isdir(folder):
        return []

    valid_extensions = (
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
    )

    return sorted(
        filename
        for filename in os.listdir(folder)
        if filename.lower().endswith(valid_extensions)
    )


def build_gallery(filename, images):
    path = os.path.join(AKTUELLES_DIR, filename)

    content = read_file(path)

    marker = "\n\n## Bilder zum Beitrag\n"

    if marker in content:
        content = content.split(marker)[0]

    if images:
        content += "\n\n## Bilder zum Beitrag\n\n"
        content += '<div class="gallery" markdown>\n\n'

        for image in images:
            content += (
                f'<a class="glightbox" href="{image}">'
                f'<img src="{image}" width="300" '
                f'style="border-radius: 8px; margin: 8px;" />'
                f'</a>\n'
            )

        content += "\n</div>\n"

    write_file(path, content)


def collect_posts():
    posts = []

    for filename in get_post_files():
        path = os.path.join(AKTUELLES_DIR, filename)
        content = read_file(path)

        name = os.path.splitext(filename)[0]

        title = get_title(content)

        if not title:
            title = name.replace("-", " ").capitalize()

        posts.append({
            "filename": filename,
            "title": title,
            "teaser": get_teaser(content),
            "date": format_date(filename),
            "images": get_images(name),
        })

    return posts


def build_index(posts):
    path = os.path.join(AKTUELLES_DIR, "index.md")

    if os.path.exists(path):
        existing = read_file(path)

        if "\n\n## Beiträge\n" in existing:
            existing = existing.split("\n\n## Beiträge\n")[0]

        index_content = existing.strip()

    else:
        index_content = (
            "# Aktuelles aus der Schachabteilung\n\n"
            "Hier findest du alle Neuigkeiten."
        )

    index_content += "\n\n## Beiträge\n\n"

    for post in posts:
        date = (
            f"**[{post['date']}]** "
            if post["date"]
            else ""
        )

        index_content += (
            f"* {date}"
            f"**[{post['title']}]({post['filename']})** "
            f"– {post['teaser']} "
            f"[weiterlesen]({post['filename']})\n"
        )

    write_file(path, index_content)


def build_aktuelles():
    if not os.path.exists(AKTUELLES_DIR):
        return []

    posts = collect_posts()

    for post in posts:
        build_gallery(
            post["filename"],
            post["images"]
        )

    build_index(posts)

    return posts
