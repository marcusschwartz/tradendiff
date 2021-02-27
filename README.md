# tradendiff - Example code for trade data reconciliation

This is some code that I put together while interviewing for a real-time 
trading SRE position with a major hedge fund.  It represents about two
hours of design work, five hours of focused coding, thirty minutes of
documentation, and probably too much polishing.

This code will identify discrepencies found when comparing two or more
sets of trading logs against each other.

## Requirements

* python3 in /usr/bin
* https://pypi.org/project/sortedcollections installed

## Usage

`./diff_trades.py [options] <logdir1> <logdir2> [... <logdirN>]`

Options

* --max_jitter_seconds - Maximum allowable delta for timestamps for a 
  single trade across log sets.
* --extreme_jitter_seconds - If records for a single trade have a 
  timestamp delta greater than this value, the records will be reported
  as missing.
* --reconcile_fields - A comma-separated list of fields that are expected
  to be "equal" for a single trade across log sets.  Note that the matching
  is case-insensitive and a single leading - [dash] will be ignored.

## Input Data Format

* Each input log set should be in it's own directory.  
* Each input file should contain records for only one day.
* Filenames should begin with the date of the records that they
  contain.  Acceptable formats are YYYYMMDD, MMDDYYYY, and YY-MM-DD.
* Four digit years should be >= 1900
* Two digit years will have 2000 added to them.
* Input files should be comma-separated.
* Each input file should include a 'timestamp' field that s ISO8601
  formatted (time only, no date).
* Each input file should include a 'trade' field that will be used to
  match records across log sets.
* Each input file should contain any other fields that are specified in
  the --reconcile_fields runtime option.

## Complexity Analysis (Roughly)

* n - Total number of records in all log files.
* j - Largest number of trades in any extreme_jitter time period.
* Runtime upper bound: O(n + j log j)
** Honestly this is a guess, I am not a mathematician and I have not evaluated
   the algorithms used in the sortedcollections package.
* Space upper bound: O(j)

## To-Do

* Investigate alternatives to CsvReader that are more graceful about different
  field types while still being performant.
