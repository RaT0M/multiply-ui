import glob
import inspect
import os
import sys
import yaml
from pathlib import Path
from typing import Optional, List

from .model import Job

import multiply_data_access.data_access_component
CALVALUS_DIR = os.path.join(inspect.getfile(Job), os.pardir, os.pardir, os.pardir, os.pardir, 'calvalus-instances')
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
        multiply_config = yaml.safe_load(path_to_multiply_config_file)
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
        self._restrict_to_mundi_datastore()
        self.pm_server = pmserver.PMServer()
        config = _get_config()
        if WORKING_DIR_CONFIG_KEY in config.keys():
            self.set_working_dir(config[WORKING_DIR_CONFIG_KEY])
        if WORKFLOWS_DIRS_CONFIG_KEY in config.keys():
            for workflows_dir in config[WORKFLOWS_DIRS_CONFIG_KEY]:
                self.add_workflows_path(workflows_dir)
        if SCRIPTS_DIRS_CONFIG_KEY in config.keys():
            for scripts_dir in config[SCRIPTS_DIRS_CONFIG_KEY]:
                self.add_scripts_path(scripts_dir)
        self._python_dist = sys.executable
        if MULTIPLY_PLATFORM_PYTHON_CONFIG_KEY in config.keys():
            self._python_dist = config[MULTIPLY_PLATFORM_PYTHON_CONFIG_KEY]
        path_to_lib_dir = os.path.abspath(os.path.join(CALVALUS_DIR, 'share/lib'))
        path_to_bin_dir = os.path.abspath(os.path.join(CALVALUS_DIR, 'share/bin'))
        sys.path.insert(0, path_to_lib_dir)
        sys.path.insert(0, path_to_bin_dir)
        path = os.environ['PATH']
        os.environ['PATH'] = f'{path_to_bin_dir}:{path}'


    # TODO: require an interface of data access to select data stores to be used
    def _restrict_to_mundi_datastore(self):
        for data_store in self.data_access_component._data_stores:
            if data_store._id == "Mundi":
                self.data_access_component._data_stores = [data_store]
                return
        raise ValueError('data store Mundi not found in configuration')

    def new_job(self, duration: int) -> Job:
        job = Job(duration)
        self._jobs[job.id] = job
        return job

    def get_job(self, job_id: int) -> Optional[Job]:
        return self._jobs.get(job_id)

    def get_jobs(self) -> List[Job]:
        return [job.to_dict() for job in self._jobs.values()]

    def set_working_dir(self, working_dir: str):
        # todo remove previous working dirs
        self._working_dir = working_dir
        sys.path.insert(0, working_dir)
        os.environ['PATH'] += f':{working_dir}'

    @property
    def working_dir(self) -> str:
        return self._working_dir

    def add_workflows_path(self, workflows_path: str):
        sys.path.insert(0, workflows_path)
        os.environ['PATH'] += f':{workflows_path}'

    def add_scripts_path(self, scripts_path: str):
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
