"""Allow running with ``python -m portscope``."""
import sys

from portscope.cli import main

if __name__ == "__main__":
    sys.exit(main())
