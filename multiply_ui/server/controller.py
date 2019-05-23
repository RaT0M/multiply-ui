import json
import pkg_resources
import os
# check out with git clone -b share https://github.com/bcdev/calvalus-instances
# and add the calvalus-instances as content root to project structure
from share.lib.pmonitor import PMonitor


def get_parameters(ctx):
    json_text = pkg_resources.resource_string(__name__, "resources/processing-parameters.json")
    return json.loads(json_text)


def get_inputs(ctx, parameters):
    time_range = parameters["timeRange"]
    (minLon, minLat, maxLon, maxLat) = parameters["bbox"].split(",")
    region_wkt = "POLYGON(({} {},{} {},{} {},{} {},{} {}))".format(minLon, minLat, maxLon, minLat, maxLon, maxLat,
                                                                   minLon, maxLat, minLon, minLat)
    input_types = parameters["inputTypes"]
    parameters["inputIdentifiers"] = {}
    for input_type in input_types:
        data_set_meta_infos = ctx.data_access_component.query(region_wkt, time_range[0], time_range[1], input_type)
        parameters["inputIdentifiers"][input_type] = [entry._identifier for entry in data_set_meta_infos]
    return parameters

def submit_request(ctx, request):
    mangled_name = request['name'].replace(' ', '_')
    id = mangled_name  # TODO generate simple unique IDs
    workdir_root = '/data'  # TODO get path from some configuration
    workdir = workdir_root + '/' + id
    pm_request_file = workdir + '/' + mangled_name

    pm_request = _pm_request_of(request, workdir)
    os.makedirs(workdir)
    with open(pm_request_file, "w") as f:
        json.dump(pm_request, f)
    pm_request["requestFile"] = pm_request_file

    job = ctx.pm_server.submit_request(request)
    job_dict = {}
    job_dict['request'] = job.request
    job_dict['workflow'] = _pm_workflow_of(job.pm)
    job_dict['status'] = job.status

def _pm_request_of(request, workdir):
    template_text = pkg_resources.resource_string(__name__, "resources/pm_request_template.json")
    pm_request = json.loads(template_text)
    pm_request['requestName'] = request['name']
    pm_request['data_root'] = workdir
    (minLon, minLat, maxLon, maxLat) = request["bbox"].split(",")
    region_wkt = "POLYGON(({} {},{} {},{} {},{} {},{} {}))".format(minLon, minLat, maxLon, minLat, maxLon, maxLat,
                                                                   minLon, maxLat, minLon, minLat)
    pm_request['General']['roi'] = region_wkt
    pm_request['General']['start_time'] = request['timeRange'][0][:8]
    pm_request['General']['end_time'] = request['timeRange'][1][:8]
    pm_request['General']['time_interval'] = request['timeStep']
    pm_request['General']['spatial_resolution'] = request['spatialResolution']
    pm_request['Inference']['parameters'] = [ parameter[0] for parameter in request['parameters']]
    pm_request['Inference']['time_interval'] = request['timeStep']
    pm_request['Prior']['output_directory'] = workdir + '/priors'
    return pm_request

def _pm_workflow_of(pm):
    accu = []
    for l in pm.commands:
        accu.append({"step": l, "status": "succeeded"})
    for l in pm._failed:
        accu.append({"step": l, "status": "failed"})
    for l in pm._running:
        accu.append({"step": l, "status": "running"})
    for r in pm._backlog:
        l = '{0} {1} {2} {3}\n'.format(PMonitor.Args.get_call(r.args),
                                       ' '.join(PMonitor.Args.get_parameters(r.args)),
                                       ' '.join(PMonitor.Args.get_inputs(r.args)),
                                       ' '.join(PMonitor.Args.get_outputs(r.args)))
        accu.append({"step": l, "status": "initial"})
    return accu
