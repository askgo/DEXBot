import importlib
import logging
import copy
import multiprocessing

import dexbot.errors as errors
from bitshares.notify import Notify
from bitshares.instance import shared_bitshares_instance


log = logging.getLogger(__name__)
log_workers = logging.getLogger('dexbot.per_worker')
# NOTE this is the  special logger for per-worker events
# it returns LogRecords with extra fields: worker_name, account, market and is_disabled
# is_disabled is a callable returning True if the worker is currently disabled.
# GUIs can add a handler to this logger to get a stream of events of the running workers.


'''
***********
NOTE : this is an abbreviated class for the purpose of testing out threadpools
***********
'''

class MPWorkerInfrastructure(multiprocessing.Process):

    def __init__(
        self,
        config,
        bitshares_instance=None,
        view=None
    ):
        super().__init__()

        # BitShares instance
        self.bitshares = bitshares_instance or shared_bitshares_instance()
        self.event_lock = multiprocessing.Lock()

        self.config = copy.deepcopy(config)
        self.view = view
        self.jobs = set()
        self.notify = None

        self.workers = {}
        self.worker_name = None
        self.worker = None

        self.accounts = set()
        self.markets = set()

    def init_workers(self, config):
        """ Initialize the workers
        """
        try:
            log.info("Inside Init CORE WORKER")
            # handle only one worker
            for worker_name, worker in config["workers"].items():
                self.worker_name = worker_name
                self.worker = worker
                log.info(worker_name)

            if self.worker_name is not None and self.worker is not None:
                strategy_class = getattr(
                    importlib.import_module(self.worker["module"]),
                    'Strategy'
                )

                self.workers[self.worker_name] = strategy_class(
                    config=self.config,
                    name=self.worker_name,
                    bitshares_instance=self.bitshares,
                    view=self.view
                )
                log.info("CORE WORKER: init strategy class: {}".format(self.worker_name))

                self.markets.add(self.worker['market'])
                self.accounts.add(self.worker['account'])

        except BaseException:
            log_workers.exception("Worker initialisation", extra={
                'worker_name': self.worker_name, 'account': self.worker['account'],
                'market': 'unknown', 'is_disabled': (lambda: True)
            })

    def update_notify(self):
        self.event_lock.acquire()
        log.info("CORE WORKER: update_notify {}".format(self.worker_name))
        if not self.workers:
            log.critical("No workers actually running")
            raise errors.NoWorkersAvailable()
        if self.notify:
            # Update the notification instance
            self.notify.reset_subscriptions(list(self.accounts), list(self.markets))
            log.info("CORE WORKER: reset subscriptions ")

        else:
            # Initialize the notification instance
            self.notify = Notify(
                markets=list(self.markets),
                accounts=list(self.accounts),
                on_market=self.on_market,
                on_account=self.on_account,
                on_block=self.on_block,
                bitshares_instance=self.bitshares
            )
            log.info("CORE WORKER: INSTANTIATE NOTIFY CLASS: {}".format(self.worker_name))
        self.event_lock.release()

    # Events
    def on_block(self, data):
        if self.jobs:
            try:
                for job in self.jobs:
                    job()
            finally:
                self.jobs = set()

        self.event_lock.acquire()
        if self.workers[self.worker_name].disabled:
            self.workers[self.worker_name].log.error('Worker "{}" is disabled'.format(self.worker_name))
            self.workers.pop(self.worker_name)
        try:
            self.workers[self.worker_name].ontick(data)
            log.info("CORE WORKER: ON_BLOCK(),ontick: {}".format(self.worker_name))

        except Exception as e:
            self.workers[self.worker_name].log.exception("in ontick() {} ".format(self.worker_name))
            try:
                self.workers[self.worker_name].error_ontick(e)
            except Exception:
                self.workers[self.worker_name].log.exception("in error_ontick()")
        self.event_lock.release()

    def on_market(self, data):
        if data.get("deleted", False):  # No info available on deleted orders
            return

        self.event_lock.acquire()
        if self.workers[self.worker_name].disabled:
            self.workers[self.worker_name].log.error('Worker "{}" is disabled'.format(self.worker_name))
            self.workers.pop(self.worker_name)
        if self.worker["market"] == data.market:
            try:
                self.workers[self.worker_name].onMarketUpdate(data)
                log.info("CORE WORKER: onMarketUpdate: {}".format(self.worker_name))

            except Exception as e:
                self.workers[self.worker_name].log.exception("in onMarketUpdate()")
                try:
                    self.workers[self.worker_name].error_onMarketUpdate(e)
                    log.info("CORE WORKER: error onMarketUpdate ")

                except Exception:
                    self.workers[self.worker_name].log.exception("in error_onMarketUpdate()")
        self.event_lock.release()

    def on_account(self, account_update):
        self.event_lock.acquire()
        account = account_update.account
        if self.workers[self.worker_name].disabled:
            self.workers[self.worker_name].log.error('Worker "{}" is disabled'.format(self.worker_name))
            self.workers.pop(self.worker_name)
        if self.worker["account"] == account["name"]:
            try:
                self.workers[self.worker_name].onAccount(account_update)
                log.info("CORE WORKER: on Account:{} ".format(self.worker_name))

            except Exception as e:
                self.workers[self.worker_name].log.exception("in onAccountUpdate()")
                try:
                    self.workers[self.worker_name].error_onAccount(e)
                except Exception:
                    self.workers[self.worker_name].log.exception("in error_onAccountUpdate()")
        self.event_lock.release()

    def run(self):
        self.update_notify()
        self.notify.listen()

    def remove_market(self, worker_name):
        """ Remove the market only if the worker is the only one using it
        """
        market = self.config['workers'][worker_name]['market']
        for name, worker in self.config['workers'].items():
            if market == worker['market']:
                return  # Found the same market, do nothing
            else:
                # No markets found, safe to remove
                self.markets.remove(market)

    def stop(self, worker_name=None, pause=False):
        """ Used to stop the worker(s)

            :param str worker_name: name of the worker to stop
            :param bool pause: optional argument which tells worker if it was stopped or just paused
        """
        if worker_name:
            try:
                # Kill only the specified worker
                self.remove_market(worker_name)
            except KeyError:
                # Worker was not found meaning it does not exist or it is paused already
                return
            with self.event_lock:
                account = self.config['workers'][worker_name]['account']
                self.config['workers'].pop(worker_name)

            self.accounts.remove(account)
            if pause and worker_name in self.workers:
                self.workers[worker_name].pause()
            self.workers.pop(worker_name, None)
        else:
            # Kill all of the workers
            if pause:
                for worker in self.workers:
                    self.workers[worker].pause()
                self.workers = []

        # Update other workers
        if len(self.workers) > 0:
            self.update_notify()
        else:
            # No workers left, close websocket
            self.notify.websocket.close()

    def do_next_tick(self, job):
        """ Add a callable to be executed on the next tick """
        self.jobs.add(job)
