from build.aktuelles import build_aktuelles
from build.tags import build_tags
from build.navigation import build_navigation
from build.homebutton import build_homebutton
from build.termine import build_termine


def main():
    build_aktuelles()
    build_tags()
    build_termine()
    build_navigation()
    build_homebutton()


if __name__ == "__main__":
    main()
