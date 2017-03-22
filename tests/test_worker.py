"""Test module for eplus_worker.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import shutil
import tempfile

from worker.main import get_jobs
from worker.main import run_job
from worker.main import running_jobs
from worker.main import unzip_dir
import worker.main
from worker.runner import find_version


# patch these directories for the test
worker.main.JOBS_DIR = os.path.join(worker.main.THIS_DIR, 'test_jobs')
worker.main.RESULTS_DIR = os.path.join(worker.main.THIS_DIR, 'test_results')


def test_find_version():
    expected = '8-5-0'
    result = find_version()
    assert result == expected


class TestRunIntegration(object):

    def setup(self):
        """Back up resources.
        """
        self.jobs = get_jobs()
        for job in self.jobs:
            shutil.copy(job, '{}.bak'.format(job))

    def teardown(self):
        """Restore resources and tidy up.
        """
        test_dirs = [
             os.path.join(worker.main.RESULTS_DIR, dir_)
             for dir_ in os.listdir(worker.main.RESULTS_DIR)
             if os.path.isdir(os.path.join(worker.main.RESULTS_DIR, dir_))]
        for dir_ in test_dirs:
            shutil.rmtree(dir_)
        for job in self.jobs:
            shutil.move('{}.bak'.format(job), job)

    def test_run_job(self):
        """Integration test that we can run a job.
        """
        job = os.path.join(worker.main.JOBS_DIR, 'test.zip')
        run_job(job, rm=False)

    def test_running_jobs(self):
        """
        Test that there are no running jobs if we haven't started any and
        one if we have.

        """
        assert running_jobs() == 0
        job = os.path.join(worker.main.JOBS_DIR, 'test.zip')
        run_job(job, rm=False)
        assert running_jobs() == 1


def test_getjobs():
    """Test that the expected test job is returned when we call get_jobs.
    """
    jobs = get_jobs()
    assert jobs == [os.path.join(worker.main.JOBS_DIR, 'test.zip')]


class TestZipDir(object):

    def setup(self):
        """Back up resources and create a tempdir.
        """
        self.jobs = get_jobs()
        for job in self.jobs:
            shutil.copy(job, '{}.bak'.format(job))
        self.stored_cwd = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()

    def teardown(self):
        """Restore resources and tidy up.
        """
        for job in self.jobs:
            shutil.move('{}.bak'.format(job), job)
        os.chdir(self.stored_cwd)
        shutil.rmtree(self.tmpdir)

    def test_unzip_dir(self):
        """Test the basic behaviour.
        """
        os.chdir(worker.main.JOBS_DIR)
        job = 'test.zip'
        unzip_dir(job)
        expected = ['in.epw', 'in.idf', 'dummy.csv', 'test.zip']
        result = os.listdir(os.getcwd())
        assert all([e in result for e in expected])
        for f in expected:
            os.remove(os.path.join(os.getcwd(), f))

    def test_unzip_dir_specify_dest(self):
        """Test the behaviour when specifying a destination to unzip to.
        """
        job = os.path.join(worker.main.JOBS_DIR, 'test.zip')
        unzip_dir(job, self.tmpdir)
        expected = ['in.epw', 'in.idf', 'dummy.csv']
        result = os.listdir(self.tmpdir)
        assert all([e in result for e in expected])

    def test_unzip_dir_specify_rm(self):
        """Test the behaviour when specifying to remove the zipfile.
        """
        job = os.path.join(worker.main.JOBS_DIR, 'test.zip')
        unzip_dir(job, self.tmpdir, rm=True)
        expected = ['in.epw', 'in.idf', 'dummy.csv']
        result = os.listdir(self.tmpdir)
        assert all([e in result for e in expected])
        assert not os.path.isfile(job)
