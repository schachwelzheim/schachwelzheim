from build.aktuelles import build_aktuelles
from build.tags import build_tags
from build.navigation import build_navigation
from build.homebutton import build_homebuttons


def main():
    build_aktuelles()
    build_tags()
    build_navigation()
    insert_homebuttons()


if __name__ == "__main__":
    main()
