"""Point the suite at an EMPTY data tree before anything imports ihlib.

The tests must see exactly what CI sees: a fresh clone, where `data/` is
git-ignored and therefore absent. Without this, a test that calls
`load_capture()` quietly reads whatever captures happen to be on the
developer's disk — which is how a green local run shipped a PR that failed in
CI on 7 Aug 2026.

Tests needing a capture build a synthetic one (see the fixture and the
DuplicateAffixNameTest / LockActionsTest helpers). None may depend on the
contents of the working tree.
"""

import os
import tempfile

os.environ.setdefault("IH_DATA_DIR", tempfile.mkdtemp(prefix="ih-tests-data-"))
