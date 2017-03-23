#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
worker.py
~~~~~~~~~
EnergyPlus worker. This contains the basic code required to watch a folder for
incoming jobs, then run them and place the results ready to be fetched by the
client.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import glob
import logging
from multiprocessing import cpu_count
import multiprocessing
import os
import time
from zipfile import BadZipfile
import zipfile

from worker.runner import run as eplus_run


THIS_DIR = os.path.abspath(os.path.dirname(__file__))
JOBS_DIR = os.path.join(THIS_DIR, 'jobs')
RESULTS_DIR = os.path.join(THIS_DIR, 'results')
LOG_PATH = os.path.join(THIS_DIR, 'worker.log')

logging.basicConfig(
    level=logging.DEBUG,
    filename=LOG_PATH,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%m-%d %H:%M',
    filemode='a')
logging.info("Starting worker")


def get_jobs():
    """Pick up the jobs currently in the jobs directory.

    Returns
    -------
    list
        List of absolute paths to each zipped job.

    """
    jobs = [os.path.join(JOBS_DIR, job)
            for job in os.listdir(JOBS_DIR)
            if job != '.gitignore']
    return jobs


def unzip_dir(src, dest=None, rm=False, retry_time=5):
    """Unzip a zipped file.

    This is used for the incoming jobs.

    Parameters
    ----------
    src : str
        Path to the zip archive.
    dest : str, optional {default: None}
        The destination folder.
    rm : bool, optional {default: False}
        Flag indicating whether to delete the archive once unzipped.
    retry_time : int, {default: 5}
        Seconds to wait if unzipping fails on first attempt.

    """
    with zipfile.ZipFile(src, 'r') as zf:
        try:
            zf.extractall(dest)
        except BadZipfile:
            time.sleep(retry_time)  # allow partially-uploaded jobs to complete
            zf.extractall(dest)
    if rm:
        os.remove(src)


def ensure_dir(dir_):
    """Ensure a directory exists.
    """
    try:
        os.mkdir(dir_)
    except OSError:
        assert os.path.isdir(dir_)


def run_job(job, rm=True):
    """Run an EnergyPlus job.
    """
    run_dir = os.path.join(
        RESULTS_DIR, os.path.basename(job).replace('.zip', ''))
    ensure_dir(run_dir)
    unzip_dir(job, run_dir, rm=rm, retry_time=5)
    try:
        idf = glob.glob(os.path.join(run_dir, '*.idf'))[0]
        epw = glob.glob(os.path.join(run_dir, '*.epw'))[0]
        output_dir = os.path.join(
            RESULTS_DIR, os.path.basename(run_dir))
        eplus_run(idf, epw,
                  output_directory=output_dir,
                  expandobjects=True,
                  verbose='v')
    except Exception as e:
        logging.error("Error: %s" % e)
        raise


def running_jobs():
    """Get a count of currently running jobs.

    Returns
    -------
    int

    """
    dirs = [os.path.join(RESULTS_DIR, dir_)
            for dir_ in os.listdir(RESULTS_DIR)
            if os.path.isdir(os.path.join(RESULTS_DIR, dir_))]
    active_jobs = len(dirs)
    for f in dirs:
        if 'eplusout.end\n' in os.listdir(os.path.join(RESULTS_DIR, f)):
            active_jobs -= 1
    return active_jobs


def main():
    num_cpus = cpu_count()
    logging.info('This system has %i CPUs available' % num_cpus)
    while True:
        jobs = get_jobs()
        if jobs:
            logging.info('found %i jobs' % len(jobs))
        for job in jobs:
            p = multiprocessing.Process(target=run_job, args=(job,))
            p.start()
        time.sleep(5)
        if running_jobs() <= num_cpus:
            open(os.path.join(
                THIS_DIR, os.pardir, 'ready.txt'), 'a').close()
        time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(e, exc_info=True)
        raise
