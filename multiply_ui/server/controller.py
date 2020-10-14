import datetime
import json
import logging
import pkg_resources
import os
import shutil
import subprocess
import urllib.request
import webbrowser
from .context import ServiceContext #import to ensure calvalus-instances is added to system path
from multiply_core.util import get_num_tiles, get_time_from_string
# check out with git clone -b share https://github.com/bcdev/calvalus-instances
# and add the calvalus-instances as content root to project structure
from share.lib.pmonitor import PMonitor
from shapely.wkt import loads
from typing import Dict, List, Tuple

logging.getLogger().setLevel(logging.INFO)


def get_parameters(ctx):
    input_type_dicts = ctx.get_available_input_types()
    variable_dicts = ctx.get_available_variables()
    forward_model_dicts = ctx.get_available_forward_models()
    post_processor_dicts = ctx.get_available_post_processors()
    indicator_dicts = ctx.get_available_post_processor_indicators()
    parameters = {
        "inputTypes": input_type_dicts,
        "variables": variable_dicts,
        "forwardModels": forward_model_dicts,
        "postProcessors": post_processor_dicts,
        "indicators": indicator_dicts
    }
    return parameters


def get_inputs(ctx, parameters):
    time_range = parameters["timeRange"]
    region_wkt = parameters["roi"]
    input_types = parameters["inputTypes"]
    parameters["inputIdentifiers"] = {}
    for input_type in input_types:
        data_set_meta_infos = ctx.data_access_component.query(region_wkt, time_range[0], time_range[1], input_type)
        parameters["inputIdentifiers"][input_type] = [entry._identifier for entry in data_set_meta_infos]
    return parameters


def submit_request(ctx, request) -> Dict:
    mangled_name = request['name'].replace(' ', '_')
    id = mangled_name
    job = ctx.get_job(mangled_name)
    index = 0
    while job is not None:
        id = f'{mangled_name}_{index}'
        job = ctx.get_job(id)
        index += 1
    workdir_root = ctx.working_dir
    logging.info(f'working dir root from context {workdir_root}')
    workdir = workdir_root + '/' + id
    pm_request_file = f'{workdir}/{mangled_name}.json'

    pm_request = _pm_request_of(request, workdir, id)
    if os.path.exists(workdir):
        shutil.rmtree(workdir)
    os.makedirs(workdir)
    with open(pm_request_file, "w") as f:
        json.dump(pm_request, f)
    pm_request["requestFile"] = pm_request_file

    job = ctx.pm_server.submit_request(pm_request)
    return _get_job_dict(job, id, request['name'])


def _translate_step(step: str) -> str:
    step_parts = step.split(" ")
    if step_parts[0] == "combine_biophys_outputs.py":
        return 'Assembling results from inference'
    if step_parts[0] == "combine_hres_biophys_outputs.py":
        return 'Assembling results from S2 inference'
    if step_parts[0] == "create_s1_kaska_inference_output_files.py":
        return f'Creating Output Files for S1 Kaska Inference for time step from {step_parts[2]} to {step_parts[3]}'
    if step_parts[0] == "create_s2_kaska_inference_output_files.py":
        return f'Creating Output Files for S2 Kaska Inference for time step from {step_parts[2]} to {step_parts[3]}'
    if step_parts[0] == "data_access_get_static.py":
        return f'Retrieving data required for all time steps of S2-Pre-Processing'
    if step_parts[0] == "data_access_put_s2_l2.py":
        return f'Storing S2 Pre-processing results of time step from {step_parts[2]} to {step_parts[3]}'
    if step_parts[0] == "determine_s1_priors.py":
        return f'Assembling Priors for S1 Retrieval for time step from {step_parts[2]} to {step_parts[3]}'
    if step_parts[0] == "get_data_for_s1_preprocessing.py":
        return f'Retrieving SAR data for time step from {step_parts[2]} to {step_parts[3]}'
    if step_parts[0] == "get_data_for_s2_preprocessing.py":
        return f'Retrieving S2 data for time step from {step_parts[2]} to {step_parts[3]}'
    if step_parts[0] == "infer_s2_kafka.py":
        return f'Inferring variables from S2 inference for time step from {step_parts[2]} to {step_parts[3]}'
    if step_parts[0] == "infer_s1_kaska.py":
        return f'Inferring variables from S1 inference for tile {step_parts[4]}, {step_parts[5]} and time step from {step_parts[2]} to {step_parts[3]}'
    if step_parts[0] == "infer_s2_kaska.py":
        return f'Inferring variables from S2 inference for tile {step_parts[4]}, {step_parts[5]}'
    if step_parts[0] == "preprocess_s1.py":
        return 'Preprocessing S1 data for all time steps'
    if step_parts[0] == "preprocess_s2.py":
        return f'Preprocessing S2 Data for time step from {step_parts[2]} to {step_parts[3]}'
    if step_parts[0] == "post_process.py":
        return 'Conduct post-processing'
    if step_parts[0] == "retrieve_s2_priors.py":
        return f'Retrieving priors for S2 inference for time step from {step_parts[2]} to {step_parts[3]}'
    if step_parts[0] == "stack_s1.py":
        return f'Creating S1 Stack for time step from {step_parts[2]} to {step_parts[3]}'
    return step


def _translate_status(pm_status: str) -> str:
    if pm_status == 'ERROR' or pm_status == 'FAILED':
        return 'failed'
    if pm_status == 'RUNNING':
        return 'running'
    if pm_status == 'DONE' or pm_status == 'SUCCEEDED' or pm_status == 'SUCCESS':
        return 'succeeded'
    if pm_status == 'CANCELLED':
        return 'cancelled'
    if pm_status == 'INITIAL':
        return 'new'


def _pm_request_of(request, workdir: str, id: str) -> Dict:
    template_text = pkg_resources.resource_string(__name__, "resources/pm_request_template.json")
    pm_request = json.loads(template_text)
    pm_request['requestName'] = f"{workdir}/{request['name']}"
    pm_request['requestId'] = id
    pm_request['productionType'] = _determine_workflow(request)
    pm_request['data_root'] = workdir
    pm_request['simulation'] = pm_request['simulation'] == 'True'
    pm_request['log_dir'] = f'{workdir}/log'
    pm_request['General']['roi'] = request['roi']
    pm_request['General']['start_time'] = \
        datetime.datetime.strftime(get_time_from_string(request['timeRange'][0]), '%Y-%m-%d')
    pm_request['General']['end_time'] = \
        datetime.datetime.strftime(get_time_from_string(request['timeRange'][1]), '%Y-%m-%d')
    pm_request['General']['time_interval'] = request['timeStep']
    pm_request['General']['spatial_resolution'] = request['spatialResolution']
    pm_request['General']['tile_width'] = 512
    pm_request['General']['tile_height'] = 512
    num_tiles_x, num_tiles_y = _get_num_tiles_of_request(request, 512, 512)
    pm_request['General']['num_tiles_x'] = num_tiles_x
    pm_request['General']['num_tiles_y'] = num_tiles_y
    pm_request['Inference']['time_interval'] = request['timeStep']
    forward_models = []
    for model_dict in request['forwardModels']:
        model = {"name": model_dict["name"],
                 "type": model_dict["type"],
                 "data_type": model_dict["modelDataType"],
                 "required_priors": [prior for prior in model_dict["requiredPriors"]],
                 "output_parameters": [parameter for parameter in model_dict["outputParameters"]]}
        forward_models.append(model)
    pm_request['Inference']['forward_models'] = forward_models
    pm_request['Prior']['output_directory'] = workdir + '/priors'
    for user_prior_dict in request['userPriors']:
        if 'mu' in user_prior_dict:
            pm_request['Prior'][user_prior_dict['name']] = {'user': {'mu': user_prior_dict['mu']}}
        if 'unc' in user_prior_dict:
            if 'user' not in pm_request['Prior'][user_prior_dict['name']]:
                pm_request['Prior'][user_prior_dict['name']]['user'] = {}
            pm_request['Prior'][user_prior_dict['name']]['user']['unc'] = user_prior_dict['unc']
    if 's1TemporalFilter' in request:
        pm_request['SAR']['speckle_filter']['multi_temporal']['files'] = request['s1TemporalFilter']
        (min_lon, min_lat, max_lon, max_lat) = loads(request['roi']).bounds
        pm_request['SAR']['region']['ul']['lat'] = max_lat
        pm_request['SAR']['region']['ul']['lon'] = min_lon
        pm_request['SAR']['region']['lr']['lat'] = min_lat
        pm_request['SAR']['region']['lr']['lon'] = max_lon
        pm_request['SAR']['year'] = datetime.datetime.strftime(get_time_from_string(request['timeRange'][0]), '%Y')
    if 's2ComputeRoi' in request:
        pm_request['S2-PreProcessing']['compute_only_roi'] = request['s2ComputeRoi']
    if 'postProcessors' in request:
        post_processor_list = []
        for post_processor_dict in request['postProcessors']:
            pp_dict = {}
            pp_dict['name'] = post_processor_dict['name']
            pp_dict['type'] = post_processor_dict['type']
            pp_dict['input_types'] = [input_type for input_type in post_processor_dict["inputTypes"]]
            pp_dict['indicator_names'] = [indicator_name for indicator_name in post_processor_dict["indicatorNames"]]
            pp_dict['variable_names'] = [variable_name for variable_name in post_processor_dict["variableNames"]]
            post_processor_list.append(pp_dict)
        pm_request['post_processing']['post_processors'] = post_processor_list
    return pm_request


def _get_num_tiles_of_request(request, tile_width, tile_height) -> Tuple:
    roi = request['roi']
    spatial_resolution = request['spatialResolution']
    return get_num_tiles(spatial_resolution=spatial_resolution, roi=roi, tile_width=tile_width, tile_height=tile_height)


def _determine_workflow(request) -> str:
    if "productionType" in request:
        return request["productionType"]
    return 'multiply-full'


def _pm_workflow_of(pm) -> List:
    accu = []
    backlog = pm._backlog.copy()
    running = pm._running.copy()
    commands = pm._commands.copy()
    cancelled = pm._cancelled.copy()
    failed = pm._failed.copy()
    for r in backlog:
        l = '{0} {1} {2} {3}\n'.format(PMonitor.Args.get_call(r.args),
                                       ' '.join(PMonitor.Args.get_parameters(r.args)),
                                       ' '.join(PMonitor.Args.get_inputs(r.args)),
                                       ' '.join(PMonitor.Args.get_outputs(r.args)))
        accu.append({"step": l, "status": "initial", "progress": 0, "logs": []})
    for l in running:
        accu.append({"step": l, "status": "running", "progress": pm.get_progress(l), "logs": pm.get_logs(l)})
    for l in commands:
        accu.append({"step": l, "status": "succeeded", "progress": 100, "logs": pm.get_logs(l)})
    for l in cancelled:
        accu.append({"step": l, "status": "cancelled", "progress": pm.get_progress(l), "logs": pm.get_logs(l)})
    for l in failed:
        accu.append({"step": l, "status": "failed", "progress": pm.get_progress(l), "logs": pm.get_logs(l)})
    return accu


def set_earth_data_authentication(ctx, parameters):
    ctx.set_earth_data_authentication(parameters['user_name'], parameters['password'])

def set_scihub_authentication(ctx, parameters):
    ctx.set_scihub_authentication(parameters['user_name'], parameters['password'])

def set_mundi_authentication(ctx, parameters):
    ctx.set_mundi_authentication(parameters['access_key_id'], parameters['secret_access_key'])


def get_job(ctx, id: str) -> Dict:
    job = ctx.get_job(id)
    request_name = job.request['requestName'].split('/')[-1]
    return _get_job_dict(job, id, request_name)


def _get_job_dict(job, request_id: str, request_name: str):
    job_dict = {'id': request_id, 'name': request_name, 'status': _translate_status(job.status)}
    tasks = _pm_workflow_of(job.pm)
    job_dict['tasks'] = []
    job_progress = 0
    for task in tasks:
        status = task['status']
        progress = task['progress']
        job_progress += progress
        task_dict = {
            'name': _translate_step(task['step']),
            'status': status,
            'progress': progress,
            'logs': task['logs']
        }
        job_dict['tasks'].append(task_dict)
    job_dict['progress'] = int(job_progress / len(tasks)) if len(tasks) > 0 else 100
    return job_dict


def cancel(ctx, id: str):
    job = ctx.get_job(id)
    job.pm.cancel()


def visualize(ctx, id: str) -> Dict:
    job = ctx.get_job(id)
    output_dir = os.path.join(job.pm._data_root, 'biophys')
    subprocess.Popen(['/software/miniconda/envs/multiply_vis/bin/python',
                      '/software/MULTIPLYVisualisation/MVis.py',
                      output_dir, 'False', '8080'])
    # server = ''
    # while server == '':
    #     line = str(process.stdout.readline())
    #     if line.find("Running on") >= 0:
    #         server = line.split(" ")[-1].split('\\')[0]
    # process.stdout.close()
    external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    return {'ip': f'http://{external_ip}/8080'}
