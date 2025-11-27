# Add import path handling at the top of each source file
import os
import sys
from pathlib import Path

# Add the Files directory to Python path for imports
file_dir = Path(__file__).parent.parent
if file_dir not in sys.path:
    sys.path.insert(0, str(file_dir))

# NOTE: Avoid importing modules here to prevent circular imports
# Import NoteExtended, NoteCode, etc. only when needed in the actual modules
# that use them
