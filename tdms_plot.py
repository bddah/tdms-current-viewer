from os import listdir
from re import match
from time import strftime, localtime

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
                    with TdmsFile.open(self.tdms_file_path) as tdms_file:
                        # prepare the Y channel data
                        if integrate_checkbox.value == True:
                            # integrate the signal
                            # we always integrate the raw data, so the average checkbox
                            # is not checked here
                            tmp_y = tdms_file[self.group][self.y_channel][:]
                            tmp_x = tdms_file[self.group][self.y_channel].time_track()
                            if substract_checkbox.value == True:
                                y_data = cumulative_trapezoid(
                                    tmp_y-np.mean(tmp_y), tmp_x, initial=0)
                            else:
                                y_data = cumulative_trapezoid(tmp_y, tmp_x, initial=0)
                        elif average_checkbox.value == True:
                            # calculate the smoothed signal,
                            # we use poly order 3 by default
                            # we need positive values
                            window = abs(average_value.value)
                            if (window % 2 == 0):
                                window += 1  # we need odd numbers
                            if (window < 3):
                                window = 5 # window must be larger than polynom order
                            # user should know the real window value:
                            average_value.value = window
                            y_data = savgol_filter(
                                                tdms_file[self.group]
                                                [self.y_channel][:],
                                                window, 3, mode='nearest')
                        else:
                            # use the raw data in this case
                            y_data = tdms_file[self.group][self.y_channel][:]
                        # if the X channel is Time - just use the time_track to avoid
                        # problems with dates format
                        if (x_channel.index == 0):
                            x_data = tdms_file[self.group][self.y_channel].time_track()
                        else:
                            x_data = tdms_file[self.group][self.x_channel][:]
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

if __name__ == "__main__":
    print('''This is a module containing widgets for working with TDMS files.
          Run tdms_plot.main_widget() to start widget.''')


# TODO
# DONE 1. Create a new widget subclass: https://kapernikov.com/ipywidgets-with-matplotlib/
# 2. Try to use Jupyter-flex (Voila & Widgets) to make a standalone interactive
# dashboard https://jupyter-flex.netlify.app/voila-ipywidgets/
#   - or we can use the same dashboard as for SHG calculation
