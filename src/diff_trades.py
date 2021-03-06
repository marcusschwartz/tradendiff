#!/usr/bin/python3

import logging
import optparse
import sys
import datetime

from trade_ndiffer import TradeNDiffer
from logdir_iter import LogdirIter


def format_diff(diff, include_details):
  formatted = "%s, discrepencies [%s]" % (diff[0], ','.join(diff[1]))
  if include_details:
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
    formatted = '%s\n  %s' % (formatted, '\n  '.join(records))

  return formatted


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('tradendiff')

parser = optparse.OptionParser()
parser.add_option(
    '--max_skew_seconds', dest='max_skew', default=900,
    help='allowable delta between records for the same trade')
parser.add_option(
    '--extreme_skew_seconds', dest='extreme_skew', default=3600,
    help='maximum delta between records before reporting a record as missing')
parser.add_option(
    '--reconcile_fields', dest='reconcile_fields',
    default='symbol,price,quantity',
    help='fields to reconcile in addition to timestamp')
parser.add_option(
    '--include_details', dest='include_details', action='store_true',
    help='include the full records for each reconciliation failure')

(options, args) = parser.parse_args()

log_iters = []
for logdir in args:
  log_iters.append(iter(LogdirIter(path=logdir, logger=logger)))

differ = TradeNDiffer(
    log_iters=log_iters,
    max_skew=datetime.timedelta(seconds=options.max_skew),
    extreme_skew=datetime.timedelta(seconds=options.extreme_skew),
    reconcile_fields=options.reconcile_fields.split(','),
)

for diff in differ:
  print(format_diff(diff, options.include_details))
