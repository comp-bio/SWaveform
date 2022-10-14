# -*- coding: utf-8 -*-
import sys, os, re
import sqlite3, gzip
from _functions import *

options = {'db': '', 'path': '', 'name': ''}
for par in sys.argv[1:]:
    k, v = (par + ':').split(':')[0:2]
    if k in options: options[k] = v

# --------------------------------------------------------------------------- #
if options['db'] == '' or not os.path.isfile(f"{options['db']}/index.db"):
    echo('Usage:\n')
    echo('  python3 %s \\\n' % sys.argv[0])
    echo('    db:[DB directory] \\\n')
    echo('    path:[coverage directory] \\\n')
    echo('    name:[dataset name]\n')
    sys.exit(1)

# --------------------------------------------------------------------------- #
con = sqlite3.connect(f"{options['db']}/index.db")
cur = con.cursor()
storage = open(f"{options['db']}/storage.bcov", 'ab')
storage_offset = int(os.path.getsize(f"{options['db']}/storage.bcov")/2)

# --------------------------------------------------------------------------- #
filter = f" WHERE dataset = '{options['name']}'" if options['name'] != '' else ""
cur.execute("SELECT id, name, file FROM target" + filter)

notfound = {}
total = 0
no_coverage = 0
for t_id, name, file in cur.fetchall():
    total += 1
    echo('Target: %s -> %s [%d]%s\r' % (name, file, total, " " * 60))

    cur.execute(f"SELECT id, chr, start, end FROM signal WHERE target_id = {t_id:d}")
    for id, chr, start, end in cur.fetchall():
        if start < 0: continue
        if chr[0:3] == 'chr': chr = chr[3:]
        cov_file = "%s/%s/%s.bcov" % (options['path'], file, chr)
        if not os.path.isfile(cov_file):
            cov_file = "%s/%s/chr%s.bcov" % (options['path'], file, chr)
        if not os.path.isfile(cov_file):
            notfound[cov_file] = True
            continue
        bytes = 2 * (end - start + 1)
        with open(cov_file, 'rb') as f:
            f.seek(start * 2)
            bin_data = f.read(bytes)
        if bin_data == bytearray([0 for i in range(bytes)]):
            cur.execute(f"DELETE FROM signal WHERE id = ?", (id,))
            no_coverage += 1
            continue
        if len(bin_data) != (end - start + 1) * 2:
            cur.execute(f"DELETE FROM signal WHERE id = ?", (id,))
            no_coverage += 1
            continue
        cur.execute(f"UPDATE signal set coverage_offset = ? WHERE id = ?", (storage_offset, id,))
        storage_offset += (end - start + 1)
        storage.write(bin_data)

storage.close()
con.commit()
echo('Done%s\n' % (" " * 60))

skp = " ".join([f for f in notfound])
if skp != "": echo('Chromosome coverage files not found:\n%s\n' % skp)
echo('No coverage: %d\n' % no_coverage)
