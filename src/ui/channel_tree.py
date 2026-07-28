from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from services.tdms_reader import ChannelInfo, FileMetadata


class ChannelTreeWidget(QWidget):
    channel_double_clicked = Signal(object)
    plot_selected_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabel("Groups / Channels")
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)

        self.plot_selected_button = QPushButton("Plot selected", self)
        self.plot_selected_button.clicked.connect(self.plot_selected_requested.emit)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tree)
        layout.addWidget(self.plot_selected_button)
        self.setLayout(layout)

    def populate(self, metadata: FileMetadata) -> None:
        self.tree.clear()
        for group_name in metadata.groups:
            group_item = QTreeWidgetItem([group_name])
            group_item.setFlags(group_item.flags() & ~Qt.ItemIsSelectable)
            for channel_name in metadata.channels_by_group.get(group_name, []):
                channel_item = QTreeWidgetItem([channel_name])
                channel_item.setData(0, Qt.UserRole, ChannelInfo(group=group_name, name=channel_name))
                channel_item.setFlags(channel_item.flags() | Qt.ItemIsUserCheckable)
                channel_item.setCheckState(0, Qt.Unchecked)
                group_item.addChild(channel_item)
            self.tree.addTopLevelItem(group_item)
        self.tree.expandAll()

    def get_selected_channels(self) -> list[ChannelInfo]:
        channels: list[ChannelInfo] = []
        for i in range(self.tree.topLevelItemCount()):
            group_item = self.tree.topLevelItem(i)
            for j in range(group_item.childCount()):
                channel_item = group_item.child(j)
                if channel_item.checkState(0) == Qt.Checked:
                    info = channel_item.data(0, Qt.UserRole)
                    if isinstance(info, ChannelInfo):
                        channels.append(info)
        return channels

    def _on_item_double_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        info = item.data(0, Qt.UserRole)
        if isinstance(info, ChannelInfo):
            self.channel_double_clicked.emit(info)
