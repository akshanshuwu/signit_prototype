"""pyqtgraph plots — Spectrum / Waterfall / Constellation / Correlation (web parity).

Web specs: dark #020617 bg, cyan #22d3ee spectrum+constellation, Viridis
waterfall, violet #a78bfa correlation + amber #f59e0b dashed peak, grid #1e293b.
"""
import numpy as np
import pyqtgraph as pg

BG = "#020617"
CYAN = "#22d3ee"
GRID = "#1e293b"
AXIS = "#94a3b8"

pg.setConfigOptions(antialias=True)


def _style(plot: pg.PlotItem) -> None:
    # Background is set on the PlotWidget itself (constructor background=BG);
    # PlotItem has no setBackground API.
    plot.showGrid(x=True, y=True, alpha=0.35)
    for axis in ("bottom", "left"):
        ax = plot.getAxis(axis)
        ax.setPen(pg.mkPen(GRID))
        ax.setTextPen(pg.mkPen(AXIS))


class SpectrumPlotWidget(pg.PlotWidget):
    """PSD line: x freq kHz, y dB (512 pts)."""

    def __init__(self, parent=None):
        super().__init__(parent, background=BG)
        self.setObjectName("spectrumPlot")
        self._plot = self.getPlotItem()
        _style(self._plot)
        self._plot.setLabels(bottom="Freq (kHz)", left="Mag (dB)")
        self._curve = self._plot.plot(pen=pg.mkPen(CYAN, width=1.5))

    def set_data(self, freqs: list[float], mags_db: list[float]) -> None:
        self._curve.setData(np.asarray(freqs) / 1000.0, np.asarray(mags_db))


class WaterfallPlotWidget(pg.PlotWidget):
    """Heatmap: x time (s), y freq kHz, z dB (128 freq x 64 time)."""

    def __init__(self, parent=None):
        super().__init__(parent, background=BG)
        self.setObjectName("waterfallPlot")
        self._plot = self.getPlotItem()
        _style(self._plot)
        self._plot.setLabels(bottom="Time (s)", left="Freq (kHz)")
        self._img = pg.ImageItem()
        # Viridis LUT (pyqtgraph ships viridis via colormap)
        cmap = pg.colormap.get("viridis")
        self._img.setLookupTable(cmap.getLookupTable())
        self._plot.addItem(self._img)

    def set_data(self, times: list[float], freqs: list[float], z_db: list[list[float]]) -> None:
        z = np.asarray(z_db, dtype=float)  # (128 freq, 64 time)
        t = np.asarray(times, dtype=float)
        f = np.asarray(freqs, dtype=float) / 1000.0
        # ImageItem: array indexed [row=x, col=y]; transpose so x=time, y=freq.
        self._img.setImage(z.T, autoLevels=True)
        dt = (t[-1] - t[0]) / max(len(t) - 1, 1) if len(t) > 1 else 1.0
        df = (f[-1] - f[0]) / max(len(f) - 1, 1) if len(f) > 1 else 1.0
        self._img.setRect(t[0], f[0], dt * len(t), df * len(f))
        self._plot.setXRange(t[0], t[-1])
        self._plot.setYRange(f[0], f[-1])


class ConstellationPlotWidget(pg.PlotWidget):
    """Scattergl-equivalent: I/Q markers, equal aspect (<=2000 pts)."""

    def __init__(self, parent=None):
        super().__init__(parent, background=BG)
        self.setObjectName("constellationPlot")
        self._plot = self.getPlotItem()
        _style(self._plot)
        self._plot.setLabels(bottom="I", left="Q")
        self._plot.setAspectLocked(True, ratio=1.0)
        self._scatter = pg.ScatterPlotItem(
            pen=None, brush=pg.mkBrush(34, 211, 238, 150), size=4
        )
        self._plot.addItem(self._scatter)

    def set_data(self, i: list[float], q: list[float]) -> None:
        self._scatter.setData(np.asarray(i), np.asarray(q))


class CorrPeakWidget(pg.PlotWidget):
    """Sync correlation: violet line + amber dashed marker at peak lag."""

    def __init__(self, parent=None):
        super().__init__(parent, background=BG)
        self.setObjectName("corrPlot")
        self._plot = self.getPlotItem()
        _style(self._plot)
        self._plot.setLabels(bottom="Lag", left="Corr")
        self._curve = self._plot.plot(pen=pg.mkPen("#a78bfa", width=1.5))
        self._marker = pg.InfiniteLine(
            angle=90, pen=pg.mkPen("#f59e0b", width=1, style=pg.QtCore.Qt.DashLine)
        )
        self._plot.addItem(self._marker)

    def set_data(self, lags: list[int], vals: list[float], peak_lag: int) -> None:
        self._curve.setData(np.asarray(lags), np.asarray(vals))
        self._marker.setValue(peak_lag)
