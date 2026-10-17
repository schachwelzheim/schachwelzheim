import os
import yaml

from .markdown import (
    get_title,
    read_file,
)


DOCS_DIR = "docs"

IGNORED_FILES = {
    "index.md",
    "aktuelles-tags.md",
}

# FESTE REIHENFOLGE FÜR DEN ORDNER verein/termine (EXCEL-STRUKTUR)
TERMINE_ORDER = [
    "index.md",            # 1. Übersicht
    "kalender-matrix.md",   # 2. Matrix
    "tsf-welzheim-1",      # 3. TSF Welzheim I
    "spraitbach",          # 4. Spraitbach/TSF Welzheim 2
    "blitz",               # 5. Blitz
    "schnell",             # 6. Schnell
    "normal",              # 7. Normal
    "theorie",             # 8. Theorie
    "jugend",              # 9. Jugendschach
    "turnier",             # 10. Turniere Aktive
    "ferien",              # 11. Ferien
]


def get_page_title(path):
    content = read_file(path)
    title = get_title(content)

    if title:
        return title

    filename = os.path.splitext(
        os.path.basename(path)
    )[0]

    return filename.replace("-", " ").capitalize()


def is_verein_termine_path(path):
    """Prüft, ob der angegebene Pfad genau zum Ordner 'verein/termine' gehört."""
    norm_path = os.path.normpath(path).replace(os.sep, "/")
    return norm_path.endswith("verein/termine")


def sort_termine_items(items):
    """Sortiert die Navigations-Einträge des Ordners 'verein/termine' strikt nach TERMINE_ORDER."""
    def get_sort_key(item):
        val = list(item.values())[0]  # Pfad z. B. 'verein/termine/blitz.md'
        if isinstance(val, list):
            val = str(val)
        
        val_lower = str(val).lower()
        
        for idx, key in enumerate(TERMINE_ORDER):
            if key in val_lower:
                return idx
        return 999

    return sorted(items, key=get_sort_key)


def scan_folder(path):
    items = []

    for entry in sorted(os.listdir(path)):
        full_path = os.path.join(path, entry)

        if os.path.isdir(full_path):
            if entry == "themen":
                continue

            sub_items = scan_folder(full_path)

            index_path = os.path.join(
                full_path,
                "index.md"
            )

            relative_index = os.path.relpath(
                index_path,
                DOCS_DIR
            ).replace(os.sep, "/")

            if not os.path.exists(index_path) and not sub_items:
                continue

            if os.path.exists(index_path):
                folder_title = get_page_title(
                    index_path
                )
            else:
                folder_title = (
                    entry
                    .replace("_", " ")
                    .replace("-", " ")
                    .capitalize()
                )

            children = []

            if os.path.exists(index_path):
                children.append({
                    "Übersicht": relative_index
                })

            children.extend(sub_items)

            # Prüfen, ob dieser Unterordner exakt 'verein/termine' ist
            if is_verein_termine_path(full_path):
                children = sort_termine_items(children)

            items.append({
                folder_title: children
            })

        elif entry.endswith(".md"):
            if entry in IGNORED_FILES:
                continue

            relative_path = os.path.relpath(
                full_path,
                DOCS_DIR
            ).replace(os.sep, "/")

            items.append({
                get_page_title(full_path): relative_path
            })

    # Falls der aktuelle Ordner 'verein/termine' ist, dessen Einträge sortieren
    if is_verein_termine_path(path):
        items = sort_termine_items(items)

    return items


def build_navigation():
    config_path = "mkdocs.yml"

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    nav = []

    start_page = os.path.join(
        DOCS_DIR,
        "index.md"
    )

    if os.path.exists(start_page):
        nav.append({
            get_page_title(start_page): "index.md"
        })

    aktuelles = os.path.join(
        DOCS_DIR,
        "aktuelles"
    )

    if os.path.isdir(aktuelles):
        aktuelles_index = os.path.join(
            aktuelles,
            "index.md"
        )

        aktuelles_nav = []

        if os.path.exists(aktuelles_index):
            aktuelles_nav.append({
                "Übersicht": "aktuelles/index.md"
            })

        tags_page = os.path.join(
            aktuelles,
            "aktuelles-tags.md"
        )

        if os.path.exists(tags_page):
            aktuelles_nav.append({
                "Nach Themen": "aktuelles/aktuelles-tags.md"
            })

        for item in scan_folder(aktuelles):
            path = list(item.values())[0]

            if path not in {
                "aktuelles/index.md",
                "aktuelles/aktuelles-tags.md",
            }:
                aktuelles_nav.append(item)

        if aktuelles_nav:
            nav.append({
                get_page_title(aktuelles_index):
                    aktuelles_nav
            })

    for entry in sorted(os.listdir(DOCS_DIR)):
        if entry in {
            "aktuelles",
            "themen",
        }:
            continue

        full_path = os.path.join(
            DOCS_DIR,
            entry
        )

        if not os.path.isdir(full_path):
            continue

        sub_items = scan_folder(full_path)

        index_path = os.path.join(
            full_path,
            "index.md"
        )

        if not os.path.exists(index_path) and not sub_items:
            continue

        if os.path.exists(index_path):
            title = get_page_title(index_path)
            relative_index = os.path.relpath(
                index_path,
                DOCS_DIR
            ).replace(os.sep, "/")
            
            folder_nav = [{"Übersicht": relative_index}]
            folder_nav.extend(sub_items)
        else:
            title = (
                entry
                .replace("_", " ")
                .replace("-", " ")
                .capitalize()
            )
            folder_nav = sub_items

        # Sortierung gezielt anwenden, wenn der Ordner zu verein/termine gehört
        if is_verein_termine_path(full_path):
            folder_nav = sort_termine_items(folder_nav)

        nav.append({
            title: folder_nav
        })

    config["nav"] = nav

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(
            config,
            f,
            allow_unicode=True,
            sort_keys=False
                )
        
