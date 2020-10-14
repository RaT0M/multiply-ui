import concurrent.futures
import json
import logging
import traceback

import tornado.escape
import tornado.web

from .context import ServiceContext
from multiply_ui.server import controller
from typing import Optional

logging.getLogger().setLevel(logging.INFO)
_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=8)


# noinspection PyAbstractClass
class ServiceRequestHandler(tornado.web.RequestHandler):

    @property
    def ctx(self) -> ServiceContext:
        # noinspection PyProtectedMember
        return self.application._ctx

    @property
    def base_url(self):
        return self.request.protocol + '://' + self.request.host

    def set_default_headers(self):
        """Override Tornado's default headers to allow for CORS."""
        self.set_header('Access-Control-Allow-Origin',
                        '*')
        self.set_header('Access-Control-Allow-Methods',
                        'GET,'
                        'PUT,'
                        'DELETE,'
                        'OPTIONS')
        self.set_header('Access-Control-Allow-Headers',
                        'x-requested-with,'
                        'access-control-allow-origin,'
                        'authorization,'
                        'content-type')

    # noinspection PyUnusedLocal
    def options(self, *args, **kwargs):
        """Override Tornado's default OPTIONS handler."""
        self.set_status(204)
        self.finish()

    def write_error(self, status_code, **kwargs):
        """Override Tornado's default error handler."""
        self.set_header('Content-Type', 'application/json')
        # if self.settings.get("serve_traceback") and "exc_info" in kwargs:
        if "exc_info" in kwargs:
            # in debug mode, try to send a traceback
            lines = []
            for line in traceback.format_exception(*kwargs["exc_info"]):
                lines.append(line)
            self.finish(json.dumps({
                'error': {
                    'code': status_code,
                    'message': self._reason,
                    'traceback': lines,
                }
            }, indent=2))
        else:
            self.finish(json.dumps({
                'error': {
                    'code': status_code,
                    'message': self._reason,
                }
            }, indent=2))

    def get_body_as_json_object(self, name="JSON object"):
        """Utility to get the body argument as JSON object. """
        try:
            return tornado.escape.json_decode(self.request.body)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            raise tornado.web.HTTPError(status_code=400,
                                        log_message=f"Invalid or missing {name} in request body") from e


# noinspection PyAbstractClass
class ClearHandler(ServiceRequestHandler):
    def get(self, clear_type: str):
        self.ctx.clear(clear_type)


# noinspection PyAbstractClass
class GetParametersHandler(ServiceRequestHandler):
    def get(self):
        self.set_header('Content-Type', 'application/json')
        parameters = controller.get_parameters(self.ctx)
        json.dump(parameters, self)


# noinspection PyAbstractClass
class GetInputsHandler(ServiceRequestHandler):
    def post(self):
        self.set_header('Content-Type', 'application/json')
        parameters = self.get_body_as_json_object()
        request = controller.get_inputs(self.ctx, parameters)
        json.dump(request, self)
        self.finish()


# noinspection PyAbstractClass
class ExecuteJobsHandler(ServiceRequestHandler):
    def post(self):
        self.set_header('Content-Type', 'application/json')
        request = self.get_body_as_json_object()
        job = controller.submit_request(self.ctx, request)
        json.dump(job, self)
        self.finish()


# noinspection PyAbstractClass
class GetJobHandler(ServiceRequestHandler):
    def get(self, job_id: str):
        self.set_header('Content-Type', 'application/json')
        job = controller.get_job(self.ctx, job_id)
        json.dump(job, self)
        self.finish()


# noinspection PyAbstractClass
class CancelHandler(ServiceRequestHandler):
    def get(self, job_id: str):
        self.set_header('Content-Type', 'application/json')
        controller.cancel(self.ctx, job_id)


# noinspection PyAbstractClass
class PostEarthDataAuthHandler(ServiceRequestHandler):
    def post(self):
        self.set_header('Content-Type', 'application/json')
        parameters = self.get_body_as_json_object()
        controller.set_earth_data_authentication(self.ctx, parameters)


# noinspection PyAbstractClass
class PostSciHubAuthHandler(ServiceRequestHandler):
    def post(self):
        self.set_header('Content-Type', 'application/json')
        parameters = self.get_body_as_json_object()
        controller.set_scihub_authentication(self.ctx, parameters)


# noinspection PyAbstractClass
class PostMundiAuthHandler(ServiceRequestHandler):
    def post(self):
        self.set_header('Content-Type', 'application/json')
        parameters = self.get_body_as_json_object()
        controller.set_mundi_authentication(self.ctx, parameters)


# noinspection PyAbstractClass
class VisualizeHandler(ServiceRequestHandler):
    def get(self, job_id: str):
        self.set_header('Content-Type', 'application/json')
        ip_dict = controller.visualize(self.ctx, job_id)
        json.dump(ip_dict, self)
        self.finish()
