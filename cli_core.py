#!/usr/bin/env python3

import cProfile
from dexbot import cli_core


if __name__ == '__main__':

    cProfile.run('cli_core.main()', 'cli_core_stats')
