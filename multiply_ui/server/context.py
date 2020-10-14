import glob
import inspect
import logging
import os
import shutil
import sys
import yaml
from pathlib import Path
from typing import List

import multiply_data_access.data_access_component
from multiply_core.models import get_forward_models
from multiply_core.observations import INPUT_TYPES
from multiply_core.variables import get_registered_variables
from multiply_post_processing import get_available_indicators, get_post_processor_creators, PostProcessorType
from multiply_prior_engine.vegetation_prior_creator import SUPPORTED_VARIABLES as POSSIBLE_USER_PRIORS
from vm_support import set_earth_data_authentication, set_mundi_authentication, set_scihub_authentication

from .model import Job


logging.getLogger().setLevel(logging.INFO)

CALVALUS_DIR = os.path.abspath(os.path.join(inspect.getfile(Job), os.pardir, os.pardir, os.pardir, os.pardir, 'calvalus-instances'))
sys.path.insert(0, CALVALUS_DIR)
# check out with git clone -b share https://github.com/bcdev/calvalus-instances
# and add the calvalus-instances as content root to project structure
import share.bin.pmserver as pmserver

MULTIPLY_DIR_NAME = '.multiply'
MULTIPLY_CONFIG_FILE_NAME = 'multiply_config.yaml'
MULTIPLY_PLATFORM_PYTHON_CONFIG_KEY = 'platform-env'
WORKING_DIR_CONFIG_KEY = 'working_dir'
WORKFLOWS_DIRS_CONFIG_KEY = 'workflows_dirs'
SCRIPTS_DIRS_CONFIG_KEY = 'scripts_dirs'


def _get_config() -> dict:
    home_dir = str(Path.home())
    multiply_home_dir = '{0}/{1}'.format(home_dir, MULTIPLY_DIR_NAME)
    if not os.path.exists(multiply_home_dir):
        os.mkdir(multiply_home_dir)
    path_to_multiply_config_file = '{0}/{1}'.format(multiply_home_dir, MULTIPLY_CONFIG_FILE_NAME)
    if os.path.exists(path_to_multiply_config_file):
        with open(path_to_multiply_config_file, 'r') as multiply_config_file:
            multiply_config = yaml.safe_load(multiply_config_file)
            return multiply_config
    return {
        WORKING_DIR_CONFIG_KEY: f'{multiply_home_dir}/multiply',
        WORKFLOWS_DIRS_CONFIG_KEY: [],
        SCRIPTS_DIRS_CONFIG_KEY: []
    }


class ServiceContext:

    def __init__(self):
        self._jobs = {}
        self.data_access_component = multiply_data_access.data_access_component.DataAccessComponent()
        self.pm_server = pmserver.PMServer()
        self._python_dist = sys.executable
        config = _get_config()
        if MULTIPLY_PLATFORM_PYTHON_CONFIG_KEY in config.keys():
            self._python_dist = config[MULTIPLY_PLATFORM_PYTHON_CONFIG_KEY]
        if WORKING_DIR_CONFIG_KEY in config.keys():
            self.set_working_dir(config[WORKING_DIR_CONFIG_KEY])
        if WORKFLOWS_DIRS_CONFIG_KEY in config.keys():
            for workflows_dir in config[WORKFLOWS_DIRS_CONFIG_KEY]:
                logging.info(f'adding workflows dir {workflows_dir}')
                self.add_workflows_path(workflows_dir)
        if SCRIPTS_DIRS_CONFIG_KEY in config.keys():
            for scripts_dir in config[SCRIPTS_DIRS_CONFIG_KEY]:
                logging.info(f'adding scripts dir {scripts_dir}')
                self.add_scripts_path(scripts_dir)
        path_to_lib_dir = os.path.abspath(os.path.join(CALVALUS_DIR, 'share/lib'))
        path_to_bin_dir = os.path.abspath(os.path.join(CALVALUS_DIR, 'share/bin'))
        sys.path.insert(0, path_to_lib_dir)
        sys.path.insert(0, path_to_bin_dir)
        path = os.environ['PATH']
        os.environ['PATH'] = f'{path_to_bin_dir}:{path}'

    @staticmethod
    def get_available_forward_models() -> List[dict]:
        dict_list = []
        forward_models = get_forward_models()
        for model in forward_models:
            dict_list.append({
                "id": model.id,
                "name": model.name,
                "description": model.description,
                "modelAuthors": model.authors,
                "modelUrl": model.url,
                "inputType": model.model_data_type,
                "type": model.inference_engine_type,
                "requiredPriors": model.required_priors,
                "variables": model.variables
            })
        return dict_list

    @staticmethod
    def get_available_input_types() -> List[dict]:
        input_types = []
        for input_type in INPUT_TYPES:
            input_types.append({"id": input_type, "name": INPUT_TYPES[input_type]["input_data_type_name"],
                                "timeRange": INPUT_TYPES[input_type]["timeRange"]})
        return input_types

    @staticmethod
    def get_available_variables() -> List[dict]:
        dict_list = []
        variables = get_registered_variables()
        for variable in variables:
            dict_list.append({
                "id": variable.short_name,
                "name": variable.display_name,
                "unit": variable.unit,
                "description": variable.description,
                "valueRange": variable.range,
                "mayBeUserPrior": variable.short_name in POSSIBLE_USER_PRIORS,
                "applications": variable.applications
            })
        return dict_list

    @staticmethod
    def get_available_post_processor_indicators() -> List[dict]:
        dict_list = []
        indicators = get_available_indicators()
        for indicator in indicators:
            dict_list.append({
                "id": indicator.short_name,
                "name": indicator.display_name,
                "unit": indicator.unit,
                "description": indicator.description,
                "valueRange": indicator.range,
                "mayBeUserPrior": False,
                "applications": indicator.applications
            })
        return dict_list

    @staticmethod
    def get_available_post_processors() -> List[dict]:
        dict_list = []
        post_processor_creators = get_post_processor_creators()
        for post_processor_creator in post_processor_creators:
            indicator_descriptions = post_processor_creator.get_indicator_descriptions()
            indicator_names = []
            for indicator_description in indicator_descriptions:
                indicator_names.append(indicator_description.short_name)
            type = 0
            if post_processor_creator.get_type() == PostProcessorType.EO_DATA_POST_PROCESSOR:
                type = 1
            dict_list.append({
                "name": post_processor_creator.get_name(),
                "description": post_processor_creator.get_description(),
                "type": type,
                "inputTypes": post_processor_creator.get_required_input_data_types(),
                "indicators": indicator_names,
            })
        return dict_list

    @staticmethod
    def set_earth_data_authentication(username: str, password: str):
        set_earth_data_authentication(username, password)

    @staticmethod
    def set_scihub_authentication(username: str, password: str):
        set_scihub_authentication(username, password)

    @staticmethod
    def set_mundi_authentication(access_key_id: str, secret_access_key: str):
        set_mundi_authentication(access_key_id, secret_access_key)

    def set_working_dir(self, working_dir: str):
        # todo remove previous working dirs
        self._working_dir = working_dir
        sys.path.insert(0, working_dir)
        os.environ['PATH'] += f':{working_dir}'

    @property
    def working_dir(self) -> str:
        return self._working_dir

    @staticmethod
    def add_workflows_path(workflows_path: str):
        sys.path.insert(0, workflows_path)
        os.environ['PATH'] += f':{workflows_path}'

    def add_scripts_path(self, scripts_path: str):
        sys.path.insert(0, scripts_path)
        scripts = glob.glob(f'{scripts_path}/*.py')
        for script in scripts:
            read_file = open(script, 'r+')
            content = read_file.read()
            content = content.replace('{PYTHON}', self._python_dist)
            read_file.close()
            write_file = open(script, 'w')
            write_file.write(content)
            write_file.close()
        os.environ['PATH'] += f':{scripts_path}'

    def get_job(self, id: str):
        for job in self.pm_server.queue:
            if job.request['requestId'] == id:
                return job

    def clear(self, type: str):
        if type == 'cache':
            self.data_access_component.clear_caches()
        elif type == 'working':
            working_dirs = glob.glob('/data/working_dirs/*')
            for working_dir in working_dirs:
                shutil.rmtree(working_dir)
        elif type == 'archive':
            archive_dirs = glob.glob('/data/archive/*')
            for archive_dir in archive_dirs:
                shutil.rmtree(archive_dir)
        elif type == 'aux':
            aux_files = glob.glob('/data/auxiliary/**', recursive=True)
            for aux_file in aux_files:
                if os.path.isfile(aux_file) and not aux_file.endswith('bucket_info.json'):
                    os.remove(aux_file)
