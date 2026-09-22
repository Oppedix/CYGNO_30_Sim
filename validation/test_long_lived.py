"""Real U238 transport with and without the supported explicit macro threshold."""
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from study.preflight import check
build = Path(sys.argv[1]).resolve()
parent = Path(tempfile.mkdtemp(prefix='long-lived-', dir=build/'validation-results'))
assert check(build, parent/'preflight', long_lived_only=True) == 0
