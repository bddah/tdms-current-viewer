from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QSettings, Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSplitter,
    QStyle,
    QWidget,
)

from services.exporter import Exporter
from services.tdms_reader import ChannelInfo, FileMetadata, TdmsReader
from ui.channel_tree import ChannelTreeWidget
from ui.dialogs import ProgressDialog, show_error, show_info
from ui.plot_panel import PlotPanel


class MetadataLoadWorker(QObject):
    progress = Signal(int)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, reader: TdmsReader, file_path: str | Path):
        super().__init__()
        self.reader = reader
        self.file_path = file_path

    @Slot()
    def run(self) -> None:
        try:
            self.progress.emit(10)
            metadata = self.reader.load_metadata(self.file_path)
            self.progress.emit(100)
            self.finished.emit(metadata)
        except Exception as exc:
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TDMS Viewer")
        self.resize(1280, 800)

        self.reader = TdmsReader()
        self.exporter = Exporter()
        self.settings = QSettings("TdmsViewer", "TdmsViewer")

        self.metadata: FileMetadata | None = None
        self.current_file_path: Path | None = None
        self.current_plot_data: dict[str, object] | None = None
        self._loader_thread: QThread | None = None
        self._loader_worker: MetadataLoadWorker | None = None
        self._progress_dialog: ProgressDialog | None = None

        self.channel_tree = ChannelTreeWidget(self)
        self.plot_panel = PlotPanel(self)
        self.channel_tree.channel_double_clicked.connect(self._plot_single_channel)
        self.channel_tree.plot_selected_requested.connect(self._plot_checked_channels)
        self.plot_panel.plot_requested.connect(self._plot_checked_channels)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(self.channel_tree)
        splitter.addWidget(self.plot_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.addWidget(splitter)
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.file_label = QLabel("No file loaded", self)
        self.cursor_label = QLabel("", self)
        self.statusBar().addWidget(self.file_label, 1)
        self.statusBar().addPermanentWidget(self.cursor_label)

        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self._connect_plot_cursor_tracking()

    def _standard_icon(self, icon_enum):
        return self.style().standardIcon(icon_enum)

    def _create_actions(self) -> None:
        self.open_action = QAction(self._standard_icon(QStyle.SP_DialogOpenButton), "Open", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.open_file)

        self.refresh_action = QAction(self._standard_icon(QStyle.SP_BrowserReload), "Refresh", self)
        self.refresh_action.setShortcut("F5")
        self.refresh_action.triggered.connect(self.refresh_file)

        self.export_csv_action = QAction(self._standard_icon(QStyle.SP_DialogSaveButton), "Export CSV", self)
        self.export_csv_action.setShortcut("Ctrl+E")
        self.export_csv_action.triggered.connect(self.export_csv)

        self.save_plot_action = QAction(self._standard_icon(QStyle.SP_DriveFDIcon), "Save Plot", self)
        self.save_plot_action.setShortcut("Ctrl+S")
        self.save_plot_action.triggered.connect(self.save_plot)

        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.close)

        self.toggle_legend_action = QAction("Toggle Legend", self)
        self.toggle_legend_action.triggered.connect(self.plot_panel.plot_widget.toggle_legend)

        self.toggle_grid_action = QAction("Toggle Grid", self)
        self.toggle_grid_action.triggered.connect(self.plot_panel.plot_widget.toggle_grid)

        self.about_action = QAction("About", self)
        self.about_action.triggered.connect(self.show_about)

    def _create_menus(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.refresh_action)
        file_menu.addSeparator()
        file_menu.addAction(self.export_csv_action)
        file_menu.addAction(self.save_plot_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        view_menu = menu_bar.addMenu("View")
        view_menu.addAction(self.toggle_legend_action)
        view_menu.addAction(self.toggle_grid_action)

        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction(self.about_action)

    def _create_toolbar(self) -> None:
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.refresh_action)
        toolbar.addAction(self.export_csv_action)
        toolbar.addAction(self.save_plot_action)

    def _connect_plot_cursor_tracking(self) -> None:
        scene = self.plot_panel.plot_widget.plot_item.scene()
        scene.sigMouseMoved.connect(self._on_mouse_moved)

    @Slot(object)
    def _on_mouse_moved(self, pos) -> None:
        plot_item = self.plot_panel.plot_widget.plot_item
        if plot_item.sceneBoundingRect().contains(pos):
            point = plot_item.vb.mapSceneToView(pos)
            self.cursor_label.setText(f"x={point.x():.6g}, y={point.y():.6g}")
        else:
            self.cursor_label.clear()

    @Slot()
    def open_file(self) -> None:
        start_dir = self.settings.value("last_dir", str(Path.cwd()))
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open TDMS file",
            start_dir,
            "TDMS Files (*.tdms)",
        )
        if not file_path:
            return
        selected_path = Path(file_path)
        self.settings.setValue("last_dir", str(selected_path.parent))
        self._load_file(selected_path)

    @Slot()
    def refresh_file(self) -> None:
        if self.current_file_path is None:
            show_info(self, "Refresh", "Open a TDMS file first.")
            return
        self._load_file(self.current_file_path)

    def _load_file(self, file_path: Path) -> None:
        if self._loader_thread is not None:
            return
        self.current_file_path = file_path.resolve()
        self._progress_dialog = ProgressDialog(self, "Loading TDMS", f"Loading {file_path.name}...", 0, 100)
        self._progress_dialog.setValue(0)
        self._progress_dialog.show()

        self._loader_thread = QThread(self)
        self._loader_worker = MetadataLoadWorker(self.reader, self.current_file_path)
        self._loader_worker.moveToThread(self._loader_thread)

        self._loader_thread.started.connect(self._loader_worker.run)
        self._loader_worker.progress.connect(self._progress_dialog.setValue)
        self._loader_worker.finished.connect(self._on_metadata_loaded)
        self._loader_worker.error.connect(self._on_metadata_error)
        self._loader_worker.finished.connect(lambda _metadata: self._cleanup_loader())
        self._loader_worker.error.connect(lambda _message: self._cleanup_loader())
        self._loader_thread.start()

    @Slot(object)
    def _on_metadata_loaded(self, metadata: FileMetadata) -> None:
        self.metadata = metadata
        self.channel_tree.populate(metadata)
        first_group = metadata.groups[0] if metadata.groups else None
        if first_group is not None:
            self.plot_panel.set_channels(metadata.channels_by_group.get(first_group, []))
        self.file_label.setText(str(metadata.path))
        self.statusBar().showMessage(f"Loaded {metadata.path}", 3000)

    @Slot(str)
    def _on_metadata_error(self, message: str) -> None:
        show_error(self, "Open TDMS file", message)
        self.statusBar().showMessage("Failed to load TDMS file", 3000)

    @Slot()
    def _cleanup_loader(self) -> None:
        if self._progress_dialog is not None:
            self._progress_dialog.setValue(100)
            self._progress_dialog.close()
            self._progress_dialog.deleteLater()
            self._progress_dialog = None
        if self._loader_thread is not None:
            self._loader_thread.quit()
            self._loader_thread.wait()
            self._loader_thread.deleteLater()
            self._loader_thread = None
        if self._loader_worker is not None:
            self._loader_worker.deleteLater()
            self._loader_worker = None

    @Slot(object)
    def _plot_single_channel(self, info: ChannelInfo) -> None:
        self.plot_channels([info])

    @Slot()
    def _plot_checked_channels(self) -> None:
        channels = self.channel_tree.get_selected_channels()
        if not channels:
            show_info(self, "Plot channels", "Select at least one channel to plot.")
            return
        self.plot_channels(channels)

    def plot_channels(self, channels: list[ChannelInfo]) -> None:
        if self.metadata is None:
            show_info(self, "Plot channels", "Open a TDMS file first.")
            return
        group_channels = self.metadata.channels_by_group.get(channels[0].group, [])
        self.plot_panel.set_channels(group_channels)
        options = self.plot_panel.current_options()
        self.plot_panel.plot_widget.clear_plot()
        self.current_plot_data = None

        plotted = 0
        errors: list[str] = []
        for info in channels:
            try:
                x_data, y_data = self.reader.get_channel_data(
                    self.metadata,
                    info.group,
                    info.name,
                    x_channel=str(options["x_channel"]),
                    integrate=bool(options["integrate"]),
                    subtract_average=bool(options["subtract_average"]),
                    average=bool(options["average"]),
                    average_window=int(options["average_window"]),
                )
                curve_name = f"{info.group}/{info.name}"
                if plotted == 0:
                    self.plot_panel.plot_widget.plot_channel(
                        x_data,
                        y_data,
                        str(options["x_channel"]),
                        info.name,
                        curve_name,
                    )
                    self.current_plot_data = {
                        "x": x_data,
                        "y": y_data,
                        "x_label": str(options["x_channel"]),
                        "y_label": info.name,
                    }
                else:
                    self.plot_panel.plot_widget.add_channel(x_data, y_data, curve_name)
                plotted += 1
            except Exception as exc:
                errors.append(f"{info.group}/{info.name}: {exc}")

        if plotted:
            self.statusBar().showMessage(f"Plotted {plotted} channel(s)", 3000)
        if errors:
            show_error(self, "Plot channels", "\n".join(errors))

    @Slot()
    def export_csv(self) -> None:
        if not self.current_plot_data:
            show_info(self, "Export CSV", "Plot a channel first.")
            return
        start_dir = self.settings.value("last_dir", str(Path.cwd()))
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            str(Path(start_dir) / "plot_data.csv"),
            "CSV Files (*.csv)",
        )
        if not file_path:
            return
        output_path = Path(file_path)
        self.settings.setValue("last_dir", str(output_path.parent))
        self.exporter.to_csv(
            self.current_plot_data["x"],
            self.current_plot_data["y"],
            str(self.current_plot_data["x_label"]),
            str(self.current_plot_data["y_label"]),
            output_path,
        )
        self.statusBar().showMessage(f"CSV exported to {output_path}", 3000)

    @Slot()
    def save_plot(self) -> None:
        if not self.current_plot_data:
            show_info(self, "Save Plot", "Plot a channel first.")
            return
        start_dir = self.settings.value("last_dir", str(Path.cwd()))
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Plot",
            str(Path(start_dir) / "plot.png"),
            "PNG Files (*.png)",
        )
        if not file_path:
            return
        output_path = Path(file_path)
        self.settings.setValue("last_dir", str(output_path.parent))
        self.exporter.save_plot_png(self.plot_panel.plot_widget, output_path)
        self.statusBar().showMessage(f"Plot saved to {output_path}", 3000)

    @Slot()
    def show_about(self) -> None:
        show_info(
            self,
            "About TDMS Viewer",
            "TDMS Viewer\n\nNative desktop TDMS plotting application built with PySide6 and pyqtgraph.",
        )
