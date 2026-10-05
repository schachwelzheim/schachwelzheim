import os
import re
import yaml


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def parse_frontmatter(content):
    if not content.startswith("---"):
        return {}, content

    match = re.match(
        r"^---\s*\n(.*?)\n---\s*\n?",
        content,
        re.DOTALL
    )

    if not match:
        return {}, content

    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        data = {}

    body = content[match.end():]
    return data, body


def get_title(content):
    frontmatter, body = parse_frontmatter(content)

    match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    if match:
        return match.group(1).strip()

    match = re.search(
        r"<h1[^>]*>(.*?)</h1>",
        body,
        re.IGNORECASE | re.DOTALL
    )

    if match:
        title = match.group(1)
        title = re.sub(r"<br\s*/?>", " ", title, flags=re.IGNORECASE)
        title = re.sub(r"<[^>]+>", "", title)
        return title.strip()

    return ""


def get_tags(content):
    frontmatter, _ = parse_frontmatter(content)

    tags = frontmatter.get("tags", [])

    if isinstance(tags, str):
        return [tags]

    if isinstance(tags, list):
        return [str(tag).strip() for tag in tags if str(tag).strip()]

    return []


def get_teaser(content, words_count=10):
    _, body = parse_frontmatter(content)

    title = get_title(content)

    lines = body.splitlines()
    words = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        if re.match(r"^\d+\.", line):
            continue

        clean = re.sub(r"<[^>]+>", " ", line)
        clean = re.sub(r"\s+", " ", clean)

        found = re.findall(r"\b\w+\b", clean)
        words.extend(found)

        if len(words) >= words_count:
            break

    if not words:
        return "Keine Vorschau verfügbar..."

    teaser = " ".join(words[:words_count])

    if len(words) > words_count:
        teaser += "..."

    return teaser
