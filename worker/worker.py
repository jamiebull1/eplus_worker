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
import os
import tempfile
import zipfile

from runner import run as eplus_run


THIS_DIR = os.path.abspath(os.path.dirname(__file__))
JOBS_DIR = os.path.join(THIS_DIR, 'jobs')
RESULTS_DIR = os.path.join(THIS_DIR, 'results')


def get_jobs():
    """
    """
    jobs = [os.path.join(JOBS_DIR, job)
            for job in os.listdir(JOBS_DIR)]
    return jobs


def unzip(src, dest=None, rm=False):
    """Unzip a zipped file.
    
    Parameters
    ----------
    src : str
        Path to the zip archive.
    dest : str, optional {default: None}
        The destination folder.
    rm : bool
        Flag indicating whether to delete the archive once unzipped.

    """
    with zipfile.ZipFile(src, 'r') as zf:
        zf.extractall(dest)
    if rm:
        os.remove(src)


def main():
    while True:
        jobs = get_jobs()
        run_dir = tempfile.mkdtemp()
        if jobs:
            logging.debug('found %i jobs' % len(jobs))
            unzip(jobs[0], run_dir)

            idf = os.path.join(run_dir, 'in.idf')
            epw = os.path.join(run_dir, 'in.epw')
            eplus_run(idf, epw, output_directory=RESULTS_DIR)
    
    
if __name__ == "__main__":
    main()