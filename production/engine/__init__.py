"""SIGNIT signal-intel engine (in-process Python, offline). Phases 2-6 land here."""
from engine.demod import (
    DemodError,
    DemodResult,
    demod_log_lines,
    demodulate_preview,
    estimate_carrier,
    estimate_symbol_rate,
    sync_search,
)
from engine.estimators import (
    EstimateResult,
    EstimatorError,
    analyze_preview,
    estimator_log_lines,
    to_demo_dict,
)
from engine.fec import (
    FECResult,
    RSCodec,
    RSDecodeError,
    assess_bits,
    backend_status,
    conv_encode,
    fec_log_lines,
    viterbi_decode,
)
from engine.ingest import IngestError, IngestResult, ingest_file, log_lines, raw_view

__all__ = [
    "DemodError",
    "DemodResult",
    "EstimateResult",
    "EstimatorError",
    "FECResult",
    "IngestError",
    "IngestResult",
    "RSCodec",
    "RSDecodeError",
    "analyze_preview",
    "assess_bits",
    "backend_status",
    "conv_encode",
    "demod_log_lines",
    "demodulate_preview",
    "estimate_carrier",
    "estimate_symbol_rate",
    "estimator_log_lines",
    "fec_log_lines",
    "ingest_file",
    "log_lines",
    "raw_view",
    "sync_search",
    "to_demo_dict",
    "viterbi_decode",
]
