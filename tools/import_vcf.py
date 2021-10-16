# -*- coding: utf-8 -*-

import sys, os, re
import sqlite3
from _functions import *
from vcf2score import Variants

# --------------------------------------------------------------------------- #
if len(sys.argv) < 4:
    echo('Usage:   python3 %s [DB sqlite file] [vcf file] [metadata]\n' % sys.argv[0])
    echo('Example: python3 %s ./signal.db ./sv.vcf hgdp_structural_variation/HGDP.metadata\n\n' % sys.argv[0])
    sys.exit(1)

db_file, vcf_file, meta = sys.argv[1:4]
offset = 256

# --------------------------------------------------------------------------- #
# Init DB
con = sqlite3.connect(db_file)
cur = con.cursor()
loc = os.path.dirname(os.path.realpath(__file__))
with open("%s/../data/schema.sql" % loc, 'r') as sql:
    for req in sql.read().replace('\n', '').split(';'):
        cur.execute(req)

# --------------------------------------------------------------------------- #
metadata = get_lines(meta)
header = next(metadata)
samples = {line[2]:([line[0]]+line[6:]) for line in metadata}

# Variants
signals = []
targets = []
counts = {}
reader = Variants(vcf_file)
for chr, L, R, sv_type, rec in reader.info():
    echo('Chr: %s   \r' % chr)
    for sample in rec.samples:
        name = sample.sample
        if name not in samples:
            continue

        gt = re.sub('[1-9][0-9]{0,}', '1', sample.data.GT).count('1')
        if gt == 0:
            continue

        obj = cur.execute("SELECT * FROM target WHERE name = '%s'" % name).fetchone()
        if obj:
            target_id = obj[0]
        if obj is None:
            cur.execute("INSERT INTO target VALUES (?,?,?,?,?,?,?)", (None, name,) + tuple(samples[name]))
            target_id = cur.lastrowid
            targets.append(name)

        if sv_type not in counts:
            counts[sv_type] = 0

        counts[sv_type] += 1
        if R - L <= 64:
            C = round(R - L / 2)
            signals.append((None, target_id, chr, C - offset, C + offset - 1, sv_type, 'C', gt, ''))
        else:
            signals.append((None, target_id, chr, L - offset, L + offset - 1, sv_type, 'L', gt, ''))
            signals.append((None, target_id, chr, R - offset, R + offset - 1, sv_type, 'R', gt, ''))

cur.executemany("INSERT INTO signal VALUES (?,?,?,?,?,?,?,?,?)", signals)
con.commit()

echo('Done%s\n' % (" " * 60))
echo('> Variants:    %d\n' % len(signals))
echo('> New targets: %d\n' % len(targets))
print(counts)
