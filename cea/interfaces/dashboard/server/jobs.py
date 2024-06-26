"""
jobs: maintain a list of jobs to be simulated.
"""
import subprocess
from datetime import datetime
from typing import Dict, Any

import psutil
from fastapi import APIRouter
from pydantic import BaseModel

from cea.interfaces.dashboard.dependencies import CEAJobs
from cea.interfaces.dashboard.server.socketio import sio

router = APIRouter()

# Job states
JOB_STATE_PENDING = 0
JOB_STATE_STARTED = 1
JOB_STATE_SUCCESS = 2
JOB_STATE_ERROR = 3
JOB_STATE_CANCELED = 4

# job_info_model = api.model('JobInfo', {
#     'id': fields.Integer,
#     'script': fields.String,
#     'state': fields.Integer,
#     'error': fields.String,
#     'parameters': fields.Raw,
#     'start_time': fields.DateTime,
#     'end_time': fields.DateTime,
# })
#
# job_info_request_parser = reqparse.RequestParser()
# job_info_request_parser.add_argument("id", type=int, location="json")
# job_info_request_parser.add_argument("script", type=str, required=True, location="json")
# job_info_request_parser.add_argument("state", location="json")
# job_info_request_parser.add_argument("error", location="json")
# job_info_request_parser.add_argument("parameters", type=dict, location="json")


worker_processes = {}  # jobid -> subprocess.Popen


# FIXME: replace with database or similar solution
class JobInfo(BaseModel):
    """Store all the information required to run a job"""
    id: str
    script: str
    parameters: dict
    state: int = JOB_STATE_PENDING
    error: str = None
    start_time: datetime = None
    end_time: datetime = None



@router.get("/{job_id}")
async def get_job_info(jobs: CEAJobs, job_id: str):
    """Return a JobInfo by id"""
    return jobs[job_id]


@router.post("/new")
async def create_new_job(jobs: CEAJobs, payload: Dict[str, Any]):
    """Post a new job to the list of jobs to complete"""
    args = payload
    print("NewJob: args={args}".format(**locals()))

    def next_id():
        """
        FIXME: replace with better solution
        """
        try:
            return str(len(jobs.keys()) + 1)
        except ValueError:
            # this is the first job...
            return str(1)

    job = JobInfo(id=next_id(), script=args["script"], parameters=args["parameters"])
    jobs[job.id] = job
    await sio.emit("cea-job-created", job.model_dump(mode='json'))
    return job


@router.get("/")
async def get_jobs(jobs: CEAJobs):
    return [job.dict() for job in jobs.values()]


@router.post("/started/{job_id}")
async def set_job_started(jobs: CEAJobs, job_id: str) -> JobInfo:
    job = jobs[job_id]
    job.state = JOB_STATE_STARTED
    job.start_time = datetime.now()
    await sio.emit("cea-worker-started", job.model_dump(mode='json'))
    return job


@router.post("/success/{job_id}")
async def set_job_success(jobs: CEAJobs, job_id: str) -> JobInfo:
    job = jobs[job_id]
    job.state = JOB_STATE_SUCCESS
    job.error = None
    job.end_time = datetime.now()
    if job.id in worker_processes:
        del worker_processes[job.id]
    await sio.emit("cea-worker-success", job.model_dump(mode='json'))
    return job


@router.post("/error/{job_id}")
async def set_job_error(jobs: CEAJobs, job_id: str, error: str) -> JobInfo:
    job = jobs[job_id]
    job.state = JOB_STATE_ERROR
    job.error = error
    job.end_time = datetime.now()
    if job.id in worker_processes:
        del worker_processes[job.id]
    await sio.emit("cea-worker-error", job.model_dump(mode='json'))
    return job


@router.post('/start/{job_id}')
async def start_job(jobs: CEAJobs, job_id: str):
    """Start a ``cea-worker`` subprocess for the script. (FUTURE: add support for cloud-based workers"""
    print("tools/route_start: {job_id}".format(**locals()))
    worker_processes[job_id] = subprocess.Popen(["python", "-m", "cea.worker", f"{job_id}"])
    return job_id


@router.post("/cancel/{job_id}")
async def cancel_job(jobs: CEAJobs, job_id: str) -> JobInfo:
    job = jobs[job_id]
    job.state = JOB_STATE_CANCELED
    job.error = "Canceled by user"
    job.end_time = datetime.now()
    kill_job(job_id)
    await sio.emit("cea-worker-canceled", job.model_dump(mode='json'))
    return job


def kill_job(jobid):
    """Kill the processes associated with a jobid"""
    if jobid not in worker_processes:
        return

    popen = worker_processes[jobid]
    # using code from here: https://stackoverflow.com/a/4229404/2260
    # to terminate child processes too
    print("killing child processes of {jobid} ({pid})".format(jobid=jobid, pid=popen.pid))
    try:
        process = psutil.Process(popen.pid)
    except psutil.NoSuchProcess:
        return
    children = process.children(recursive=True)
    for child in children:
        print("-- killing child {pid}".format(pid=child.pid))
        child.kill()
    process.kill()
    del worker_processes[jobid]
