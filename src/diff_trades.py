#!/usr/bin/python3

import logging
import optparse
import sys
import datetime

from trade_ndiffer import TradeNDiffer
from logdir_iter import LogdirIter


def format_diff(diff):
  records = []
  iter_idx = 0
  for logdir in args:
    record = diff[2][iter_idx]
    output = ['[%s]' % logdir]
    if record:
      output.append('timestamp=%s' % record['timestamp'])
      for f in options.reconcile_fields.split(','):
        output.append('%s=%s' % (f, record[f]))
    else:
      output.append('[missing]')
    records.append('%s' % ' '.join(output))
    iter_idx += 1
  return "%s, discrepencies [%s]\n  %s" % (
      diff[0], ','.join(diff[1]), '\n  '.join(records))

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

for diff in differ:
  print(format_diff(diff))
