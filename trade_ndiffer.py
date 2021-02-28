from collections import defaultdict

import sortedcontainers


class TradeNDiffer:
  """Reconcile records from multiple log iterators."""
  DT_MISS = 0

  def __init__(self, log_iters, max_jitter, extreme_jitter, reconcile_fields):
    self.log_iters = log_iters
    self.max_jitter = max_jitter
    self.extreme_jitter = extreme_jitter
    self.reconcile_fields = reconcile_fields

  def __iter__(self):
    # the next record from each log iter, sorted by the timestamp of the record
    # each entry is [iter_idx, record]
    self.next_records = sortedcontainers.SortedList(key=lambda x: x[1]['timestamp'])

    # a dict of T_ID -> [rec.log_iter1, ..., rec.log_iterN]
    self.pending_trades = dict()

    # a sorted dict of [timestamp, iter_idx, T_ID] -> True
    self.pending_records = sortedcontainers.SortedDict() # key=lambda x: x[0])

    iter_idx = 0
    for log_iter in self.log_iters:
      self.next_records.add([iter_idx, next(log_iter)])
      iter_idx += 1

    return self 

  def __next__(self):
    if not self.next_records:
      # if there are no more records, flush any partial trades
      for unfinished_trade in self.pending_trades.keys():
        r = self.reconcileTrade(unfinished_trade)
        if r:
          return r
      # and we're done
      raise StopIteration

    while len(self.next_records):
      # if any pending records are past the extreme jitter threshold, note them
      # as having at least one missing related record
      # use the timestamp of the next record from any stream as a basis for the threshold
      (iter_idx, record) = self.next_records[0]
      threshold = record['timestamp'] - self.extreme_jitter
      while self.pending_records and self.pending_records.peekitem(index=0)[0][0] < threshold:
        t_id = self.pending_records.peekitem(index=0)[0][2]
        r = self.reconcileTrade(t_id)
        if r:
          return r

      # get the oldest available record and backfill it if possible
      (iter_idx, record) = self.next_records.pop(0)
      try:
        backfill_record = next(self.log_iters[iter_idx])
        self.next_records.add([iter_idx, backfill_record])
      except StopIteration:
        # it's the end of the iter as we know it
        pass

      # if this trade id hasn't been seen yet, add it to the pending dict
      if record['trade'] not in self.pending_trades:
        self.pending_trades[record['trade']] = [None] * len(self.log_iters)

      if self.pending_trades[record['trade']][iter_idx] is not None:
        raise ValueError('duplicate trade')

      self.pending_trades[record['trade']][iter_idx] = record
      self.pending_records[(record['timestamp'], iter_idx, record['trade'])] = True

      # if we have received this trade from all of the log iters, reconcile it
      if None not in self.pending_trades[record['trade']]:
        r = self.reconcileTrade(record['trade'])
        if r:
          return r

    # apparently we've reconciled the last trade
    raise StopIteration

  def reconcileTrade(self, trade_id):
    timestamps = []
    field_values = defaultdict(set)

    diff_types = []

    for iter_idx in range(0, len(self.log_iters)):
      if self.pending_trades[trade_id][iter_idx] is None:
        diff_types.append('_missing')
      else:
        timestamps.append(self.pending_trades[trade_id][iter_idx]['timestamp'])
        for field in self.reconcile_fields:
          val = self.pending_trades[trade_id][iter_idx][field].lower()
          if val[0] == '-':
            val = val[1:]
          field_values[field].add(val)

    if max(timestamps) - min(timestamps) > self.max_jitter:
      diff_types.append('timestamp')

    for field in self.reconcile_fields:
      if len(field_values[field]) > 1:
        diff_types.append(field)
    
    diff_record = None
    if len(diff_types):
      diff_record = [trade_id, diff_types, self.pending_trades[trade_id]]
    
    iter_idx = 0

    for iter_record in self.pending_trades[trade_id]:
      if iter_record:
        del self.pending_records[(iter_record['timestamp'], iter_idx, trade_id)]
      iter_idx += 1

    del self.pending_trades[trade_id]

    return diff_record
