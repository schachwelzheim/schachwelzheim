import os
from build.markdown import read_file, write_file

def build_homebutton(docs_dir="docs"):
    """Fügt automatisch auf allen Unterseiten einen Home-Button ein."""
    button_html = """<p><a href="https://schachwelzheim.github.io/schachwelzheim/" title="Startseite" style="margin: 0 12px; text-decoration: none;">
  <img src="https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/homeassistant.svg" width="28" height="28" alt="Startseite" style="vertical-align: middle;" />
</a>
</p>

"""
    
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if not file.endswith(".md"):
                continue
            
            # Die Hauptseite überspringen
            if file == "index.md" and root == docs_dir:
                continue
                
            file_path = os.path.join(root, file)
            content = read_file(file_path)
            
            if "Zur Startseite" in content or "homeassistant.svg" in content:
                continue
                
            # Nach dem Frontmatter einfügen, falls vorhanden
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    new_content = f"---{parts[1]}---\n\n{button_html}{parts[2]}"
                else:
                    new_content = button_html + content
            else:
                new_content = button_html + content
                
            write_file(file_path, new_content)
            
