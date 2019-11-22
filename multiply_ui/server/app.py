import tornado.web

from .handlers import GetParametersHandler, GetInputsHandler, ExecuteHandler, ListHandler, StatusHandler, \
    CancelHandler, ResultsFromJobHandler, ResultHandler, ResultsOpenHandler, PostEarthDataAuthHandler, \
    PostMundiAuthHandler


def new_application():
    return tornado.web.Application([
        (r"/multiply/api/processing/parameters", GetParametersHandler),
        (r"/multiply/api/processing/inputs", GetInputsHandler),
        (r"/multiply/api/auth/earthdata", PostEarthDataAuthHandler),
        (r"/multiply/api/auth/mundi", PostMundiAuthHandler),
        (r"/jobs/execute", ExecuteHandler),
        (r"/jobs/list", ListHandler),
        (r"/jobs/([0-9]+)", StatusHandler),
        (r"/jobs/cancel/([0-9]+)", CancelHandler),
        (r"/jobs/results/([0-9]+)", ResultsFromJobHandler),
        (r"/result/([0-9]+)", ResultHandler),
        (r"/results/open/([0-9]+)", ResultsOpenHandler)
    ])
