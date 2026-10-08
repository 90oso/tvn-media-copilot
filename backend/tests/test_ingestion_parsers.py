import json
from pathlib import Path

import pandas as pd

from app.ingestion.gdelt import _parse_seen_date, _iter_windows


def test_gdelt_seen_date_parser():
    assert _parse_seen_date("20260601T140000Z") == "2026-06-01T14:00:00Z"


def test_gdelt_windows_cover_requested_period_without_overlap():
    windows = list(_iter_windows("2026-06-01", "2026-06-10", 7))
    assert len(windows) == 2
    assert windows[0][0] < windows[0][1]
    assert windows[0][1] < windows[1][0]
