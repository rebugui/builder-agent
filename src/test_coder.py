import sys
from pathlib import Path
# Add project root and intelligence module to sys.path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parents[1]
intelligence_dir = project_root / 'modules' / 'intelligence'

for path in [str(project_root), str(intelligence_dir)]:
    if path not in sys.path:
        sys.path.append(path)

from coder import CodeGenerator

coder = CodeGenerator()
try:
    print("Generating...")
    code = coder.generate_code("Test", "Test desc")
    print("Code generated successfully.")
except Exception as e:
    import traceback
    traceback.print_exc()
