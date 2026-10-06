import os
import re
from build.markdown import read_file, write_file

def build_homebutton(docs_dir="docs"):
    """Fügt automatisch auf allen Unterseiten oben rechts einen Home-Button ein (ohne Duplikate)."""
    button_html = """<div style="float: right; margin-top: -10px; margin-bottom: 15px; z-index: 10;">
  <a href="https://schachwelzheim.github.io/schachwelzheim/" title="Startseite" style="text-decoration: none;">
    <img src="https://raw.githubusercontent.com/feathericons/feather/master/icons/home.svg" width="26" height="26" alt="Startseite" style="vertical-align: middle;" />
  </a>
</div>

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
            
            # 1. Zuerst eventuell bereits vorhandene Home-Button-Blöcke komplett entfernen,
            # damit sie bei erneuten Durchläufen nicht gestapelt werden.
            # Wir suchen nach dem spezifischen DIV mit dem Home-Icon.
            content = re.sub(
                r'<div style="float: right;[^>]*>.*?<img[^>]*home\.svg[^>]*>.*?</div>\s*',
                '',
                content,
                flags=re.DOTALL
            )
            
            # 2. Nach dem Frontmatter einfügen, falls vorhanden
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    new_content = f"---{parts[1]}---\n\n{button_html}{parts[2]}"
                else:
                    new_content = button_html + content
            else:
                new_content = button_html + content
                
            write_file(file_path, new_content)
            
