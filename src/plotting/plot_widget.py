from __future__ import annotations

import pyqtgraph as pg
import pyqtgraph.exporters


class TdmsPlotWidget(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.plot_item = self.addPlot(row=0, col=0)
        self.plot_item.setMenuEnabled(True)
        self.plot_item.showGrid(x=True, y=True, alpha=0.3)
        self._grid_visible = True
        self._legend_visible = True
        self._legend = None
        self._traces: list[dict] = []
        self._x_label = ""
        self._y_label = ""
        self._colors = [
            "#4C78A8",
            "#F58518",
            "#54A24B",
            "#E45756",
            "#72B7B2",
            "#B279A2",
            "#FF9DA6",
            "#9D755D",
        ]
        self._rebuild_plot()

    def _rebuild_plot(self) -> None:
        self.plot_item.clear()
        if self._legend is not None:
            scene = self._legend.scene()
            if scene is not None:
                scene.removeItem(self._legend)
            self._legend = None
        if self._legend_visible:
            self._legend = self.plot_item.addLegend()
        self.plot_item.showGrid(x=self._grid_visible, y=self._grid_visible, alpha=0.3)
        if self._x_label:
            self.plot_item.setLabel("bottom", self._x_label)
        if self._y_label:
            self.plot_item.setLabel("left", self._y_label)
        for trace in self._traces:
            self.plot_item.plot(
                trace["x"],
                trace["y"],
                name=trace["name"],
                pen=pg.mkPen(trace["color"], width=2),
            )
        if not self._traces:
            self.plot_item.setLabel("bottom", "")
            self.plot_item.setLabel("left", "")

    def plot_channel(self, x, y, x_label, y_label, name):
        self._x_label = x_label
        self._y_label = y_label
        self._traces = [
            {"x": x, "y": y, "name": name, "color": self._colors[0]}
        ]
        self._rebuild_plot()

    def add_channel(self, x, y, name):
        color = self._colors[len(self._traces) % len(self._colors)]
        self._traces.append({"x": x, "y": y, "name": name, "color": color})
        self._rebuild_plot()

    def clear_plot(self):
        self._traces = []
        self._x_label = ""
        self._y_label = ""
        self._rebuild_plot()

    def toggle_legend(self):
        self._legend_visible = not self._legend_visible
        self._rebuild_plot()

    def toggle_grid(self):
        self._grid_visible = not self._grid_visible
        self.plot_item.showGrid(x=self._grid_visible, y=self._grid_visible, alpha=0.3)

    def export_png(self, path):
        exporter = pg.exporters.ImageExporter(self.plot_item)
        exporter.export(str(path))
