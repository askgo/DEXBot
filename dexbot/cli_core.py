#!/usr/bin/env python3

from collections import OrderedDict
from bitshares.instance import shared_bitshares_instance

import logging
import os
import os.path
import signal
import sys

from dexbot.config import Config, DEFAULT_CONFIG_FILE
from dexbot.cli_conf import SYSTEMD_SERVICE_NAME, get_whiptail, setup_systemd
from dexbot.helper import initialize_orders_log, initialize_data_folders
from dexbot.ui import (
    verbose,
    chain,
    unlock,
    configfile
)
from .core_worker import CoreWorkerInfrastructure
from .mp_worker import MPWorkerInfrastructure

from .cli_conf import configure_dexbot, dexbot_service_running
from . import errors
from . import helper

# We need to do this before importing click
if "LANG" not in os.environ:
    os.environ['LANG'] = 'C.UTF-8'
import click  # noqa: E402

from concurrent import futures
from concurrent.futures.thread import ThreadPoolExecutor
import multiprocessing

from concurrent.futures.process import ProcessPoolExecutor

MAX_WORKERS = 20


log = logging.getLogger(__name__)

# Initial logging before proper setup.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# Configure orders logging
initialize_orders_log()

# Initialize data folders
initialize_data_folders()

bitshares = None

def set_global_session():
    global bitshares
    if not bitshares:
        bitshares = shared_bitshares_instance()


@click.group()
@click.option(
    "--configfile",
    default=DEFAULT_CONFIG_FILE,
)
@click.option(
    '--logfile',
    default=None,
    type=click.Path(dir_okay=False, writable=True),
    help='Override logfile location (example: ~/dexbot.log)'
)
@click.option(
    '--verbose',
    '-v',
    type=int,
    default=3,
    help='Verbosity (0-15)')
@click.option(
    '--systemd/--no-systemd',
    '-d',
    default=False,
    help='Run as a daemon from systemd')
@click.option(
    '--pidfile',
    '-p',
    type=click.Path(dir_okay=False, writable=True),
    default='',
    help='File to write PID')
@click.pass_context
def main(ctx, **kwargs):
    ctx.obj = {}
    for k, v in kwargs.items():
        ctx.obj[k] = v


@main.command()
@click.pass_context
@configfile
@chain
@unlock
@verbose
def run(ctx):
    """ Continuously run the worker
     ** NOTE ** : this is an abbreviated cli file for the purpose of testing out threadpools
    """
    print("THIS IS A DEXBOT CLI-CORE RUN")

    if ctx.obj['pidfile']:
        with open(ctx.obj['pidfile'], 'w') as fd:
            fd.write(str(os.getpid()))
    try:
        log.info("Running Dexbot multiprocessing")

        list_of_workers = []
        for worker_name in ctx.config["workers"].items():
            single_worker_config = Config.get_worker_config_file(worker_name[0])
            worker = CoreWorkerInfrastructure(single_worker_config)
            list_of_workers.append(worker)

        MAX_WORKERS =  len(list_of_workers)
        print("Total number of workers", MAX_WORKERS)

        print("Entering MP PoolExecutor in core run")
        to_do = []

        with ProcessPoolExecutor(initializer=set_global_session) as pool:
            for obj in list_of_workers:
                future_result = pool.submit(obj.run)
                to_do.append(future_result)

        for future in futures.as_completed(to_do):
            res = future.result()
            print('Future result', res, sep='')

    except errors.NoWorkersAvailable:
        sys.exit(70)  # 70= "Software error" in /usr/include/sysexts.h



@main.command()
@click.pass_context
@configfile
@chain
@unlock
@verbose
def runmp(ctx):
    """ Continuously run the worker
     ** NOTE ** : this is an abbreviated cli file for the purpose of testing out threadpools
     This method for ThreadPool of Workers, each of which is a Process
    """
    if ctx.obj['pidfile']:
        with open(ctx.obj['pidfile'], 'w') as fd:
            fd.write(str(os.getpid()))
    try:
        list_of_workers = []
        MAX_WORKERS = len(ctx.config["workers"].items())
        print("Total Number of workers", MAX_WORKERS)

        bitshares = shared_bitshares_instance()
        for worker_name in ctx.config["workers"].items():
            single_worker_config = Config.get_worker_config_file(worker_name[0])
            # print(single_worker_config)
            worker = MPWorkerInfrastructure(single_worker_config, bitshares_instance=bitshares)
            worker.init_workers(single_worker_config)
            list_of_workers.append(worker)

    except errors.NoWorkersAvailable:
        sys.exit(70)  # 70= "Software error" in /usr/include/sysexts.h


@main.command()
@click.pass_context
@configfile
@chain
@unlock
def configure(ctx):
    """ Interactively configure dexbot
    """
    # Make sure the dexbot service isn't running while we do the config edits
    if dexbot_service_running():
        click.echo("Stopping dexbot daemon")
        os.system('systemctl --user stop dexbot')

    config = Config(path=ctx.obj['configfile'])
    configure_dexbot(config, ctx)
    config.save_config()

    click.echo("New configuration saved")
    if config.get('systemd_status', 'disabled') == 'enabled':
        click.echo("Starting dexbot daemon")
        os.system("systemctl --user start dexbot")


if __name__ == '__main__':
    main()
