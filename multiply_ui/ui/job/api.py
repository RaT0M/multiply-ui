import random
import string

from .model import Job
from ..debug import get_debug_view
from ..req.model import InputRequestMixin
from ...util.callapi import call_api

URL_BASE = "http://localhost:9090/"
CANCEL_URL = URL_BASE + "multiply/api/jobs/cancel/{}"
GET_JOB_URL = URL_BASE + "multiply/api/jobs/{}"
SUBMIT_PROCESSING_REQUEST_URL = URL_BASE + "multiply/api/jobs/execute"

debug_view = get_debug_view()


def submit_processing_request(request: InputRequestMixin, apply_func, mock=False):
    if mock:
        _submit_processing_request_mock(request, apply_func)
    else:
        _submit_processing_request(request, apply_func)


def _submit_processing_request(request: InputRequestMixin, apply_func):
    def _apply_func(response) -> Job:
        return apply_func(Job(response))
    # TODO: make sure "multiply/api/jobs/execute" can also consume processing requests without input identifiers
    call_api(SUBMIT_PROCESSING_REQUEST_URL, data=request.as_dict(), apply_func=_apply_func)


@debug_view.capture(clear_output=True)
def _submit_processing_request_mock(request: InputRequestMixin, apply_func):
    debug_view.value = ''
    random_id = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
    apply_func(Job(dict(id=random_id,
                        name=request.name,
                        progress=0,
                        status='new',
                        tasks=[
                            {
                                "name": "Collecting static Data",
                                "progress": 0,
                                "status": "new"
                            },
                            {
                                "name": "Collecting Data from 2017-06-01 to 2017-06-10",
                                "progress": 0,
                                "status": "new"
                            }
                        ],
                        )))


def cancel(job_id: str, apply_func):
    def _apply_func(response):
        return apply_func(Job(response))
    call_api(CANCEL_URL.format(job_id), apply_func=_apply_func)


def get_job(job_id: str, apply_func):
    def _apply_func(response) -> Job:
        return apply_func(Job(response))
    call_api(GET_JOB_URL.format(job_id), apply_func=_apply_func)
