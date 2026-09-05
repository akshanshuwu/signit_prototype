"""SIGNIT signal-intel engine (in-process Python, offline). Phases 2-6 land here."""
from engine.ingest import IngestError, IngestResult, ingest_file, log_lines, raw_view

__all__ = ["IngestError", "IngestResult", "ingest_file", "log_lines", "raw_view"]
