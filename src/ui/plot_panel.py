from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from plotting.plot_widget import TdmsPlotWidget


class PlotPanel(QWidget):
    plot_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.plot_widget = TdmsPlotWidget(self)

        self.x_channel_combo = QComboBox(self)
        self.average_checkbox = QCheckBox("Average", self)
        self.average_window_spin = QSpinBox(self)
        self.average_window_spin.setMinimum(1)
        self.average_window_spin.setMaximum(100000)
        self.average_window_spin.setValue(5)
        self.integrate_checkbox = QCheckBox("Integrate", self)
        self.subtract_average_checkbox = QCheckBox("Subtract average", self)
        self.plot_button = QPushButton("Plot", self)
        self.plot_button.clicked.connect(self.plot_requested.emit)

        toolbar_layout = QHBoxLayout()
        toolbar_layout.addWidget(QLabel("X Channel:", self))
        toolbar_layout.addWidget(self.x_channel_combo, 1)
        toolbar_layout.addWidget(self.average_checkbox)
        toolbar_layout.addWidget(QLabel("Window:", self))
        toolbar_layout.addWidget(self.average_window_spin)
        toolbar_layout.addWidget(self.integrate_checkbox)
        toolbar_layout.addWidget(self.subtract_average_checkbox)
        toolbar_layout.addWidget(self.plot_button)

        layout = QVBoxLayout(self)
        layout.addLayout(toolbar_layout)
        layout.addWidget(self.plot_widget, 1)
        self.setLayout(layout)
        self.set_channels([])

    def set_channels(self, channels: list[str]) -> None:
        current = self.x_channel_combo.currentText()
        options = ["Time", *[channel for channel in channels if channel != "Time"]]
        self.x_channel_combo.clear()
        self.x_channel_combo.addItems(options)
        if current and current in options:
            self.x_channel_combo.setCurrentText(current)
        else:
            self.x_channel_combo.setCurrentText("Time")

    def current_options(self) -> dict[str, object]:
        window = abs(int(self.average_window_spin.value()))
        if window % 2 == 0:
            window += 1
        if window < 3:
            window = 5
        self.average_window_spin.setValue(window)
        return {
            "x_channel": self.x_channel_combo.currentText() or "Time",
            "average": self.average_checkbox.isChecked(),
            "average_window": window,
            "integrate": self.integrate_checkbox.isChecked(),
            "subtract_average": self.subtract_average_checkbox.isChecked(),
        }
