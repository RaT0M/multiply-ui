import threading
import time
from typing import Dict, List, Optional, Union

import ipywidgets
from IPython.display import display

from .callapi import call_api

URL_BASE = "http://localhost:9090/"

JOB_EXECUTE_URL = URL_BASE + "jobs/execute?duration={duration}"
JOB_LIST_URL = URL_BASE + "jobs/list"
JOB_STATUS_URL = URL_BASE + "jobs/{job_id}"
JOB_CANCEL_URL = URL_BASE + "jobs/cancel/{job_id}"
JOB_RESULTS_URL = URL_BASE + "jobs/results/{job_id}"
RESULT_URL = URL_BASE + "result/{job_id}?parameter={parameter}"
RESULT_OPEN_URL = URL_BASE + "/results/open/{id})"


def exec_ui():
    _interact = ipywidgets.interact.options(manual=True, manual_name="Execute Job")
    _interact(Job.execute_job,
              duration=ipywidgets.IntSlider(min=10, max=1000, step=10, value=60))


def job_monitor():
    header_box = ipywidgets.HBox([ipywidgets.Label('Job ID'), ipywidgets.Label('Duration'),
                                  ipywidgets.Label('Progress'), ipywidgets.Label('Status')])
    boxes = [header_box]
    job_status_list = Job.get_all().get_as_dict_list()
    progress_bars = []
    status_labels = []
    for job_status_dict in job_status_list:
        progress = ipywidgets.FloatProgress(value=job_status_dict["progress"], min=0.0, max=1.0)
        status_label = ipywidgets.Label(str(job_status_dict["status"]))
        box = ipywidgets.HBox([ipywidgets.Label(str(job_status_dict["id"])),
                               ipywidgets.Label(str(job_status_dict["duration"])),
                               progress, status_label])
        progress_bars.append(progress)
        status_labels.append(status_label)
        boxes.append(box)

    def monitor(boxes, progress_bars, status_labels):
        while True:
            job_status_list = Job.get_all().get_as_dict_list()
            num_progress_bars = len(progress_bars)
            for index, job_status_dict in enumerate(job_status_list):
                if index < num_progress_bars:
                    if status_labels[index].value == "new":
                        if job_status_dict["status"] == "new":
                            continue
                            progress_bars[index].value = job_status_dict["progress"]
                        status_labels[index].value = job_status_dict["status"]
                    elif status_labels[index].value == "cancelled" and job_status_dict["status"] != "cancelled":
                        progress_bars[index].value = job_status_dict["progress"]
                        status_labels[index].value = "cancelled"
                    elif status_labels[index].value == "success" and job_status_dict["status"] != "success":
                        progress_bars[index].value = job_status_dict["progress"]
                        status_labels[index].value = "success"
                    elif status_labels[index].value == "running":
                        progress_bars[index].value = job_status_dict["progress"]
                        status_labels[index].value = job_status_dict["status"]
                else:
                    progress = ipywidgets.FloatProgress(value=job_status_dict["progress"], min=0.0, max=1.0)
                    status_label = ipywidgets.Label(str(job_status_dict["status"]))
                    box = ipywidgets.HBox([ipywidgets.Label(str(job_status_dict["id"])),
                                           ipywidgets.Label(str(job_status_dict["duration"])),
                                           progress, status_label])
                    progress_bars.append(progress)
                    status_labels.append(status_label)
                    boxes.append(box)
            time.sleep(0.5)

    job_monitor = ipywidgets.VBox(boxes)
    monitor_thread = threading.Thread(target=monitor, args=(boxes, progress_bars, status_labels))
    display(job_monitor)
    monitor_thread.start()


class Result:

    def __init__(self, result_dict: Dict):
        self._result_dict = result_dict

    def _repr_html_(self):
        return self.html_table([self._result_dict])

    @classmethod
    def html_table(cls, result_dict_list: List[Dict]):
        table_rows = []
        for result_dict in result_dict_list:
            result_group_id = result_dict["result_group_id"]
            result_id = result_dict["result_id"]
            result_parameter = result_dict["parameter_name"]
            table_rows.append(f"<tr>"
                              f"<td>{result_group_id}</td>"
                              f"<td>{result_id}</td>"
                              f"<td>{result_parameter}</td>"
                              f"</tr>")
            table_header = (f"<tr>"
                            f"<th>Result Group ID</th>"
                            f"<th>Result ID</th>"
                            f"<th>Parameter</th>"
                            f"</tr>")
        return (
            f"<table>"
            f"  {table_header}"
            f"  {''.join(table_rows)}"
            f"</table>"
        )


class ResultGroup(Result):

    def __init__(self, result_dict: Dict):
        super().__init__(result_dict)

    def _repr_html_(self):
        return self.html_table(self._result_dict["results"])

    def result(self, parameter: Union[str, int]) -> Result:
        for result in self._result_dict["results"]:
            if ("result_id" in result and parameter == result["result_id"]) or \
                    ("parameter_name" in result and parameter == result["parameter_name"]):
                return Result(result)


class JobStatus:

    def __init__(self, job_status_dict: Dict):
        self._status_dict = job_status_dict

    def _repr_html_(self):
        return self.html_table([self._status_dict])

    @classmethod
    def html_table(cls, job_status_dict_list: List[Dict]):
        table_rows = []
        for job_status_dict in job_status_dict_list:
            job_id = job_status_dict["id"]
            job_duration = job_status_dict["duration"]
            job_progress = job_status_dict["progress"]
            job_status = job_status_dict["status"]
            max_width = 200
            if job_progress is not None:
                width = int(job_progress * max_width)
                progress_html = (f"<div style=\"width:{width}px;height:1em;background-color:Aquamarine;\"></div>")
            else:
                progress_html = f"<div style=\"min-width:{max_width};background-color:LightGray;\">Not started</div>"
            table_rows.append(f"<tr>"
                              f"<td>{job_id}</td>"
                              f"<td>{job_duration}</td>"
                              f"<td>{progress_html}</td>"
                              f"<td>{job_status}</td>"
                              f"</tr>")
        table_header = (f"<tr>"
                        f"<th>Job ID</th>"
                        f"<th>Duration</th>"
                        f"<th>Progress</th>"
                        f"<th>Status</th>"
                        f"</tr>")
        return (
            f"<table>"
            f"  {table_header}"
            f"  {''.join(table_rows)}"
            f"</table>"
        )


class JobStatusList:

    def __init__(self, job_status_dict_list: List[Dict]):
        self._status_dict_list = job_status_dict_list

    def _repr_html_(self):
        return JobStatus.html_table(self._status_dict_list)

    def get_as_dict_list(self) -> List[Dict]:
        return self._status_dict_list


class Job:

    def __init__(self, job_id: int):
        self._id = job_id

    @classmethod
    def execute_job(cls, duration: int = 100) -> "Job":
        def apply_func(json_obj: Dict):
            return Job(json_obj["id"])

        return call_api(JOB_EXECUTE_URL.format(duration=duration), apply_func)

    @classmethod
    def get_all(cls) -> JobStatusList:
        def apply_func(json_obj: Dict):
            return JobStatusList(json_obj["jobs"])

        return call_api(JOB_LIST_URL, apply_func)

    @classmethod
    def num_jobs(cls) -> int:
        def apply_func(json_obj: Dict):
            return len(json_obj["jobs"])

        return call_api(JOB_LIST_URL, apply_func)

    def cancel(self) -> JobStatus:
        return call_api(JOB_CANCEL_URL.format(job_id=self._id), JobStatus)

    def result(self, parameter: Union[str, int]) -> Result:
        return call_api(RESULT_URL.format(job_id=self._id, parameter=parameter), Result)

    @property
    def status(self) -> JobStatus:
        return call_api(JOB_STATUS_URL.format(job_id=self._id), JobStatus)

    @property
    def progress(self) -> float:
        def apply_func(job_status_dict: Dict) -> float:
            return job_status_dict["progress"]

        return call_api(JOB_STATUS_URL.format(job_id=self._id), apply_func)

    @property
    def results(self) -> Optional[ResultGroup]:
        return call_api(JOB_RESULTS_URL.format(job_id=self._id), ResultGroup)

    def _repr_html_(self):
        return f"<h4>Job #{self._id}</h4>"
