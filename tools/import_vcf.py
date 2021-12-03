# -*- coding: utf-8 -*-

import sys, os, re
import sqlite3
from _functions import *
from vcf2score import Variants

# --------------------------------------------------------------------------- #
if len(sys.argv) < 5:
    echo('Usage:   python3 %s [DB sqlite file] [vcf file] [metadata] [dataset name]\n' % sys.argv[0])
    echo('Example: python3 %s ./signal.db ./sv.vcf hgdp_structural_variation/HGDP.metadata HGDP\n\n' % sys.argv[0])
    sys.exit(1)

db_file, vcf_file, meta, dataset = sys.argv[1:5]
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
samples = {}
metadata = get_lines(meta)
header = next(metadata)
for line in metadata:
    assoc = dict(zip(header, line))
    if 'sample' not in assoc:
        continue
    for label in ['population', 'region', 'sex', 'meancov']:
        if label not in assoc: assoc[label] = ''
    samples[assoc['sample_accession']] = assoc

samples_not_found = {}

# Variants
signals = []
targets = []
counts = {}
reader = Variants(filename=vcf_file)
for chr, L, R, sv_type, rec in reader.info():
    echo('Chr: %s   \r' % chr)
    for sample in rec.samples:
        name = sample.sample
        if name not in samples:
            pats = rec.ID.split('_')
            found_by_ID = False
            for i in range(len(pats)):
                nm = "_".join(pats[0:len(pats)-i])
                if nm in samples:
                    name = nm
                    found_by_ID = True
                    break
            if not found_by_ID:
                if name not in samples_not_found:
                    print("[!] Not found: " + name)
                samples_not_found[name] = True
                continue

        if not hasattr(sample.data, 'GT'):
            continue

        gt = re.sub('[1-9][0-9]{0,}', '1', sample.data.GT).count('1')
        if sample.data.GT == '-34': gt = -34
        if gt == 0:
            continue

        obj = cur.execute("SELECT * FROM target WHERE name = '%s'" % name).fetchone()
        if obj:
            target_id = obj[0]
        if obj is None:
            cur.execute("INSERT INTO target VALUES (?,?,?,?,?,?,?,?)",
                (None, name, samples[name]['sample'], dataset, samples[name]['population'], samples[name]['region'], samples[name]['sex'], samples[name]['meancov'],))
            target_id = cur.lastrowid
            targets.append(name)

        if sv_type not in counts:
            counts[sv_type] = 0

        counts[sv_type] += 1
        if R - L <= 32:
            C = round(R - L / 2)
            signals.append((None, target_id, chr, C - offset, C + offset - 1, sv_type, 'C', gt, ''))
        else:
            signals.append((None, target_id, chr, L - offset, L + offset - 1, sv_type, 'L', gt, ''))
            signals.append((None, target_id, chr, R - offset, R + offset - 1, sv_type, 'R', gt, ''))

cur.executemany("INSERT INTO signal VALUES (?,?,?,?,?,?,?,?,?)", signals)
con.commit()

echo('Done%s\n' % (" " * 60))
echo('> Signalss:    %d\n' % len(signals))
echo('> New targets: %d\n' % len(targets))
echo('> Samples not found: %s\n' % [k for k in samples_not_found])
print(counts)
