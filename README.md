# tradendiff - Example code for trade data reconciliation

This is a design and some code that I put together while interviewing
for a real-time trading SRE position with a major hedge fund.  It
represents about one work day of focused effort, and probably too much
polishing.

This code will identify discrepencies found when comparing two or more
sets of trading logs against each other.

## Requirements

* python3 in /usr/bin
* https://pypi.org/project/sortedcontainers installed

## Usage

`./diff_trades.py [options] <logdir1> <logdir2> [... <logdirN>]`

Options

* `--max_jitter_seconds=900` - Maximum allowable delta for timestamps for a 
  single trade across log sets.
* `--extreme_jitter_seconds=3600` - If records for a single trade have a 
  timestamp delta greater than this value, the records will be reported
  as missing.
* `--reconcile_fields=symbol,price,quantity` - A comma-separated list of fields
  that are expected to be "equal" for a single trade across log sets.  Note 
  that the matching is case-insensitive and a single leading - [dash] will be 
  ignored.
* `--include_details` - Include the full log records associated with each 
  reconcilation failure in the output, one record per line.

## Input Data Format

* Each input log set should be in it's own directory.  
* Each input file should contain records for only one day.
* Filenames should begin with the date of the records that they
  contain.  Acceptable formats are YYYYMMDD, MMDDYYYY, and YY-MM-DD.
* Four digit years should be >= 1900
* Two digit years will have 2000 added to them.
* Records should be comma-separated and begin with a field list.
* Each input file should include a 'timestamp' field that s ISO8601
  formatted (time only, no date).
* Each input file should include a 'trade' field that will be used to
  match records across log sets.
* Each input file should contain any other fields that are specified in
  the --reconcile_fields runtime option.

## Complexity Analysis (Roughly)

* n - Total number of records in all log files.
* j - Largest number of trades in any extreme_jitter time period.
* f - Largest number of input files in all log sets for any day.
* Runtime upper bound: O(n + j log j + f log f)
    * Honestly this is a guess, I am not a mathematician and I have not 
      evaluated the algorithms used in the sortedcontainers package.
* Space upper bound: O(j + f)

## Source Files

* diff_trades.py - command line interface for differ
* trade_ndiffer.py - library containing differ logic
* logdir_iter.py - library for accessing a log set as a single iterator
* logdir_cat.py - command line wrapper for logdir_iter.py

## To-Do

* Replace SortedDict with SortedList.
* Add unit tests.
* Investigate alternatives to CsvReader that are more graceful about different
  field types while still being performant.
