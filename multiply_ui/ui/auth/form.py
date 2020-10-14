from .api import set_earth_data_authentication, set_mundi_authentication, set_scihub_authentication
from ..debug import get_debug_view
from ..info import InfoComponent
from ...util.html import html_element

import ipywidgets as widgets

__author__ = 'Tonio Fincke (Brockmann Consult GmbH)'


def auth_form():
    debug_view = get_debug_view()

    earth_data_info = InfoComponent()
    mundi_info = InfoComponent()
    scihub_user_name = widgets.Text()
    scihub_password = widgets.Text()
    earth_data_user_name = widgets.Text()
    earth_data_password = widgets.Text()
    mundi_access_key_id = widgets.Text()
    mundi_secret_access_key = widgets.Text()

    @debug_view.capture(clear_output=True)
    def set_scihub_auth(*args, **kwargs):
        if scihub_user_name.value == '':
            scihub_info.output_error('No User Name set')
            return
        if scihub_password.value == '':
            scihub_info.output_error('No Password set')
            return
        scihub_info.output_message('Setting SciHub Authentication ...')
        scihub_auth = {'user_name': scihub_user_name.value, 'password': scihub_password.value}
        set_scihub_authentication(scihub_auth, scihub_info.message_func)
        scihub_info.output_message('Earth Data Authentication set')

    set_scihub_button = widgets.Button(description="Set SCIHUB Authentication Credentials")
    set_scihub_button.on_click(set_scihub_auth)

    @debug_view.capture(clear_output=True)
    def set_earth_data_auth(*args, **kwargs):
        if earth_data_user_name.value == '':
            earth_data_info.output_error('No User Name set')
            return
        if earth_data_password.value == '':
            earth_data_info.output_error('No Password set')
            return
        earth_data_info.output_message('Setting Earth Data Authentication ...')
        earth_data_auth = {'user_name': earth_data_user_name.value, 'password': earth_data_password.value}
        set_earth_data_authentication(earth_data_auth, earth_data_info.message_func)
        earth_data_info.output_message('Earth Data Authentication set')

    set_earth_data_button = widgets.Button(description="Set Earth Data Authentication")
    set_earth_data_button.on_click(set_earth_data_auth)

    @debug_view.capture(clear_output=True)
    def set_mundi_auth(*args, **kwargs):
        if mundi_access_key_id.value == '':
            mundi_info.output_error('No Access Key ID set')
            return
        if mundi_secret_access_key.value == '':
            mundi_info.output_error('No Secret Access Key set')
            return
        mundi_info.output_message('Setting MUNDI Authentication ...')
        mundi_auth = {'access_key_id': mundi_access_key_id.value, 'secret_access_key': mundi_secret_access_key.value}
        set_mundi_authentication(mundi_auth, mundi_info.message_func)
        mundi_info.output_message('MUNDI Authentication set')

    set_mundi_button = widgets.Button(description="Set MUNDI Authentication Credentials")
    set_mundi_button.on_click(set_mundi_auth)

    form_item_layout = widgets.Layout(
        display='flex',
        flex_flow='row',
        justify_content='space-between',
    )
    form_items = [
        widgets.Box([widgets.HTML(value=html_element('h2', value='Earth Data Authentication'))], layout=form_item_layout),
        widgets.Box([widgets.Label(value='User name'), earth_data_user_name], layout=form_item_layout),
        widgets.Box([widgets.Label(value='Password'), earth_data_password], layout=form_item_layout),
        widgets.Box([widgets.Label(value=''), set_earth_data_button], layout=form_item_layout),
        widgets.Box([earth_data_info.as_widget()], layout=form_item_layout),
        widgets.Box([widgets.HTML(value=html_element('h2', value='MUNDI Authentication'))], layout=form_item_layout),
        widgets.Box([widgets.Label(value='Access Key ID'), mundi_access_key_id], layout=form_item_layout),
        widgets.Box([widgets.Label(value='Secret Access Key'), mundi_secret_access_key], layout=form_item_layout),
        widgets.Box([widgets.Label(value=''), set_mundi_button], layout = form_item_layout),
        widgets.Box([mundi_info.as_widget()], layout=form_item_layout)
    ]

    form = widgets.Box(form_items, layout=widgets.Layout(
        display='flex',
        flex_flow='column',
        border='solid 1px lightgray',
        align_items='stretch',
        width='50%'
    ))

    return form
