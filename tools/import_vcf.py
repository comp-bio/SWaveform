# -*- coding: utf-8 -*-
import sys, os, re, time, sqlite3
from _functions import *
from vcf2score import Variants

options = {
  'db': time.strftime('signal-%Y_%m_%d-%H_%M_%S'),
  'offset': 256,
  'special': 0,
  'spp': 0,
  'genome': 'GRCh38',
  'sample': None,
  'vcf': '',
  'meta': '',
  'name':'TEST'
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
    echo('    offset:[BND offset in bases (integer, >16, default: 256)] \\\n')
    echo('    genome:[human genome version, default GRCh38] \\\n')
    echo('    special:[if SV is less than this parameter, store it as an additional\n')
    echo('      breakpoint with type `SBP`, default: 0*] \\\n')
    echo('    spp:[number from 0 to 1. Specify the center of SV around which offset \n')
    echo('      will be taken, default: 0.5*]\n')
    echo('\n')
    echo('Special breakpoint (`special` & `spp`):\n')
    echo('  If you want to save a signal around a small size SV to the database, you can \n')
    echo('  use the `special` and `spp` options. All SVs greater than the `special` \n')
    echo('  parameter will not be added to the database. `spp` is responsible for the \n')
    echo('  position of the point around which offset will be taken. The point is \n')
    echo('  calculated relative to the SV size: SBP = L + (R - L) * spp. For example, \n')
    echo('  if you specify spp = 0.5, then for the deletion in coordinates 3000–3024, \n')
    echo('  center 3012 and the signal from segment 3012±256 [2756–3268] will be stored \n')
    echo('  in the database\n')
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
offset = max(int(options['offset']), 16)

special = max(int(options['special']), 0)
spp = min(1, max(float(options['spp']), 0))

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
        if R == L:
            signals.append((None, target_id, chr, L - offset, L + offset - 1, sv_type, 'BP', L, gt, ''))
        else:
            signals.append((None, target_id, chr, L - offset, L + offset - 1, sv_type, 'L', R - L, gt, ''))
            signals.append((None, target_id, chr, R - offset, R + offset - 1, sv_type, 'R', R - L, gt, ''))
        if R - L < special:
            SBP = L + int((R - L) * spp)
            signals.append((None, target_id, chr, SBP - offset, SBP + offset - 1, sv_type, 'SBP', SBP, gt, ''))

cur.executemany("INSERT INTO signal VALUES (?,?,?,?,?,?,?,?,?,?)", signals)
con.commit()

echo('Done%s\n' % (" " * 60))
echo('> Signals:     %d\n' % len(signals))
echo('> New targets: %d\n' % len(targets))
if len(samples_not_found) > 0:
    echo('> Samples not found: %s\n' % [k for k in samples_not_found])
for k in counts:
    echo(f'• {k}: {counts[k]}\n')
