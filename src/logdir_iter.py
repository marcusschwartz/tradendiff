import os
import csv
import re
import datetime
import logging
from collections import defaultdict

from sortedcontainers import SortedList


class LogdirIter:
  """Present a directory full of csv log files as a sorted iter of records.

     Each log file must have an ISO-formatted 'timestamp' column.

     Log filenames must begin with either YYYYMMDD, MMYYDDDD, or YY-MM-DD.
     Dates earlier than 1900 may have unexpected behavior.
     Two-digit years will have 2000 added to them.
  """

  def __init__(self, path, o_id=None, logger=None):
    self.o_id = o_id  # a unique human-readable descriptor for this stream
    self.path = path  # the path where the log files reside

    if logger:
      self.logger = logger
    else:
      self.logger = logging.getLogger('LogdirIter')

    if o_id:
      self.o_id = o_id
    else:
      self.o_id = path

    # a mapping of dates to files containing their records
    self.files_by_date = None
    self.remaining_dates = None  # the dates that haven't been processed yet
    self.active_date = None  # the date we are currently streaming
    self.active_readers = None  # the csv readers for the active date
    self.reader_counts = None  # the count of returned records for each reader
    self.total_count = None  # total count of returned records
    # the next record from each file in the current date
    self.next_records = None

  def __iter__(self):
    """Reset the iterator state."""
    self.files_by_date = self.loadFileDates()
    self.remaining_dates = sorted(self.files_by_date.keys())
    self.active_date = None
    self.active_readers = None
    self.next_records = SortedList(key=lambda x: x[1])
    self.total_count = 0

    return self

  def __next__(self):
    """Get the next log record."""
    if not len(self.next_records):
      self.nextDate()

    (reader_id, next_ts, next_record) = self.next_records.pop(0)

    # read the next record from the file that gave us this record, or close it
    try:
      record = next(self.active_readers[reader_id])
      ts = datetime.time.fromisoformat(record['timestamp'])
      self.next_records.add([reader_id, ts, record])
    except StopIteration:
      # that reader is done
      self.logger.info("[%s] [%s] read %d records" % (
          self.o_id,
          self.files_by_date[self.active_date][reader_id].name,
          self.reader_counts[reader_id]))
      pass

    # maintain some debugging stats
    self.reader_counts[reader_id] += 1
    self.total_count += 1

    next_record['timestamp'] = datetime.datetime.combine(
        self.active_date, next_ts)
    return next_record

  def nextDate(self):
    """Start processing the next available date."""

    # are we at the end of the logdir?
    if not self.remaining_dates:
      logging.info("[%s] %d records processed" %
                   (self.o_id, self.total_count))
      raise StopIteration

    self.active_date = self.remaining_dates.pop(0)
    logging.info("[%s] processing date %s" %
                 (self.o_id, self.active_date))

    self.active_readers = list()
    self.reader_counts = list()

    # open all of the logs for this date
    for f in self.files_by_date[self.active_date]:
      fd = open(f)
      reader = csv.DictReader(fd)
      self.active_readers.append(reader)
      self.logger.debug("[%s] opened reader for %s" %
                        (self.o_id, f.name))

    # read the first record from each log file
    for i in range(0, len(self.active_readers)):
      record = next(self.active_readers[i])
      ts = datetime.time.fromisoformat(record['timestamp'])
      self.next_records.add([i, ts, record])
      self.reader_counts.append(0)

  def dateFromPath(self, path):
    """Try to guess at the date of the logs based on the filename.

       WARNING: This logic is kind of clowny.  Why do we allow 
       YYYYMMDD and MMDDYYYY in the same directory but not
       YYYYDDMM or DDMMYYYY?
    """
    basename = os.path.basename(path)

    # YYYYDDMM
    m = re.match('^(\d{4})(\d{2})(\d{2})', basename)
    if m and int(m.group(1)) >= 1900:
      return datetime.date(int(m.group(1)), int(m.group(2)),
                           int(m.group(3)))

    # MMDDYYYY
    m = re.match('^(\d{2})(\d{2})(\d{4})', basename)
    if m:
      return datetime.date(int(m.group(3)), int(m.group(1)),
                           int(m.group(2)))

    # YY-MM-DD
    m = re.match('^(\d{2})-(\d{2})-(\d{2})', basename)
    if m:
      return datetime.date(int(m.group(1)) + 2000, int(m.group(2)),
                           int(m.group(3)))

    raise ValueError('unexpected filename format')

  def loadFileDates(self):
    """Find all filenames that we can parse a date from."""
    files_by_date = defaultdict(list)
    filecount = 0

    with os.scandir(self.path) as d:
      for p in d:
        if not p.is_file():
          continue
        try:
          d = self.dateFromPath(p)
          self.logger.debug(
              '[%s] found input file "%s" [date: %s]' % (self.o_id, p.name, d))
          files_by_date[d].append(p)
          filecount += 1
        except Exception as e:
          self.logger.warning(
              '[%s] ingoring input file "%s": %s' % (self.o_id, p.name, e))

    self.logger.info("[%s] found %d input files for %d dates" %
                     (self.o_id, filecount, len(files_by_date)))
    return files_by_date
