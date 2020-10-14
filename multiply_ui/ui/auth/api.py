from typing import List
from ...util.callapi import call_api

__author__ = 'Tonio Fincke (Brockmann Consult GmbH)'

URL_BASE = "http://localhost:9090/"

POST_EARTH_AUTH_URL = URL_BASE + "multiply/api/auth/earthdata"
POST_MUNDI_AUTH_URL = URL_BASE + "multiply/api/auth/mundi"
POST_SCIHUB_AUTH_URL = URL_BASE + "multiply/api/auth/scihub"


def _write_to_command_line(message: str, stack_trace: List[str]=[]):
    print(message)
    for line in stack_trace:
        print(line)


def set_earth_data_authentication(earth_data_auth: dict, message_func=_write_to_command_line):
    return call_api(POST_EARTH_AUTH_URL, data=earth_data_auth, message_func=message_func)


def set_mundi_authentication(mundi_auth: dict, message_func=_write_to_command_line):
    return call_api(POST_MUNDI_AUTH_URL, data=mundi_auth, message_func=message_func)


def set_scihub_authentication(scihub_auth: dict, message_func=_write_to_command_line):
    return call_api(POST_SCIHUB_AUTH_URL, data=scihub_auth, message_func=message_func)
