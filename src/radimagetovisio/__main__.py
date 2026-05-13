import sys

from radimagetovisio.app import main as gui_main
from radimagetovisio.cli import main as cli_main

if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    else:
        sys.exit(gui_main())
