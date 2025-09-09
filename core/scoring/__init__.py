"""Lightweight scoring engine accessors.

This module exposes scoring helpers used by the test-suite.  Only pure
functions that avoid network and disk I/O should be re-exported here.
"""

from core.spice.v22 import build_spice_report_v22
from core.engines.updc import UPDCResult, updc_transform

__all__ = ["build_spice_report_v22", "UPDCResult", "updc_transform"]
