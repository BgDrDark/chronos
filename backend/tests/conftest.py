"""Pytest bootstrap for the Chronos backend test suite.

The tests import the application as the top-level ``backend`` package, so the
repository root must be on ``sys.path`` even when pytest is started from
``backend/`` (where ``backend/`` itself, not its parent, is the rootdir entry).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Known broken import (Phase 5, Task 5.7): BULGARIAN_LABOR_CONSTANTS is defined
# locally in test_payroll_compliance.py, not exported by backend.crud. Keep this
# module out of the Phase 0 baseline until the import is fixed.
collect_ignore = ["test_payroll_2month_compliance.py"]
