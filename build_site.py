import os
import yaml
import re


# ============================================================
# GRUNDEINSTELLUNGEN
# ============================================================

docs_dir = "docs"
aktuelles_dir = os.path.join(docs_dir, "aktuelles")

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

            # Frontmatter überspringen
            if clean_line == "---":
                in_frontmatter = not in_frontmatter
                continue

            if in_frontmatter:
                continue

            # Titel aus Markdown-H1
            if not title and clean_line.startswith("# "):
                title = clean_line[2:].strip()
                continue

            # Titel aus HTML-H1
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

            # Teasertext
            if (
                title
                and clean_line
                and not clean_line.startswith("#")
                and not clean_line.startswith("---")
            ):
                # Nummerierte Listen nicht als Teaser verwenden
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
# TAGS AUS MARKDOWN-FRONTMATTER LESEN
# ============================================================

def get_tags_from_file(file_path):
    """
    Liest Tags aus dem YAML-Frontmatter einer Markdown-Datei.

    Unterstützte Schreibweisen:

    tags:
      - Turnier
      - Jugend

    oder:

    tags: [Turnier, Jugend]
    """

    tags = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Frontmatter muss am Dateianfang stehen
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
            # Einzelner Tag
            tags = [raw_tags]

        elif isinstance(raw_tags, list):
            tags = raw_tags

        # Nur sinnvolle Strings übernehmen
        cleaned_tags = []

        for tag in tags:
            if tag is None:
                continue

            tag = str(tag).strip()

            if tag:
                cleaned_tags.append(tag)

        return cleaned_tags

    except Exception:
        return []


# ============================================================
# TAGS AUS ALLEN MARKDOWN-DATEIEN SAMMELN
# ============================================================

def collect_all_tags():
    """
    Durchsucht den kompletten docs-Ordner nach Markdown-Dateien
    und sammelt alle verwendeten Tags.
    """

    all_tags = {}

    for root, dirs, files in os.walk(docs_dir):

        # Verzeichnisse, die nicht durchsucht werden sollen
        dirs[:] = [
            d for d in dirs
            if d != ".git"
        ]

        for filename in files:

            if not filename.endswith(".md"):
                continue

            # Technische Übersichtsseiten nicht berücksichtigen
            if filename in [
                "index.md",
                "aktuelles-tags.md"
            ]:
                continue

            file_path = os.path.join(root, filename)

            tags = get_tags_from_file(file_path)

            for tag in tags:

                # Einheitliche Schreibweise für die Sortierung
                normalized = tag.casefold()

                if normalized not in all_tags:
                    all_tags[normalized] = tag

    # Alphabetisch sortieren
    return [
        all_tags[key]
        for key in sorted(all_tags.keys())
    ]


# ============================================================
# TAG-SEITE ERZEUGEN
# ============================================================

def create_tags_page():
    """
    Erzeugt automatisch aktuelles/aktuelles-tags.md.

    Die eigentliche Filterung übernimmt das MkDocs-Material
    Tags-Plugin.
    """

    tags = collect_all_tags()

    tags_path = os.path.join(
        aktuelles_dir,
        "aktuelles-tags.md"
    )

    content = """# Beiträge nach Themen

Hier findest du die Beiträge nach Themen sortiert.

Klicke auf ein Thema, um alle Beiträge mit diesem Tag anzuzeigen.

## Themen

"""

    if tags:

        for tag in tags:
            content += f"- [{tag}](../tags/#/default/{tag.lower()})\n"

    else:
        content += "Noch keine Tags vorhanden.\n"

    with open(tags_path, "w", encoding="utf-8") as f:
        f.write(content)


# ============================================================
# AKTUELLES EINLESEN
# ============================================================

if os.path.exists(aktuelles_dir):

    all_files = [
        f
        for f in os.listdir(aktuelles_dir)
        if f.endswith(".md")
        and f != "index.md"
        and f != "aktuelles-tags.md"
    ]

    # Dateien nach Namensschema aufteilen
    date_files = []
    number_files = []
    other_files = []

    for f in all_files:

        base_name = os.path.splitext(f)[0]

        if re.match(r"^\d{4}-\d{2}-\d{2}$", base_name):
            date_files.append(f)

        elif re.match(r"^\d+$", base_name):
            number_files.append(f)

        else:
            other_files.append(f)

    # Sortierung
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

    # Beiträge einlesen
    for filename in sorted_files:

        file_path = os.path.join(
            aktuelles_dir,
            filename
        )

        base_name = os.path.splitext(filename)[0]

        default_title = base_name

        title, teaser = parse_markdown_file(
            file_path
        )

        if not title:
            title = (
                default_title
                .replace("-", " ")
                .capitalize()
            )

        # Datum aus Dateinamen
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

        # Bilderordner
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

        # Tags
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
    # GALERIEN IN BEITRÄGEN AKTUALISIEREN
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

        gallery_marker = (
            "\n\n## Bilder zum Beitrag\n"
        )

        if gallery_marker in content:

            content = content.split(
                gallery_marker
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
                    f'margin: 8px;" />'
                    f'</a>\n'
                )

            content += "\n</div>\n"

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(content)


    # ========================================================
    # AKTUELLES INDEX ERZEUGEN
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

        d_str = (
            f"**[{item['date']}]** "
            if item["date"]
            else ""
        )

        index_content += (
            f"* {d_str}"
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
# TAG-SEITE ERSTELLEN
# ============================================================

if os.path.exists(aktuelles_dir):

    create_tags_page()


# ============================================================
# RESTLICHE ORDNER SCANNEN
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

            # Beitrags-Bildordner überspringen
            if any(
                item["base_name"] == entry
                for item in news_items
            ):
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
        # MARKDOWN-DATEIEN
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
# AKTUELLES NAVIGATION
# ============================================================

aktuelles_items = scan_folder(
    aktuelles_dir
)

if os.path.exists(aktuelles_dir):

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
# RESTLICHE ORDNER IN DIE NAVIGATION
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
        and entry != "aktuelles"
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
                    .capitalize()
                )

            folder_nav_list = [
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

            nav.append({
                folder_title:
                folder_nav_list
            })


# ============================================================
# MKDOCS.YML AKTUALISIEREN
# ============================================================

with open(
    "mkdocs.yml",
    "r",
    encoding="utf-8"
) as f:

    config = yaml.safe_load(f)


config["nav"] = nav


with open(
    "mkdocs.yml",
    "w",
    encoding="utf-8"
) as f:

    yaml.dump(
        config,
        f,
        allow_unicode=True,
        sort_keys=False
    )


print("Build-Skript erfolgreich ausgeführt.")

print(
    f"{len(news_items)} Beiträge in 'Aktuelles' gefunden."
)

print(
    f"{len(collect_all_tags())} Tags gefunden."
    )
