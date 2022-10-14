# -*- coding: utf-8 -*-
import sys, os, re, time, sqlite3
from _functions import *
from vcf2score import Variants

options = {
  'db': time.strftime('signal-%Y_%m_%d-%H_%M_%S'),
  'offset': 256,
  'center': 32,
  'all': 256,
  'genome': 'GRCh38',
  'sample': None,
  'vcf': '', 'meta':'', 'name':'TEST'
}
for par in sys.argv[1:]:
    k, v = (par + ':').split(':')[0:2]
    if k in options: options[k] = v

# --------------------------------------------------------------------------- #

if len(options['vcf']) == 0 or len(options['meta']) == 0:
    echo('Usage:\n')
    echo('  python3 %s \\\n' % sys.argv[0])
    echo('    db:[DB path name] \\\n')
    echo('    vcf:[vcf or vcf.gz file] \\\n')
    echo('    meta:[metadata file] \\\n')
    echo('    name:[dataset file] \\\n')
    echo('    center:[if SV size is less than specified, DO NOT keep `L` `R` ends but keep only `C` (32)] \\\n')
    echo('    all:[if SV size is less than specified, keep both BND: `L` R and `C` (256)] \\\n')
    echo('    offset:[BND offset in bases (integer, >16, default: 256)] \\\n')
    echo('    genome:[human genome version, default GRCh38]\n')
    sys.exit(1)

# --------------------------------------------------------------------------- #
# Init DB
if not os.path.isdir(options['db']):
    os.mkdir(options['db'])

con = sqlite3.connect(f"{options['db']}/index.db")
cur = con.cursor()
with open("%s/../data/schema.sql" % os.path.dirname(os.path.realpath(__file__)), 'r') as sql:
    for req in sql.read().split(';'):
        cur.execute(req)

# --------------------------------------------------------------------------- #
samples = {}
metadata = get_lines(options['meta'])
header = next(metadata)
for line in metadata:
    assoc = dict(zip(header, line))
    if 'sample' not in assoc:
        continue
    for label in ['population', 'region', 'sex', 'meancov']:
        if label not in assoc: assoc[label] = ''
    samples[assoc['sample_accession']] = assoc

samples_not_found = {}
offset, m_center, m_all = (max(int(options['offset']), 16), max(int(options['center']), 1), max(int(options['all']), 1))

# Variants
signals = []
targets = []
counts = {}
reader = Variants(filename=options['vcf'])
for chr, L, R, sv_type, rec in reader.info():
    echo('Chr: %s   \r' % chr)
    for sample in rec.samples:
        name = sample.sample
        if options['sample'] != None:
            name = options['sample']
        if name not in samples:
            found_by_ID = False
            if rec.ID:
                pats = rec.ID.split('_')
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
            cur.execute("INSERT INTO target VALUES (?,?,?,?,?,?,?,?,?)",
                (None, name, samples[name]['sample'], options['name'], options['genome'], samples[name]['population'], samples[name]['region'], samples[name]['sex'], samples[name]['meancov'],))
            target_id = cur.lastrowid
            targets.append(name)

        if sv_type == 'CNV':
            if 'data' in sample.__dir__() and 'CNF' in sample.data.__dir__():
                # sv_type = 'CNV_gain' if sample.data.CNF > 1 else 'CNV_loss'
                if sample.data.CNF > 1.5: sv_type = 'CNV_gain'
                if sample.data.CNF < 1.0: sv_type = 'CNV_loss'
                if sv_type == 'CNV': continue

        if sv_type == 'INS':
            L = R

        if sv_type not in counts:
            counts[sv_type] = 0

        counts[sv_type] += 1
        if R - L <= m_all:
            C = round(R - L / 2)
            signals.append((None, target_id, chr, C - offset, C + offset - 1, sv_type, 'C', R - L, gt, ''))
        if R - L > m_center:
            signals.append((None, target_id, chr, L - offset, L + offset - 1, sv_type, 'L', R - L, gt, ''))
            signals.append((None, target_id, chr, R - offset, R + offset - 1, sv_type, 'R', R - L, gt, ''))

cur.executemany("INSERT INTO signal VALUES (?,?,?,?,?,?,?,?,?,?)", signals)
con.commit()

echo('Done%s\n' % (" " * 60))
echo('> Signals:     %d\n' % len(signals))
echo('> New targets: %d\n' % len(targets))
if len(samples_not_found) > 0:
    echo('> Samples not found: %s\n' % [k for k in samples_not_found])
for k in counts:
    echo(f'• {k}: {counts[k]}\n')
