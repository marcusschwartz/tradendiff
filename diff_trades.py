#!/usr/bin/python3

import logging
import optparse
import sys
import datetime

from trade_ndiffer import TradeNDiffer
from logdir_iter import LogdirIter


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('tradendiff')

parser = optparse.OptionParser()
parser.add_option(
  '--max_jitter_seconds', dest='max_jitter', default=900,
  help='allowable delta between records for the same trade')
parser.add_option(
  '--extreme_jitter_seconds', dest='extreme_jitter', default=3600,
  help='maximum delta between records before reporting a record as missing')
parser.add_option(
  '--reconcile_fields', dest='reconcile_fields',
  default='symbol,price,quantity',
  help='fields to reconcile in addition to timestamp')

(options, args) = parser.parse_args()

log_iters = []
for logdir in args:
  log_iters.append(iter(LogdirIter(path=logdir, logger=logger)))

differ = TradeNDiffer(
  log_iters=log_iters,
  max_jitter=datetime.timedelta(seconds=options.max_jitter),
  extreme_jitter=datetime.timedelta(seconds=options.extreme_jitter),
  reconcile_fields=options.reconcile_fields.split(','),
)

differ.diff()
