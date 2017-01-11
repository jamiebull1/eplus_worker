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

import logging
from multiprocessing import cpu_count
import multiprocessing
import os
import time
from zipfile import BadZipfile
import zipfile

from worker.runner import run as eplus_run


logging.basicConfig(
    level=logging.DEBUG,
    filename='/var/log/worker.log',
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%m-%d %H:%M',
    filemode='a')
logging.info("Starting worker")

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
JOBS_DIR = os.path.join(THIS_DIR, 'jobs')
RESULTS_DIR = os.path.join(THIS_DIR, 'results')


def get_jobs():
    """Pick up the jobs currently in the jobs directory.

    Returns
    -------
    list
        List of absolute paths to each zipped job.

    """
    jobs = [os.path.join(JOBS_DIR, job)
            for job in os.listdir(JOBS_DIR)]
    return jobs


def unzip_dir(src, dest=None, rm=False):
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

    """
    with zipfile.ZipFile(src, 'r') as zf:
        try:
            zf.extractall(dest)
        except BadZipfile:
            time.sleep(5)  # allow any partially-uploaded jobs to complete
            zf.extractall(dest)
    if rm:
        os.remove(src)


def run_job(job):
    time.sleep(5)  # allow any partially-uploaded jobs to complete

    run_dir = os.path.join(
        RESULTS_DIR, os.path.basename(job).replace('.zip', ''))
    os.mkdir(run_dir)
    unzip_dir(job, run_dir, rm=True)
    try:
        idf = os.path.join(run_dir, 'in.idf')
        epw = os.path.join(run_dir, 'in.epw')
        output_dir = os.path.join(
            RESULTS_DIR, os.path.basename(run_dir))
        eplus_run(idf, epw,
                  output_directory=output_dir,
                  expandobjects=True,
                  verbose='q')
    except Exception as e:
        logging.error("Error: %s" % e)
        raise


def running_jobs():
    dirs = os.listdir(RESULTS_DIR)
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
        if running_jobs <= num_cpus:
            open(os.path.join(
                THIS_DIR, os.pardir, os.pardir, 'ready.txt'), 'a').close()
        time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(e, exc_info=True)
        raise
