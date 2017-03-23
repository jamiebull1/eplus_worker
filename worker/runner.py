# Copyright (c) 2016 Jamie Bull
# =======================================================================
#  Distributed under the MIT License.
#  (See accompanying file LICENSE or copy at
#  http://opensource.org/licenses/MIT)
# =======================================================================
"""
Class to run IDF objects in EnergyPlus.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import distutils.spawn
import os
import platform
from pprint import pprint
from subprocess import CalledProcessError
from subprocess import check_call
import tempfile


def find_version():
    """Get the installed EnergyPlus version number.
    """
    energyplus = distutils.spawn.find_executable('energyplus')
    if not energyplus:
        raise AttributeError
    energyplus = os.path.realpath(energyplus)  # follow links in /usr/bin
    folder = os.path.dirname(energyplus)
    version = os.path.basename(folder)[-5:]
#    version = version.replace('.', '-')
#    assert version[1] == '-' and version[3] == '-'

    return version

try:
    VERSION = os.environ["ENERGYPLUS_INSTALL_VERSION"]  # used in CI file)
except KeyError:
    VERSION = find_version()

if platform.system() == 'Windows':
    EPLUS_HOME = "C:/EnergyPlusV{VERSION}".format(**locals())
    EPLUS_EXE = os.path.join(EPLUS_HOME, 'energyplus.exe')
elif platform.system() == "Linux":
    EPLUS_HOME = "/usr/local/EnergyPlus-{VERSION}".format(**locals())
    EPLUS_EXE = os.path.join(EPLUS_HOME, 'energyplus')
else:
    EPLUS_HOME = "/Applications/EnergyPlus-{VERSION}".format(**locals())
    EPLUS_EXE = os.path.join(EPLUS_HOME, 'energyplus')

EPLUS_WEATHER = os.path.join(EPLUS_HOME, 'WeatherData')
THIS_DIR = os.path.abspath(os.path.dirname(__file__))


def run(idf=None, weather=None, output_directory='', annual=False,
        design_day=False, idd=None, epmacro=False, expandobjects=False,
        readvars=False, output_prefix=None, output_suffix=None, version=False,
        verbose='v'):
    """
    Wrapper around the EnergyPlus command line interface.

    Parameters
    ----------
    idf : str
        Full or relative path to the IDF file to be run.

    weather : str
        Full or relative path to the weather file.

    output_directory : str, optional
        Full or relative path to an output directory (default: 'run_outputs)

    annual : bool, optional
        If True then force annual simulation (default: False)

    design_day : bool, optional
        Force design-day-only simulation (default: False)

    idd : str, optional
        Input data dictionary (default: Energy+.idd in EnergyPlus directory)

    epmacro : str, optional
        Run EPMacro prior to simulation (default: False).

    expandobjects : bool, optional
        Run ExpandObjects prior to simulation (default: False)

    readvars : bool, optional
        Run ReadVarsESO after simulation (default: False)

    output_prefix : str, optional
        Prefix for output file names (default: eplus)

    output_suffix : str, optional
        Suffix style for output file names (default: L)
            L: Legacy (e.g., eplustbl.csv)
            C: Capital (e.g., eplusTable.csv)
            D: Dash (e.g., eplus-table.csv)

    version : bool, optional
        Display version information (default: False)

    verbose: str
        Set verbosity of runtime messages (default: v)
            v: verbose
            q: quiet

    Returns
    -------
    str : status

    Raises
    ------
    CalledProcessError

    """
    args = locals().copy()
    if version:
        # just get EnergyPlus version number and return
        cmd = [EPLUS_EXE, '--version']
        check_call(cmd)
        return

    # get unneeded params out of args ready to pass the rest to energyplus.exe
    verbose = args.pop('verbose')
    idf = os.path.abspath(args.pop('idf'))

    # convert paths to absolute paths if required
    if os.path.isfile(args['weather']):
        args['weather'] = os.path.abspath(args['weather'])
    else:
        args['weather'] = os.path.join(EPLUS_WEATHER, args['weather'])
    args['output_directory'] = os.path.abspath(args['output_directory'])

    # store the directory we start in
    cwd = os.getcwd()
    run_dir = os.path.abspath(tempfile.mkdtemp())
    os.chdir(run_dir)

    # build a list of command line arguments
    cmd = [EPLUS_EXE]
    for arg in args:
        if args[arg]:
            if isinstance(args[arg], bool):
                args[arg] = ''
            cmd.extend(['--{}'.format(arg.replace('_', '-'))])
            if args[arg] != "":
                cmd.extend([args[arg]])
    cmd.extend([idf])

    try:
        if verbose == 'v':
            check_call(cmd)
        elif verbose == 'q':
            check_call(cmd, stdout=open(os.devnull, 'w'))
    except CalledProcessError as e:
        # potentially catch contents of std out and put it in the error
        raise
    except IOError as e:
        raise
    finally:
        os.chdir(cwd)
    return 'OK'
