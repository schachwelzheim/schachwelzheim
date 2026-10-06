from build.aktuelles import build_aktuelles
from build.tags import build_tags
from build.navigation import build_navigation
from build.homebutton import insert_home_buttons


def main():
    build_aktuelles()
    build_tags()
    build_navigation()


if __name__ == "__main__":
    main()
