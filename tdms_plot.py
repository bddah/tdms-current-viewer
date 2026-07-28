from os import listdir
from pathlib import Path
from re import match
from time import strftime, localtime
from urllib.parse import parse_qs, urlparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import plotly.graph_objects as go
import numpy as np
from ipywidgets import widgets, Layout
from nptdms import TdmsFile
from scipy.signal import savgol_filter
from scipy.integrate import cumulative_trapezoid

'''
This is a module containing widgets for working with TDMS files.

Minimal example:
import tdms_plot
tdms_plot.main_widget()
'''


def _prepare_y_data(tdms_file, group_name, y_channel, integrate=False,
                    subtract_average=False, average=False, average_window=5):
    if integrate:
        tmp_y = tdms_file[group_name][y_channel][:]
        tmp_x = tdms_file[group_name][y_channel].time_track()
        if subtract_average:
            return cumulative_trapezoid(tmp_y-np.mean(tmp_y), tmp_x, initial=0)
        return cumulative_trapezoid(tmp_y, tmp_x, initial=0)

    if average:
        window = abs(int(average_window))
        if (window % 2 == 0):
            window += 1
        if (window < 3):
            window = 5
        return savgol_filter(tdms_file[group_name][y_channel][:], window, 3,
                             mode='nearest')

    return tdms_file[group_name][y_channel][:]


def get_plot_data(tdms_file_path, group_name, x_channel, y_channel,
                  integrate=False, subtract_average=False, average=False,
                  average_window=5):
    with TdmsFile.open(tdms_file_path) as tdms_file:
        y_data = _prepare_y_data(
            tdms_file, group_name, y_channel,
            integrate=integrate,
            subtract_average=subtract_average,
            average=average,
            average_window=average_window
        )
        if x_channel == 'Time':
            x_data = tdms_file[group_name][y_channel].time_track()
        else:
            x_data = tdms_file[group_name][x_channel][:]
    return x_data, y_data

class main_widget(widgets.VBox):

    def __init__(self):
        super().__init__()

        style = {'description_width': 'initial'}

        tdms_file_base_folder_w = widgets.Text(
            value='',
            placeholder='Relative path to directory with tdms files',
            description='Base path:',
            style={'description_width': 'initial'},
            # layout=Layout(width='250px'),
            )

        tdms_file_path_w = widgets.Dropdown(
            options=['tmp.tdms'],
            value='tmp.tdms',
            placeholder='Type file name',
            description='TDMS file:',
            style={'description_width': 'initial'},
            layout=Layout(width='250px'),
            )

        refresh_btn = widgets.Button(
            description='',
            button_style='',
            icon='refresh',  # icons are taken from font-awesome
            layout=Layout(width='50px'),
            tooltip='refresh files list'
            )

        def refresh_file_list(change):
            # listdir is imported from os, match - from re
            tdms_file_path_w.options = [
                f for f in listdir('./'+tdms_file_base_folder_w.value+'/') if match(r'.*\.tdms$', f)]
        refresh_btn.on_click(refresh_file_list)

        group = widgets.Dropdown(
            options=['Untitled'],
            value='Untitled',
            description='Group:',
            layout=Layout(width='150px'),
            style=style
            )

        group_index = widgets.IntSlider(
            value=0,
            min=0,
            max=1,
            step=1,
            continuous_update=False,
            layout=Layout(width='300px'),
            style=style
            )
        group_link = widgets.jslink((group, 'index'), (group_index, 'value'))

        open_file_btn = widgets.Button(
            description='Open TDMS file',
            disabled=False,
            button_style='',  # 'success', 'info', 'warning', 'danger' or ''
            tooltip='Open TDMS file',
            layout=Layout(width='200px')
            )
        # on_click event for this button is defined further

        file_loading = widgets.ToggleButton(
            value=False,
            description='...',
            button_style='info',
            disabled=True,
            style=style,
            layout=Layout(width='100px')
            )

        x_channel = widgets.Dropdown(
            options=['Time', '1 Voltage', '2 Current'],
            value='Time',
            description='Channel for x axis:',
            style=style
            )

        y_channel = widgets.Dropdown(
            options=['Time', '1 Voltage', '2 Current'],
            value='1 Voltage',
            description='Channel for y axis:',
            style=style
            )

        average_checkbox = widgets.Checkbox(
            value=False,
            description='Average',
            layout=Layout(width='100px'),
            style=style
            )

        average_value = widgets.IntText(
            value=0,
            min=0,
            description='',
            layout=Layout(width='70px'),
            style=style
            )

        integrate_checkbox = widgets.Checkbox(
            value=False,
            description='Integrate',
            layout=Layout(width='90px'),
            style=style
            )

        substract_checkbox = widgets.Checkbox(
            value=False,
            description='Subtract average',
            layout=Layout(width='150px'),
            style=style
            )

        save_file_btn = widgets.Button(
            description='Save to file',
            disabled=False,
            button_style='',  # 'success', 'info', 'warning', 'danger' or ''
            tooltip='Save data within curent xrange to csv file',
            layout=Layout(width='200px')
        )
        # on_click event is defined further

        save_file_path_w = widgets.Text(
            value='',
            placeholder='File is saved in "Base path" folder',
            description='Save path:',
            style={'description_width': 'initial'},
            # layout=Layout(width='250px'),
            )

        def refresh_graph(change):
            if not file_loading.value:
                # save the values for possible future use
                self.group = group.value
                self.x_channel = x_channel.value
                self.y_channel = y_channel.value
                with graph.batch_update():
                    window = abs(int(average_value.value))
                    if (window % 2 == 0):
                        window += 1
                    if (window < 3):
                        window = 5
                    average_value.value = window
                    x_data, y_data = get_plot_data(
                        self.tdms_file_path,
                        self.group,
                        self.x_channel,
                        self.y_channel,
                        integrate=integrate_checkbox.value,
                        subtract_average=substract_checkbox.value,
                        average=average_checkbox.value,
                        average_window=window
                    )
                    # if the trace is not created yet - add new trace
                    if not graph.data:
                        graph.add_scatter(x=x_data, y=y_data)
                    else:
                        graph.data[0].x = x_data
                        graph.data[0].y = y_data

        log_area = widgets.Textarea(
            style=style,
            layout=Layout(width='400px', height='150px'),
            )

        margin = go.layout.Margin(l=20, r=20, b=20, t=30)
        graph = go.FigureWidget(data=[])
        self.xrange = []
        graph.update_layout(margin=margin)

        average_checkbox.observe(refresh_graph, names="value")
        integrate_checkbox.observe(refresh_graph, names="value")
        substract_checkbox.observe(refresh_graph, names="value")
        group.observe(refresh_graph, names="value")
        x_channel.observe(refresh_graph, names="value")
        y_channel.observe(refresh_graph, names="value")

        def figure_xrange_change(layout, xrange):
            self.xrange = xrange
        graph.layout.on_change(figure_xrange_change,'xaxis.range')

        def save_file(change):
            if save_file_path_w.value =='':
                log_area.value += strftime("%Y-%m-%d %H:%M:%S",
                                    localtime()) + "can't save file - save path is empty"
                return
            if x_channel.index != 0:
                log_area.value += strftime("%Y-%m-%d %H:%M:%S",
                                    localtime()) + " can't save file - x_channel should be Time (index = 0)"
                return
            with TdmsFile.open(self.tdms_file_path) as tdms_file:
                y_data = tdms_file[self.group][self.y_channel][:]
                x_data = tdms_file[self.group][self.y_channel].time_track()
                x_data_mask = (x_data > self.xrange[0]) & (x_data < self.xrange[1])
                tmp_array = np.concatenate((np.vstack(x_data[x_data_mask]), np.vstack(y_data[x_data_mask])), axis=1)
                save_file_path = './'+tdms_file_base_folder_w.value+'/'+save_file_path_w.value
                np.savetxt(save_file_path, tmp_array, delimiter='\t')
                log_area.value += strftime("%Y-%m-%d %H:%M:%S",
                                    localtime()) + f" chosen data range saved to {save_file_path}"
        save_file_btn.on_click(save_file)

        def average_value_change(change):
            # recalculate smoothed signal if we changed the window and the
            # "average" checkbox is ON
            if average_checkbox.value == True:
                refresh_graph(change)

        average_value.observe(average_value_change, names="value")

        def open_file_event(b):
            file_loading.value = True
            file_loading.description = 'Loading file'
            self.tdms_file_path = './'+tdms_file_base_folder_w.value+'/'+tdms_file_path_w.value
            self.tdms_file = TdmsFile.read_metadata(self.tdms_file_path)
            self.groups = self.tdms_file.groups()
            self.channels = [channel.name for channel in self.groups[0].channels()]
            group.options = [group.name for group in self.groups]
            group_index.max = len(self.groups)-1
            x_channel.options = self.channels
            y_channel.options = self.channels
            x_channel.value = self.channels[0]
            if len(self.channels) > 1:
                y_channel.value = self.channels[1]
            log_area.value += strftime("%Y-%m-%d %H:%M:%S",
                                    localtime()) + f" file {self.tdms_file_path} opened" + "\n"
            file_loading.value = False
            file_loading.description = '...'

        open_file_btn.on_click(open_file_event)

        # listdir imported from os, match - from re
        tdms_file_path_w.options = [
            f for f in listdir('./') if match(r'.*\.tdms$', f)]

        # Build UI layout
        box_layout = widgets.Layout(
            margin='0px 0px 0px 0px',
            padding='5px 5px 5px 5px'
        )
        tdms_file_path_box = widgets.VBox(
            [widgets.HBox([refresh_btn, tdms_file_path_w]),
             tdms_file_base_folder_w, widgets.HBox([open_file_btn, file_loading])])
        group_box = widgets.HBox([group, group_index])
        ui_left = widgets.VBox(
            [tdms_file_path_box, group_box, x_channel, y_channel,
            widgets.HBox([average_checkbox, average_value, integrate_checkbox,
                substract_checkbox])])
        ui_left.layout = box_layout
        ui_left.layout.width = '50%'
        ui_right = widgets.HBox([log_area])
        ui_right.layout.align_items = 'stretch'
        ui_right.layout = box_layout
        save_file_box = widgets.HBox([save_file_path_w, save_file_btn])
        ui_bottom = widgets.VBox([graph,save_file_box])
        ui_bottom.layout.height = '380px'
        ui_top = widgets.HBox([ui_left, ui_right])
        self.children = [ui_top, ui_bottom]


def _resolve_base_path(base_path):
    root = Path.cwd().resolve()
    if not base_path:
        return root
    candidate = (root / base_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError('Base path should be inside current directory') from exc
    return candidate


def _list_tdms_files(base_path):
    folder = _resolve_base_path(base_path)
    if not folder.is_dir():
        raise FileNotFoundError(f'Folder not found: {folder}')
    return sorted(
        [item.name for item in folder.iterdir()
         if item.is_file() and item.suffix.lower() == '.tdms']
    )


def _resolve_tdms_file_path(base_path, file_name):
    if not file_name:
        raise ValueError('File name is required')
    if '/' in file_name or '\\' in file_name:
        raise ValueError('File name should not include directories')
    folder = _resolve_base_path(base_path)
    tdms_file_path = (folder / file_name).resolve()
    try:
        tdms_file_path.relative_to(folder)
    except ValueError as exc:
        raise ValueError('Invalid file path') from exc
    if not tdms_file_path.is_file():
        raise FileNotFoundError(f'File not found: {tdms_file_path}')
    return tdms_file_path


def _read_tdms_metadata(tdms_file_path):
    tdms_meta = TdmsFile.read_metadata(str(tdms_file_path))
    groups = tdms_meta.groups()
    channels_by_group = {
        group.name: [channel.name for channel in group.channels()]
        for group in groups
    }
    return {
        'groups': [group.name for group in groups],
        'channels_by_group': channels_by_group
    }


def _serialize_axis(data):
    np_data = np.asarray(data)
    if np.issubdtype(np_data.dtype, np.datetime64):
        return np_data.astype('datetime64[ms]').astype(str).tolist()
    return np_data.tolist()


WEB_APP_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>TDMS Viewer</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    body { font-family: Arial, sans-serif; margin: 16px; }
    .row { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 10px; align-items: center; }
    label { min-width: 110px; }
    input, select { min-width: 220px; padding: 4px; }
    #plot { width: 100%; height: 500px; border: 1px solid #ddd; }
    #status { white-space: pre-wrap; font-size: 13px; color: #333; }
    button { padding: 6px 12px; }
    details { border: 1px solid #ccc; padding: 6px 10px; margin-bottom: 10px; border-radius: 4px; background: #fafafa; }
    details summary { cursor: pointer; font-weight: bold; user-select: none; }
  </style>
</head>
<body>
  <h2>TDMS local web app</h2>

  <!-- Trace 1 -->
  <div class="row">
    <label for="basePath">Base path</label>
    <input id="basePath" placeholder="Relative or absolute folder path" />
    <button id="refreshFiles">Refresh files</button>
  </div>
  <div class="row">
    <label for="tdmsFile">TDMS file</label>
    <select id="tdmsFile"></select>
  </div>
  <div class="row">
    <label for="group">Group</label>
    <select id="group"></select>
    <label for="xChannel">X channel</label>
    <select id="xChannel"></select>
    <label for="yChannel">Y channel</label>
    <select id="yChannel"></select>
  </div>
  <div class="row">
    <label><input type="checkbox" id="average" /> Average</label>
    <label style="min-width:auto;">Window <input id="averageWindow" type="number" value="5" min="3" step="1" style="min-width: 80px;" /></label>
  </div>
  <div class="row">
    <label><input type="checkbox" id="integrate" /> Integrate</label>
    <label><input type="checkbox" id="subtractAverage" /> Subtract average</label>
  </div>

  <!-- Compare: multi-trace — overlay or separate subplots -->
  <details id="compareSection">
    <summary>Compare: multi-trace (overlay or separate subplots)</summary>
    <div class="row">
      <label for="basePath2">Base path 2</label>
      <input id="basePath2" placeholder="Relative or absolute folder path" />
      <button id="refreshFiles2">Refresh files</button>
    </div>
    <div class="row">
      <label for="tdmsFile2">TDMS file 2</label>
      <select id="tdmsFile2"></select>
    </div>
    <div class="row">
      <label for="group2">Group 2</label>
      <select id="group2"></select>
      <label for="xChannel2">X channel 2</label>
      <select id="xChannel2"></select>
      <label for="yChannel2">Y channel 2</label>
      <select id="yChannel2"></select>
    </div>
    <div class="row">
      <label><input type="checkbox" id="average2" /> Average</label>
      <label style="min-width:auto;">Window <input id="averageWindow2" type="number" value="5" min="3" step="1" style="min-width: 80px;" /></label>
    </div>
    <div class="row">
      <label><input type="checkbox" id="integrate2" /> Integrate</label>
      <label><input type="checkbox" id="subtractAverage2" /> Subtract average</label>
    </div>
    <div class="row">
      <span style="min-width:110px;">Plot mode:</span>
      <label style="min-width:auto;"><input type="radio" name="plotMode" value="overlay" checked /> Overlay (one plot)</label>
      <label style="min-width:auto;"><input type="radio" name="plotMode" value="subplots" /> Separate subplots</label>
    </div>
  </details>

  <div class="row">
    <button id="plotBtn">Plot</button>
  </div>
  <div id="plot"></div>
  <pre id="status"></pre>

  <script>
    const tdmsFile = document.getElementById('tdmsFile');
    const group = document.getElementById('group');
    const xChannel = document.getElementById('xChannel');
    const yChannel = document.getElementById('yChannel');
    const tdmsFile2 = document.getElementById('tdmsFile2');
    const group2 = document.getElementById('group2');
    const xChannel2 = document.getElementById('xChannel2');
    const yChannel2 = document.getElementById('yChannel2');
    const status = document.getElementById('status');

    let channelsByGroup = {};
    let channelsByGroup2 = {};

    function setStatus(text) { status.textContent = text; }
    function qs(basePath) { return new URLSearchParams({ base_path: basePath || '' }); }

    // --- Trace 1 ---
    async function refreshFiles() {
      try {
        setStatus('Loading file list...');
        const response = await fetch('/api/files?' + qs(document.getElementById('basePath').value).toString());
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || 'Failed to load files');
        tdmsFile.innerHTML = '';
        payload.files.forEach(file => {
          const opt = document.createElement('option');
          opt.value = file; opt.textContent = file;
          tdmsFile.appendChild(opt);
        });
        setStatus(payload.files.length ? `Found ${payload.files.length} file(s)` : 'No TDMS files found');
        if (payload.files.length) await refreshMetadata();
      } catch (err) {
        setStatus(err.message);
      }
    }

    function fillChannels() {
      const prevX = xChannel.value;
      const prevY = yChannel.value;
      const selectedGroup = group.value;
      const channels = channelsByGroup[selectedGroup] || [];
      xChannel.innerHTML = '';
      yChannel.innerHTML = '';

      const timeOption = document.createElement('option');
      timeOption.value = 'Time';
      timeOption.textContent = 'Time';
      xChannel.appendChild(timeOption);

      channels.forEach(channelName => {
        const xOpt = document.createElement('option');
        xOpt.value = channelName; xOpt.textContent = channelName;
        xChannel.appendChild(xOpt);

        const yOpt = document.createElement('option');
        yOpt.value = channelName; yOpt.textContent = channelName;
        yChannel.appendChild(yOpt);
      });

      // Preserve previous selection when the channel still exists
      if (prevX && [...xChannel.options].some(o => o.value === prevX)) {
        xChannel.value = prevX;
      } else {
        xChannel.value = 'Time';
      }
      if (prevY && [...yChannel.options].some(o => o.value === prevY)) {
        yChannel.value = prevY;
      } else if (channels.length) {
        yChannel.value = channels[0];
      }
    }

    async function refreshMetadata() {
      try {
        if (!tdmsFile.value) return;
        setStatus('Loading metadata...');
        const params = qs(document.getElementById('basePath').value);
        params.set('file', tdmsFile.value);
        const response = await fetch('/api/metadata?' + params.toString());
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || 'Failed to load metadata');
        channelsByGroup = payload.channels_by_group || {};
        group.innerHTML = '';
        payload.groups.forEach(groupName => {
          const opt = document.createElement('option');
          opt.value = groupName; opt.textContent = groupName;
          group.appendChild(opt);
        });
        fillChannels();
        setStatus(`Loaded metadata for ${tdmsFile.value}`);
      } catch (err) {
        setStatus(err.message);
      }
    }

    // --- Trace 2 ---
    async function refreshFiles2() {
      try {
        setStatus('Loading file list (trace 2)...');
        const response = await fetch('/api/files?' + qs(document.getElementById('basePath2').value).toString());
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || 'Failed to load files (trace 2)');
        tdmsFile2.innerHTML = '';
        payload.files.forEach(file => {
          const opt = document.createElement('option');
          opt.value = file; opt.textContent = file;
          tdmsFile2.appendChild(opt);
        });
        setStatus(payload.files.length ? `Trace 2: found ${payload.files.length} file(s)` : 'Trace 2: no TDMS files found');
        if (payload.files.length) await refreshMetadata2();
      } catch (err) {
        setStatus(err.message);
      }
    }

    function fillChannels2() {
      const prevX = xChannel2.value;
      const prevY = yChannel2.value;
      const selectedGroup = group2.value;
      const channels = channelsByGroup2[selectedGroup] || [];
      xChannel2.innerHTML = '';
      yChannel2.innerHTML = '';

      const timeOption = document.createElement('option');
      timeOption.value = 'Time';
      timeOption.textContent = 'Time';
      xChannel2.appendChild(timeOption);

      channels.forEach(channelName => {
        const xOpt = document.createElement('option');
        xOpt.value = channelName; xOpt.textContent = channelName;
        xChannel2.appendChild(xOpt);

        const yOpt = document.createElement('option');
        yOpt.value = channelName; yOpt.textContent = channelName;
        yChannel2.appendChild(yOpt);
      });

      if (prevX && [...xChannel2.options].some(o => o.value === prevX)) {
        xChannel2.value = prevX;
      } else {
        xChannel2.value = 'Time';
      }
      if (prevY && [...yChannel2.options].some(o => o.value === prevY)) {
        yChannel2.value = prevY;
      } else if (channels.length) {
        yChannel2.value = channels[0];
      }
    }

    async function refreshMetadata2() {
      try {
        if (!tdmsFile2.value) return;
        setStatus('Loading metadata (trace 2)...');
        const params = qs(document.getElementById('basePath2').value);
        params.set('file', tdmsFile2.value);
        const response = await fetch('/api/metadata?' + params.toString());
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || 'Failed to load metadata (trace 2)');
        channelsByGroup2 = payload.channels_by_group || {};
        group2.innerHTML = '';
        payload.groups.forEach(groupName => {
          const opt = document.createElement('option');
          opt.value = groupName; opt.textContent = groupName;
          group2.appendChild(opt);
        });
        fillChannels2();
        setStatus(`Loaded metadata (trace 2) for ${tdmsFile2.value}`);
      } catch (err) {
        setStatus(err.message);
      }
    }

    async function plotData() {
      try {
        if (!tdmsFile.value || !group.value || !yChannel.value) {
          throw new Error('Choose file, group and Y channel first');
        }
        setStatus('Building plot...');

        const p1 = await fetchTrace(
          document.getElementById('basePath').value,
          tdmsFile.value, group.value, xChannel.value, yChannel.value,
          document.getElementById('average').checked,
          document.getElementById('averageWindow').value,
          document.getElementById('integrate').checked,
          document.getElementById('subtractAverage').checked
        );

        const compareOpen = document.getElementById('compareSection').open;
        const plotMode = document.querySelector('input[name="plotMode"]:checked').value;

        if (compareOpen && tdmsFile2.value && group2.value && yChannel2.value) {
          const p2 = await fetchTrace(
            document.getElementById('basePath2').value,
            tdmsFile2.value, group2.value, xChannel2.value, yChannel2.value,
            document.getElementById('average2').checked,
            document.getElementById('averageWindow2').value,
            document.getElementById('integrate2').checked,
            document.getElementById('subtractAverage2').checked
          );

          const trace1 = { x: p1.x, y: p1.y, mode: 'lines', type: 'scatter',
                           name: `${p1.file} / ${p1.y_channel}` };
          const trace2 = { x: p2.x, y: p2.y, mode: 'lines', type: 'scatter',
                           name: `${p2.file} / ${p2.y_channel}` };

          if (plotMode === 'subplots') {
            trace2.xaxis = 'x2';
            trace2.yaxis = 'y2';
            Plotly.newPlot('plot', [trace1, trace2], {
              grid: { rows: 2, columns: 1, pattern: 'independent' },
              margin: { l: 50, r: 20, t: 30, b: 40 },
              xaxis:  { title: p1.x_channel },
              yaxis:  { title: p1.y_channel },
              xaxis2: { title: p2.x_channel },
              yaxis2: { title: p2.y_channel },
              height: 700
            });
          } else {
            Plotly.newPlot('plot', [trace1, trace2], {
              margin: { l: 50, r: 20, t: 30, b: 40 },
              xaxis: { title: p1.x_channel },
              yaxis: { title: p1.y_channel }
            });
          }
          setStatus(`Plotted trace 1: ${p1.file}/${p1.group} | trace 2: ${p2.file}/${p2.group}`);
        } else {
          Plotly.newPlot('plot', [{ x: p1.x, y: p1.y, mode: 'lines', type: 'scatter' }], {
            margin: { l: 40, r: 20, t: 30, b: 40 },
            xaxis: { title: p1.x_channel },
            yaxis: { title: p1.y_channel }
          });
          setStatus(`Plotted ${p1.file} / ${p1.group}`);
        }
      } catch (err) {
        setStatus(err.message);
      }
    }

    async function fetchTrace(basePath, file, grp, xCh, yCh, avg, avgWin, integ, subAvg) {
      const params = qs(basePath);
      params.set('file', file);
      params.set('group', grp);
      params.set('x_channel', xCh);
      params.set('y_channel', yCh);
      params.set('average', avg);
      params.set('average_window', avgWin || '5');
      params.set('integrate', integ);
      params.set('subtract_average', subAvg);
      const response = await fetch('/api/plot?' + params.toString());
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || 'Failed to build plot');
      return payload;
    }

    document.getElementById('refreshFiles').addEventListener('click', refreshFiles);
    document.getElementById('refreshFiles2').addEventListener('click', refreshFiles2);
    tdmsFile.addEventListener('change', refreshMetadata);
    tdmsFile2.addEventListener('change', refreshMetadata2);
    group.addEventListener('change', fillChannels);
    group2.addEventListener('change', fillChannels2);
    document.getElementById('plotBtn').addEventListener('click', plotData);
    refreshFiles();
  </script>
</body>
</html>
"""


def run_local_web_app(host='127.0.0.1', port=8000):
    class TdmsWebAppHandler(BaseHTTPRequestHandler):
        def _send_json(self, payload, status_code=200):
            body = json.dumps(payload).encode('utf-8')
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, html):
            body = html.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _get_query_params(self):
            return parse_qs(urlparse(self.path).query)

        def do_GET(self):
            parsed = urlparse(self.path)
            try:
                if parsed.path == '/':
                    self._send_html(WEB_APP_HTML)
                    return

                if parsed.path == '/api/files':
                    query = self._get_query_params()
                    base_path = query.get('base_path', [''])[0]
                    files = _list_tdms_files(base_path)
                    self._send_json({'files': files})
                    return

                if parsed.path == '/api/metadata':
                    query = self._get_query_params()
                    base_path = query.get('base_path', [''])[0]
                    file_name = query.get('file', [''])[0]
                    tdms_file_path = _resolve_tdms_file_path(base_path, file_name)
                    metadata = _read_tdms_metadata(tdms_file_path)
                    self._send_json(metadata)
                    return

                if parsed.path == '/api/plot':
                    query = self._get_query_params()
                    base_path = query.get('base_path', [''])[0]
                    file_name = query.get('file', [''])[0]
                    group_name = query.get('group', [''])[0]
                    x_channel = query.get('x_channel', ['Time'])[0]
                    y_channel = query.get('y_channel', [''])[0]
                    average = query.get('average', ['false'])[0].lower() == 'true'
                    integrate = query.get('integrate', ['false'])[0].lower() == 'true'
                    subtract_average = query.get(
                        'subtract_average', ['false'])[0].lower() == 'true'
                    average_window = int(query.get('average_window', ['5'])[0])
                    tdms_file_path = _resolve_tdms_file_path(base_path, file_name)
                    x_data, y_data = get_plot_data(
                        str(tdms_file_path),
                        group_name,
                        x_channel,
                        y_channel,
                        integrate=integrate,
                        subtract_average=subtract_average,
                        average=average,
                        average_window=average_window
                    )
                    self._send_json({
                        'file': file_name,
                        'group': group_name,
                        'x_channel': x_channel,
                        'y_channel': y_channel,
                        'x': _serialize_axis(x_data),
                        'y': _serialize_axis(y_data)
                    })
                    return

                self._send_json({'error': 'Not found'}, status_code=404)
            except Exception as exc:
                self._send_json({'error': str(exc)}, status_code=400)

    server = ThreadingHTTPServer((host, port), TdmsWebAppHandler)
    print(f'TDMS web app is running at http://{host}:{port}')
    server.serve_forever()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='TDMS local web viewer')
    parser.add_argument('--host', default='127.0.0.1',
                        help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000,
                        help='Port to listen on (default: 8000)')
    args = parser.parse_args()
    run_local_web_app(host=args.host, port=args.port)


# TODO
# DONE 1. Create a new widget subclass: https://kapernikov.com/ipywidgets-with-matplotlib/
# 2. Try to use Jupyter-flex (Voila & Widgets) to make a standalone interactive
# dashboard https://jupyter-flex.netlify.app/voila-ipywidgets/
#   - or we can use the same dashboard as for SHG calculation
