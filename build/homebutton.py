import os
from build.markdown import read_file, write_file

def build_homebutton(docs_dir="docs"):
    """Fügt automatisch auf allen Unterseiten einen Home-Button ein."""
    button_html = '<p><a href="https://schachwelzheim.github.io/schachwelzheim/" title="Zur Startseite" style="margin: 0 12px; text-decoration: none; display: inline-block;">
  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
</a>
</p>\n\n'
    
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if not file.endswith(".md"):
                continue
            
            # Die Hauptseite überspringen
            if file == "index.md" and root == docs_dir:
                continue
                
            file_path = os.path.join(root, file)
            content = read_file(file_path)
            
            if "Zur Startseite" in content:
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
              
