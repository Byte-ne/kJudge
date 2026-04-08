"""Allow running kjudge as: python -m kjudge"""
import sys
from kjudge.cli import main
from kjudge.setup_wizard import is_frozen, run_interactive_setup

if __name__ == "__main__":
    if is_frozen() and len(sys.argv) == 1:
        run_interactive_setup()
    else:
        main()
