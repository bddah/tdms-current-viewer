from __future__ import annotations

from pathlib import Path

import numpy as np
import pyqtgraph.exporters


class Exporter:
    def to_csv(
        self,
        x: np.ndarray,
        y: np.ndarray,
        x_label: str,
        y_label: str,
        output_path: Path,
    ) -> None:
        """Write two-column CSV with header."""
        data = np.column_stack((np.asarray(x), np.asarray(y)))
        np.savetxt(output_path, data, delimiter=",", header=f"{x_label},{y_label}", comments="", fmt="%s")

    def save_plot_png(self, plot_widget, output_path: Path) -> None:
        """Export the pyqtgraph PlotItem to PNG."""
        target = plot_widget.plot_item if hasattr(plot_widget, "plot_item") else plot_widget
        exporter = pyqtgraph.exporters.ImageExporter(target)
        exporter.export(str(output_path))
