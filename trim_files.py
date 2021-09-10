#!/usr/bin/env python3

import sys
from pathlib import Path
import tempfile
import shutil
from subprocess import check_output
from datetime import datetime, timedelta

def co(cmd):
    return check_output(cmd, shell=True).decode('utf-8')

def trim_file(fn_in, fn_out, days_to_keep):
    """Shortens the file with the name 'fn_in' and creates a new file
    'fn_out' (which can be the same file name as the input file).  The trailing
    lines from 'fn_in' are taken, starting at the first line from the day
    Now - 'days_to_keep'.  The file must have a date in each line having the
    format YYYY-MM-DD
    """

    with tempfile.TemporaryDirectory() as tmp:
        temp_p = Path(tmp) / 'trimmed-file'

        st_date = datetime.now() - timedelta(days=days_to_keep)
        st_str = st_date.strftime('%Y-%m-%d')

        res = co(f'grep -n {st_str} {fn_in} | head -n1')
        st_line = res.split(':')[0]

        co(f'head -n1 {fn_in} > {temp_p}')            # put header row in output file
        co(f'tail -n +{st_line} {fn_in} >> {temp_p}')
        shutil.copy(str(temp_p), str(fn_out))  # str() in case Python <=3.7

if __name__ == '__main__':
    # Allows command line use of this module:
    #
    #     ./trim_files.py <input file name> <output file name> <# of days to keep>
    fn_in, fn_out, days = sys.argv[1:]
    trim_file(fn_in, fn_out, float(days))
