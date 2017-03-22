# EnergyPlus Worker for local or remote simulations

EnergyPlus is a building energy simulation to model energy use and internal
environmental conditions of buildings. It is used by engineers, architects, and
academics.

However it can be frustrating having your laptop tied up running hundreds of
models, expecially when there are so many other options, from AWS EC2 to a
university network, to a handful of Raspberry Pis, or just an old laptop that
would otherwise be gathering dust.

This module provides a quick and easy way to set up an EnergyPlus worker on
a range of platforms. The only dependencies are Python and EnergyPlus.

## Installation

From a shell on your server, run:

```
git clone https://github.com/jamiebull1/eplus_worker.git
cd eplus_worker
```

## Usage

Then to start the server, run:

```python -m worker.main```

This starts a process which monitors the `./worker/jobs` directory and runs
any jobs that are uploaded.

You can then upload zipfiles containing an IDF, EPW, and optionally a CSV with
schedules, to the `./worker/jobs` directory, and download completed jobs from
the `./worker/results` directory.

There is a companion project, EnergyPlus Client to help out with managing the
uploading and downloading of jobs.
