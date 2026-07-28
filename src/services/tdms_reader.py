from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from nptdms import TdmsFile
from scipy.integrate import cumulative_trapezoid
from scipy.signal import savgol_filter


@dataclass
class ChannelInfo:
    group: str
    name: str


@dataclass
class FileMetadata:
    path: Path
    groups: list[str] = field(default_factory=list)
    channels_by_group: dict[str, list[str]] = field(default_factory=dict)


class TdmsReader:
    """Handles all TDMS file I/O."""

    def load_metadata(self, file_path: str | Path) -> FileMetadata:
        path = Path(file_path).expanduser().resolve()
        tdms_meta = TdmsFile.read_metadata(str(path))
        groups = tdms_meta.groups()
        channels_by_group = {
            group.name: [channel.name for channel in group.channels()]
            for group in groups
        }
        return FileMetadata(
            path=path,
            groups=[group.name for group in groups],
            channels_by_group=channels_by_group,
        )

    def _prepare_y_data(
        self,
        tdms_file: TdmsFile,
        group_name: str,
        y_channel: str,
        integrate: bool = False,
        subtract_average: bool = False,
        average: bool = False,
        average_window: int = 5,
    ) -> np.ndarray:
        if integrate:
            tmp_y = tdms_file[group_name][y_channel][:]
            tmp_x = tdms_file[group_name][y_channel].time_track()
            if subtract_average:
                return cumulative_trapezoid(tmp_y - np.mean(tmp_y), tmp_x, initial=0)
            return cumulative_trapezoid(tmp_y, tmp_x, initial=0)

        if average:
            window = abs(int(average_window))
            if window % 2 == 0:
                window += 1
            if window < 3:
                window = 5
            return savgol_filter(tdms_file[group_name][y_channel][:], window, 3, mode="nearest")

        return tdms_file[group_name][y_channel][:]

    @staticmethod
    def _normalize_axis_data(data: np.ndarray) -> np.ndarray:
        np_data = np.asarray(data)
        if np.issubdtype(np_data.dtype, np.datetime64):
            return np_data.astype("datetime64[ns]").astype(np.int64) / 1_000_000_000.0
        return np_data

    def get_channel_data(
        self,
        meta: FileMetadata,
        group: str,
        channel: str,
        x_channel: str = "Time",
        integrate: bool = False,
        subtract_average: bool = False,
        average: bool = False,
        average_window: int = 5,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Return (x_data, y_data) numpy arrays, reusing logic from tdms_plot."""
        with TdmsFile.open(str(meta.path)) as tdms_file:
            y_data = self._prepare_y_data(
                tdms_file,
                group,
                channel,
                integrate=integrate,
                subtract_average=subtract_average,
                average=average,
                average_window=average_window,
            )
            if x_channel == "Time":
                x_data = tdms_file[group][channel].time_track()
            else:
                x_data = tdms_file[group][x_channel][:]
        return self._normalize_axis_data(x_data), np.asarray(y_data)
