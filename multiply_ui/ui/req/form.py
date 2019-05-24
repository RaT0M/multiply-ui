import datetime
from typing import List

import IPython
import ipywidgets as widgets

from .api import fetch_inputs
from .model import InputRequest, ProcessingRequest
from ..params.model import ProcessingParameters
from ...util.html import html_element, html_table

_NUM_REQUESTS = 0


def sel_params_form(processing_parameters: ProcessingParameters, mock=False):
    fetch_inputs_func = fetch_inputs_mock if mock else fetch_inputs

    form_item_layout = widgets.Layout(
        display='flex',
        flex_flow='row',
        justify_content='space-between',
    )
    var_checks_layout = widgets.Layout(
        display='flex',
        flex_flow='row',
        justify_content='center',
    )

    variables_box = _get_checkbox_list(processing_parameters.variables.ids)
    forward_models_box = _get_checkbox_list(processing_parameters.forward_models.ids)

    # output_variables =

    global _NUM_REQUESTS
    _NUM_REQUESTS += 1
    request_name = widgets.Text(f'My request #{_NUM_REQUESTS}')
    python_var_name = widgets.Text(value='req')

    start_date = widgets.DatePicker(value=datetime.datetime(year=2010, month=1, day=1))
    end_date = widgets.DatePicker(value=datetime.datetime(year=2019, month=1, day=1))

    def format_angle(a):
        if a < 0:
            return f" {a} "
        if a > 0:
            return f" +{a} "
        return " 0 "

    lon_range = widgets.SelectionRangeSlider(
        options=[(format_angle(i - 180), i) for i in range(0, 361)],
        index=(0, 360)
    )

    lat_range = widgets.SelectionRangeSlider(
        options=[(format_angle(i - 90), i) for i in range(0, 181)],
        index=(0, 180)
    )

    spatial_resolution = widgets.Dropdown(
        options=['10', '20', '60', '300'],
        value='60',
        disabled=False,
    )

    time_steps = widgets.Dropdown(
        options=['1d', '8d', '10d', 'cal. week', 'cal. month'],
        value='8d',
        disabled=False,
    )

    # output = widgets.HTML(layout=dict(border='2px solid lightgray', padding='0.5em'))
    output = widgets.HTML()

    # noinspection PyUnusedLocal
    def handle_new_button_clicked(*args, **kwargs):
        req_var_name = python_var_name.value or None
        if req_var_name and not req_var_name.isidentifier():
            output.value = html_element('h5',
                                        att=dict(style='color:red'),
                                        value=f'Error: request name must be a valid Python identifier')
            return

        # TODO: infer input types
        input_types = ['S2_L1C']
        x1, x2 = lon_range.value
        y1, y2 = lat_range.value

        inputs_request = InputRequest(dict(
            name=request_name.value,
            timeRange=[start_date.value, end_date.value],
            bbox=f'{x1},{y1},{x2},{y2}',
            inputTypes=input_types,
        ))

        def handle_processing_request(processing_request: ProcessingRequest):

            input_identifiers = processing_request.inputs
            data_rows = []
            for input_type, input_ids in input_identifiers.as_dict().items():
                data_rows.append([input_type, len(input_ids)])

            result_html = html_table(data_rows, header_row=['Input Type', 'Number of inputs found'])

            # insert shall variable whose value is processing_request
            # users can later call the GUI with that object to edit it
            if req_var_name:
                shell = IPython.get_ipython()
                shell.push({req_var_name: processing_request}, interactive=True)
                var_name_html = html_element('p',
                                             value=f'Note: a new processing request has been '
                                             f'stored in variable <code>{req_var_name}</code>.')
                result_html = html_element('div',
                                           value=result_html + var_name_html)

            output.value = result_html

        output.value = html_element('h5', value='Fetching results...')
        fetch_inputs_func(inputs_request, apply_func=handle_processing_request)

    new_button = widgets.Button(description="New Request", icon="search")
    new_button.on_click(handle_new_button_clicked)
    form_items = [
        widgets.Box([widgets.Label(value='Output variables')], layout=form_item_layout),
        widgets.Box([variables_box], layout=var_checks_layout),
        widgets.Box([widgets.Label(value='Forward models')], layout=form_item_layout),
        widgets.Box([forward_models_box], layout=var_checks_layout),
        widgets.Box([widgets.Label(value='Start date'), start_date], layout=form_item_layout),
        widgets.Box([widgets.Label(value='End date'), end_date], layout=form_item_layout),
        widgets.Box([widgets.Label(value='Time steps'), time_steps], layout=form_item_layout),
        widgets.Box([widgets.Label(value='Longitude'), lon_range], layout=form_item_layout),
        widgets.Box([widgets.Label(value='Latitude'), lat_range], layout=form_item_layout),
        widgets.Box([widgets.Label(value='Resolution (m)'), spatial_resolution], layout=form_item_layout),
        widgets.Box([widgets.Label(value='Request name'), request_name], layout=form_item_layout),
        widgets.Box([widgets.Label(value='Python identifier'), python_var_name], layout=form_item_layout),
        widgets.Box([widgets.Label(value=''), new_button], layout=form_item_layout),
        widgets.Box([output], layout=form_item_layout),
    ]

    form = widgets.Box(form_items, layout=widgets.Layout(
        display='flex',
        flex_flow='column',
        border='solid 1px lightgray',
        align_items='stretch',
        width='50%'
    ))

    return form


def _get_checkbox_list(ids: List[str]) -> widgets.HBox:
    num_cols = 4
    # noinspection PyUnusedLocal
    v_box_item_lists = [[] for i in range(num_cols)]
    index = 0
    for var_id in ids:
        col = index % num_cols
        v_box_item_lists[col].append(widgets.Checkbox(
            value=False,
            description=var_id,
            disabled=False
        ))
        index += 1

    v_boxes = []
    for v_box_item_list in v_box_item_lists:
        v_boxes.append(widgets.VBox(v_box_item_list))
    return widgets.HBox(v_boxes)


_debug_view = widgets.Output(layout={'border': '2px solid red'})

_shell = IPython.get_ipython()
_shell.push({'debug_view': _debug_view}, interactive=True)


@_debug_view.capture(clear_output=True)
def fetch_inputs_mock(input_request: InputRequest, apply_func):
    _debug_view.value = ''
    import time
    time.sleep(3)
    input_identifiers = {input_type: [f'iid-{i}' for i in range(10)] for input_type in input_request.input_types}
    processing_request_data = input_request.as_dict()
    processing_request_data.update(dict(inputIdentifiers=input_identifiers))
    apply_func(ProcessingRequest(processing_request_data))
