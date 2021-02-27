#!/usr/bin/python3

"""Basically just an interface for testing LogdirIter."""

import logging
import sys

from logdir_iter import LogdirIter

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('logdir_cat')

logdir = LogdirIter(path=sys.argv[1], logger=logger)

i = 0
for r in logdir:
  print(r)
  i += 1

logger.info("read %d rows total" % i)
