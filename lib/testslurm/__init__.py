import datetime
import os
import re
import shutil
import subprocess
import time
import unittest
from enum import Enum
from pathlib import Path

from ._utilities import check_type, check_return_Path_None_default, resolve_path, random_unique_filename, \
    check_type_None_default, check_return_Path, check_return_int

__all__ = [
    'TestSlurm',
    'SlurmStates'
]

def _run_subprocess(args):

    completed_subprocess = subprocess.run(args, text = True, capture_output = True)

    if completed_subprocess.stderr != '':
        raise RuntimeError(f'Subprocess errored out: {completed_subprocess.stderr}')

    else:
        return completed_subprocess.stdout

def _time():
    return datetime.datetime.now().strftime('%H:%M:%S.%f %Y-%m-%d')

class SlurmStates(Enum):

    BOOT_FAIL     = 'BF'
    CANCELLED     = 'CA'
    COMPLETED     = 'CD'
    CONFIGURING   = 'CF'
    COMPLETING    = 'CG'
    DEADLINE      = 'DL'
    FAILED        = 'F'
    NODE_FAIL     = 'NF'
    OUT_OF_MEMORY = 'OOM'
    PENDING       = 'PD'
    PREEMPTED     = 'PM'
    RUNNING       = 'R'
    RESV_DEL_HOLD = 'RD'
    REQUEUE_FED   = 'RF'
    REQUEUE_HOLD  = 'RH'
    REQUEUED      = 'RQ'
    RESIZING      = 'RS'
    REVOKED       = 'RV'
    SIGNALING     = 'SI'
    SPECIAL_EXIT  = 'SE'
    STAGE_OUT     = 'SO'
    STOPPED       = 'ST'
    SUSPENDED     = 'S'
    TIMEOUT       = 'TO'
    NONE          = ''

class TestSlurm(unittest.TestCase):

    test_dir = None

    def __init_subclass__(cls, **kwargs):

        try:
            test_dir = kwargs.pop('test_dir')

        except KeyError:
            pass

        else:
            cls.test_dir = test_dir

        super().__init_subclass__(**kwargs)

    @classmethod
    def setUpClass(cls):

        if cls.test_dir is not None:

            if cls.test_dir.exists():
                shutil.rmtree(cls.test_dir)

            cls.test_dir.mkdir(parents = True, exist_ok = False)

    @classmethod
    def tearDownClass(cls):

        if cls.test_dir is not None and cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)

    def setUp(self):

        self.job_id = None
        self.error_file = None
        self.output_file = None

    def tearDown(self):

        self.cancel_job()
        self.job_id = None
        self.error_file = None
        self.output_file = None

    def check_job_id(self, job_id):

        check_type_None_default(job_id, 'job_id', str, None)

        if job_id is None and self.job_id is None:
            raise ValueError("job_id is None")

        elif job_id is not None:
            return job_id

        else:
            return self.job_id

    def cancel_job(self, job_id = None):

        job_id = self.check_job_id(job_id)
        _run_subprocess(['scancel', job_id])

    def job_state(self, job_id = None):

        job_id = self.check_job_id(job_id)
        return SlurmStates(_run_subprocess(['squeue', '-j', '-h', job_id, '-o', '%.2t']).strip())

    def check_error_file(self, regex = None):

        if self.error_file is None:
            raise ValueError('error_file is None')

        if regex is not None and not isinstance(regex, (re.Pattern, str)):
            raise TypeError

        if not self.error_file.exists():
            raise FileNotFoundError('error_file does not exist')

        if not self.error_file.is_file():
            raise FileNotFoundError('error_file is not a file')

        with self.error_file.open('r') as fh:

            contents = ''

            for line in fh:
                contents += line

        if regex is not None:

            try:
                self.assertIsNotNone(re.match(regex, contents))

            except AssertionError as e:
                raise AssertionError(contents) from e

        else:

            try:
                self.assertEqual(contents, '')

            except AssertionError as e:
                raise AssertionError(contents) from e

    def wait_till_not_state(self, state, job_id = None, max_sec = 600, query_sec = 1, verbose = False):

        check_type(state, 'state', SlurmStates)
        job_id = self.check_job_id(job_id)
        max_sec = check_return_int(max_sec, 'max_sec')
        query_sec = check_return_int(query_sec, 'query_sec')
        check_type(verbose, 'verbose', bool)
        querying = True
        start = time.time()
        current_state = None

        while querying:

            if time.time() - start >= max_sec:
                raise TimeoutError(f'Exceeded maximum wait time of {max_sec} seconds.')

            time.sleep(query_sec)
            current_state = self.job_state(job_id)
            querying = state == current_state

        if verbose:
            print(f'Job {job_id} not in state {state} (current state = {current_state})\n{_time()}')

    def write_batch(self, sbatch_file, command, name, nodes, tasks, time_sec, error_file, output_file, verbose = False):

        self.sbatch_file = check_return_Path(sbatch_file, 'sbatch_file')
        check_type(command, 'command', str)
        check_type(name, 'name', str)
        nodes = check_return_int(nodes, 'nodes')
        tasks = check_return_int(tasks, 'tasks')
        time_sec = check_return_int(time_sec, 'time_sec')
        self.error_file = check_return_Path(error_file, 'error_file')
        self.output_file = check_return_Path_None_default(output_file, 'output_file', None)
        contents = (
f"""#!/usr/bin/env bash

#SBATCH --job-name=corniferslurmtests
#SBATCH --time=00:00:{time_sec}
#SBATCH --ntasks={tasks}
#SBATCH --nodes={nodes}
#SBATCH --ntasks-per-core=1
{f'#SBATCH --output={self.output_file}' if self.output_file is not None else ''}
#SBATCH --error={self.error_file}
#SBATCH --exclude=u120

{command}
"""
            )

        with sbatch_file.open('w') as fh:
            fh.write(contents)

        if verbose:
            print(f'Wrote batch file\n{_time()}\n{self.sbatch_file}\n{contents}')

    def submit_batch(self, sbatch_file = None, verbose = False):

        self.sbatch_file = resolve_path(check_return_Path_None_default(sbatch_file, 'sbatch_file', self.sbatch_file))
        self.job_id = _run_subprocess(['sbatch', str(self.sbatch_file)])[20:-1]

        if verbose:
            print(f'Batch job submitted\n{_time()}\n{self.sbatch_file}\n{self.job_id}')