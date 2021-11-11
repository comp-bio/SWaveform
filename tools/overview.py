# -*- coding: utf-8 -*-
# Usage: python3 ./overview.py signal.db
import os, sys
import sqlite3
import json
from _functions import *
from _model import *
from hmm_plot import *


con = False
if len(sys.argv) > 1:
    db_file = sys.argv[1]
    con = sqlite3.connect(db_file)
    cur = con.cursor()

if not con:
    echo('Usage:   python3 %s [DB sqlite file]\n' % sys.argv[0])
    echo('Example: python3 %s ./signal.db\n\n' % sys.argv[0])
    sys.exit(1)

# --------------------------------------------------------------------------- #
ret = cur.execute("SELECT COUNT(*) FROM signal").fetchone()
info = {'total': list(ret)[0]}
echo('Total: %d\n' % info['total'])

cur.execute("SELECT COUNT(*), population FROM target GROUP BY population")
info['populations'] = {population:cnt for cnt, population in cur.fetchall()}
echo('Populations: %d\n' % len(info['populations']))

cur.execute("SELECT COUNT(*), type FROM signal GROUP BY type")
info['types'] = {t:cnt for cnt,t in cur.fetchall()}
echo('Types: %d\n' % len(info['types']))

cur.execute(f"SELECT chr, MAX(end) FROM signal GROUP BY chr")
chrx = {chr:mx for chr, mx in cur.fetchall()}

info['density'] = {}
for chr in chrx:
    step = round(chrx[chr]/(1000-1))
    cur.execute(f"SELECT COUNT(*), cast((`start`+256)/{step} as int) AS ro FROM signal WHERE chr = '{chr}' GROUP BY ro")
    density = {int(pos):cnt for cnt, pos in cur.fetchall()}
    all = [(0 if i not in density else density[i]) for i in range(0, 1000)]
    c = chr.replace('chr','')
    info['density'][c] = {'l': all, 'step': step}

with open('build/overview.json', "w") as h:
    json.dump(info, h)

# --------------------------------------------------------------------------- #
if not os.path.isdir('build/models'):
    os.mkdir('build/models')

for side in ['L', 'R']:
    for type in info['types']:
        echo('Type: %s (%s)\n' % (type, side))
        full, matrix, hmm = models(cur, type, side)
        hmm_plot(hmm, matrix, 'build/models/plot.%s-%s.svg' % (type, side))
        with open('build/models/full.%s-%s.json' % (type, side), "w") as h:
            json.dump(full, h)
        with open('build/models/matrix.%s-%s.json' % (type, side), "w") as h:
            json.dump(matrix, h)
        with open('build/models/hmm.%s-%s.json' % (type, side), "w") as h:
            json.dump(hmm, h)

echo('Done\n')
