import os
import re
import yaml
import shutil

docs_dir = "docs"
aktuelles_dir = os.path.join(docs_dir, "aktuelles")
tags_dir = os.path.join(docs_dir, "tags")

nav = []
news_items = []


# ============================================================
# MARKDOWN-DATEI AUSLESEN
# ============================================================

def parse_markdown_file(file_path):
    title = ""
    teaser_words = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        in_frontmatter = False

        for line in lines:
            clean_line = line.strip()

            if clean_line == "---":
                in_frontmatter = not in_frontmatter
                continue

            if in_frontmatter:
                continue

            # Markdown-H1
            if not title and clean_line.startswith("# "):
                title = clean_line[2:].strip()
                continue

            # HTML-H1
            if not title:
                h1_match = re.search(
                    r"<h1[^>]*>(.*?)</h1>",
                    clean_line,
                    re.IGNORECASE
                )

                if h1_match:
                    title = re.sub(
                        r"<br\s*/?>",
                        " ",
                        h1_match.group(1),
                        flags=re.IGNORECASE
                    )

                    title = re.sub(
                        r"<[^>]+>",
                        "",
                        title
                    ).strip()

                    continue

            # Teaser
            if (
                title
                and clean_line
                and not clean_line.startswith("#")
                and not clean_line.startswith("---")
            ):
                if re.match(r"^\d+\.", clean_line):
                    continue

                words = re.findall(r"\b\w+\b", clean_line)
                teaser_words.extend(words)

                if len(teaser_words) >= 10:
                    break

    except Exception:
        pass

    teaser = (
        " ".join(teaser_words[:10]) + "..."
        if teaser_words
        else "Keine Vorschau verfügbar..."
    )

    return title, teaser


# ============================================================
# TAGS AUS FRONTMATTER LESEN
# ============================================================

def get_tags_from_file(file_path):

    tags = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        match = re.match(
            r"^\s*---\s*\n(.*?)\n---\s*(?:\n|$)",
            content,
            re.DOTALL
        )

        if not match:
            return tags

        frontmatter = yaml.safe_load(match.group(1))

        if not isinstance(frontmatter, dict):
            return tags

        raw_tags = frontmatter.get("tags", [])

        if isinstance(raw_tags, str):
            raw_tags = [raw_tags]

        if not isinstance(raw_tags, list):
            return tags

        for tag in raw_tags:

            if tag is None:
                continue

            tag = str(tag).strip()

            if tag:
                tags.append(tag)

    except Exception:
        pass

    return tags


# ============================================================
# SICHEREN DATEINAMEN AUS TAG ERZEUGEN
# ============================================================

def slugify_tag(tag):

    slug = tag.casefold().strip()

    # Umlaute
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss"
    }

    for old, new in replacements.items():
        slug = slug.replace(old, new)

    # Alles außer Buchstaben/Zahlen durch -
    slug = re.sub(r"[^a-z0-9]+", "-", slug)

    slug = slug.strip("-")

    return slug


# ============================================================
# ALLE TAGS SAMMELN
# ============================================================

def collect_all_tags():

    all_tags = {}

    for root, dirs, files in os.walk(docs_dir):

        # Generierte Tag-Seiten nicht erneut einlesen
        dirs[:] = [
            d for d in dirs
            if d not in [".git", "tags"]
        ]

        for filename in files:

            if not filename.endswith(".md"):
                continue

            if filename in [
                "index.md",
                "aktuelles-tags.md"
            ]:
                continue

            file_path = os.path.join(root, filename)

            for tag in get_tags_from_file(file_path):

                key = tag.casefold()

                if key not in all_tags:
                    all_tags[key] = tag

    return [
        all_tags[key]
        for key in sorted(all_tags.keys())
    ]


# ============================================================
# ALLE BEITRÄGE FÜR EINEN TAG FINDEN
# ============================================================

def collect_tagged_pages(tag):

    pages = []

    target = tag.casefold()

    for root, dirs, files in os.walk(docs_dir):

        dirs[:] = [
            d for d in dirs
            if d not in [".git", "tags"]
        ]

        for filename in files:

            if not filename.endswith(".md"):
                continue

            if filename in [
                "index.md",
                "aktuelles-tags.md"
            ]:
                continue

            file_path = os.path.join(root, filename)

            file_tags = get_tags_from_file(file_path)

            if any(
                t.casefold() == target
                for t in file_tags
            ):

                title, _ = parse_markdown_file(
                    file_path
                )

                if not title:
                    title = os.path.splitext(filename)[0]

                relative_path = os.path.relpath(
                    file_path,
                    docs_dir
                ).replace(os.sep, "/")

                pages.append({
                    "title": title,
                    "path": relative_path
                })

    pages.sort(
        key=lambda x: x["title"].casefold()
    )

    return pages


# ============================================================
# TAG-SEITEN ERZEUGEN
# ============================================================

def create_tag_pages():

    os.makedirs(tags_dir, exist_ok=True)

    tags = collect_all_tags()

    # Alte automatisch erzeugte Tag-Seiten löschen
    for filename in os.listdir(tags_dir):

        path = os.path.join(
            tags_dir,
            filename
        )

        if os.path.isfile(path) and filename.endswith(".md"):
            os.remove(path)

    for tag in tags:

        slug = slugify_tag(tag)

        if not slug:
            continue

        tag_file = os.path.join(
            tags_dir,
            f"{slug}.md"
        )

        pages = collect_tagged_pages(tag)

        content = f"# {tag}\n\n"

        content += (
            f"Beiträge zum Thema **{tag}**.\n\n"
        )

        if pages:

            content += "## Beiträge\n\n"

            for page in pages:

                # Relativer Link von /tags/<tag>.md
                # zur eigentlichen Seite
                target_path = page["path"]

                target_parts = target_path.split("/")

                depth = len(target_parts) - 1

                prefix = "../" * depth

                link = prefix + target_path.split("/")[-1]

                content += (
                    f"- [{page['title']}]({link})\n"
                )

        else:
            content += "Keine Beiträge gefunden.\n"

        with open(
            tag_file,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(content)

    return tags


# ============================================================
# TAG-ÜBERSICHT ERZEUGEN
# ============================================================

def create_tags_overview(tags):

    tags_path = os.path.join(
        aktuelles_dir,
        "aktuelles-tags.md"
    )

    content = """# Beiträge nach Themen

Hier findest du alle Beiträge nach Themen sortiert.

Klicke auf ein Thema, um alle Beiträge mit diesem Tag anzuzeigen.

## Themen

"""

    if tags:

        for tag in tags:

            slug = slugify_tag(tag)

            content += (
                f"- [{tag}](../tags/{slug}.md)\n"
            )

    else:

        content += "Noch keine Tags vorhanden.\n"

    with open(
        tags_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(content)


# ============================================================
# AKTUELLES EINLESEN
# ============================================================

if os.path.exists(aktuelles_dir):

    all_files = [
        f
        for f in os.listdir(aktuelles_dir)
        if (
            f.endswith(".md")
            and f != "index.md"
            and f != "aktuelles-tags.md"
        )
    ]

    date_files = []
    number_files = []
    other_files = []

    for filename in all_files:

        base_name = os.path.splitext(filename)[0]

        if re.match(
            r"^\d{4}-\d{2}-\d{2}$",
            base_name
        ):
            date_files.append(filename)

        elif re.match(
            r"^\d+$",
            base_name
        ):
            number_files.append(filename)

        else:
            other_files.append(filename)

    date_files.sort(reverse=False)

    number_files.sort(
        key=lambda x: int(
            os.path.splitext(x)[0]
        )
    )

    other_files.sort()

    sorted_files = (
        date_files
        + number_files
        + other_files
    )

    for filename in sorted_files:

        file_path = os.path.join(
            aktuelles_dir,
            filename
        )

        base_name = os.path.splitext(filename)[0]

        title, teaser = parse_markdown_file(
            file_path
        )

        if not title:

            title = (
                base_name
                .replace("-", " ")
                .capitalize()
            )

        # Datum
        date_match = re.match(
            r"(\d{4})-(\d{2})-(\d{2})",
            base_name
        )

        if date_match:

            year, month, day = date_match.groups()

            formatted_date = (
                f"{day}.{month}.{year}"
            )

        else:
            formatted_date = ""

        # Bilder
        img_folder = os.path.join(
            aktuelles_dir,
            base_name
        )

        images = []

        if (
            os.path.exists(img_folder)
            and os.path.isdir(img_folder)
        ):

            valid_exts = (
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp"
            )

            images = sorted([
                img
                for img in os.listdir(img_folder)
                if img.lower().endswith(valid_exts)
            ])

        tags = get_tags_from_file(
            file_path
        )

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
    # GALERIEN AKTUALISIEREN
    # ========================================================

    for item in news_items:

        file_path = os.path.join(
            aktuelles_dir,
            item["filename"]
        )

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as f:

            content = f.read()

        marker = "\n\n## Bilder zum Beitrag\n"

        if marker in content:

            content = content.split(
                marker
            )[0]

        if item["images"]:

            content += (
                "\n\n"
                "## Bilder zum Beitrag\n\n"
            )

            content += (
                '<div class="gallery" markdown>\n\n'
            )

            for img in item["images"]:

                content += (
                    f'<a class="glightbox" '
                    f'href="{img}">'
                    f'<img src="{img}" '
                    f'width="300" '
                    f'style="border-radius: 8px; '
                    f'margin: 8px;" /></a>\n'
                )

            content += "\n</div>\n"

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(content)


    # ========================================================
    # AKTUELLES INDEX
    # ========================================================

    index_path = os.path.join(
        aktuelles_dir,
        "index.md"
    )

    existing_index_content = ""

    if os.path.exists(index_path):

        with open(
            index_path,
            "r",
            encoding="utf-8"
        ) as f:

            existing_index_content = f.read()

        if "\n\n## Beiträge\n" in existing_index_content:

            existing_index_content = (
                existing_index_content.split(
                    "\n\n## Beiträge\n"
                )[0]
            )

    if existing_index_content.strip():

        index_content = (
            existing_index_content.strip()
        )

    else:

        index_content = (
            "# Aktuelles aus der Schachabteilung\n\n"
            "Hier findest du alle Neuigkeiten."
        )

    index_content += "\n\n## Beiträge\n\n"

    for item in news_items:

        date_text = (
            f"**[{item['date']}]** "
            if item["date"]
            else ""
        )

        index_content += (
            f"* {date_text}"
            f"**[{item['title']}]"
            f"({item['filename']})**"
            f" – {item['teaser']} "
            f"[weiterlesen]({item['filename']})\n"
        )

    with open(
        index_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(index_content)


# ============================================================
# TAGS ERZEUGEN
# ============================================================

all_tags = create_tag_pages()

create_tags_overview(all_tags)


# ============================================================
# NAVIGATION SCANNEN
# ============================================================

def scan_folder(path):

    items = []

    entries = sorted(
        os.listdir(path),
        reverse=True
    )

    for entry in entries:

        full_path = os.path.join(
            path,
            entry
        )

        rel_path = os.path.relpath(
            full_path,
            docs_dir
        )

        # --------------------------------------------
        # ORDNER
        # --------------------------------------------

        if os.path.isdir(full_path):

            # Bildordner von Aktuelles überspringen
            if any(
                item["base_name"] == entry
                for item in news_items
            ):
                continue

            # Generierten tags-Ordner nicht automatisch
            # in die Navigation aufnehmen
            if entry == "tags":
                continue

            sub_items = scan_folder(
                full_path
            )

            if sub_items:

                sub_index = os.path.join(
                    full_path,
                    "index.md"
                )

                folder_title = ""

                if os.path.exists(sub_index):

                    folder_title, _ = (
                        parse_markdown_file(
                            sub_index
                        )
                    )

                if not folder_title:

                    folder_title = (
                        entry
                        .replace("_", " ")
                        .replace("-", " ")
                        .capitalize()
                    )

                sub_index_rel = (
                    os.path.relpath(
                        sub_index,
                        docs_dir
                    ).replace(os.sep, "/")
                )

                sub_nav_list = [
                    {
                        "Übersicht":
                        sub_index_rel
                    }
                ] + [
                    i
                    for i in sub_items
                    if list(i.values())[0]
                    != sub_index_rel
                ]

                items.append({
                    folder_title:
                    sub_nav_list
                })

        # --------------------------------------------
        # MARKDOWN
        # --------------------------------------------

        elif entry.endswith(".md"):

            if entry in [
                "index.md",
                "aktuelles-tags.md"
            ]:
                continue

            name_without_ext = (
                os.path.splitext(entry)[0]
            )

            default_title = (
                name_without_ext
                .replace("-", " ")
                .capitalize()
            )

            title, _ = parse_markdown_file(
                full_path
            )

            if not title:
                title = default_title

            items.append({
                title:
                rel_path.replace(os.sep, "/")
            })

    return items


# ============================================================
# STARTSEITE
# ============================================================

start_index = os.path.join(
    docs_dir,
    "index.md"
)

if os.path.exists(start_index):

    start_title, _ = (
        parse_markdown_file(
            start_index
        )
    )

    if not start_title:
        start_title = "Startseite"

    nav.append({
        start_title:
        "index.md"
    })


# ============================================================
# AKTUELLES
# ============================================================

if os.path.exists(aktuelles_dir):

    aktuelles_items = scan_folder(
        aktuelles_dir
    )

    akt_index = os.path.join(
        aktuelles_dir,
        "index.md"
    )

    akt_title, _ = (
        parse_markdown_file(
            akt_index
        )
    )

    if not akt_title:
        akt_title = "Aktuelles"

    aktuelles_nav_list = [
        {
            "Übersicht":
            "aktuelles/index.md"
        },
        {
            "Nach Themen":
            "aktuelles/aktuelles-tags.md"
        }
    ] + [
        i
        for i in aktuelles_items
        if list(i.values())[0]
        not in [
            "aktuelles/index.md",
            "aktuelles/aktuelles-tags.md"
        ]
    ]

    nav.append({
        akt_title:
        aktuelles_nav_list
    })


# ============================================================
# RESTLICHE ORDNER
# ============================================================

for entry in sorted(
    os.listdir(docs_dir)
):

    full_path = os.path.join(
        docs_dir,
        entry
    )

    if (
        os.path.isdir(full_path)
        and entry not in [
            "aktuelles",
            "tags"
        ]
    ):

        sub_items = scan_folder(
            full_path
        )

        if sub_items:

            sub_index = os.path.join(
                full_path,
                "index.md"
            )

            folder_title = ""

            sub_index_rel = (
                f"{entry}/index.md"
            )

            if os.path.exists(
                sub_index
            ):

                folder_title, _ = (
                    parse_markdown_file(
                        sub_index
                    )
                )

            if not folder_title:

                folder_title = (
                    entry
                    .replace("_", " ")
                    .replace("-", " ")
                    .capi
