# -*- coding: utf-8 -*-
import os, sys, glob
import sqlite3
import json
from _functions import *
from _model import *
from _hmm_plot import *


con = False
if len(sys.argv) > 1:
    db_file = sys.argv[1]
    con = sqlite3.connect(db_file)
    cur = con.cursor()

if not con:
    echo('Usage:   python3 %s [DB sqlite file] [filter (F)]\n' % sys.argv[0])
    echo('Example: python3 %s ./signal.db F\n\n' % sys.argv[0])
    sys.exit(1)

# --------------------------------------------------------------------------- #
if len(sys.argv) > 2:
    no_cov = cur.execute("SELECT COUNT(*) FROM signal WHERE coverage = ''").fetchone()[0]
    echo('No coverage signals: %d\n' % no_cov)
    cur.execute("DELETE FROM signal WHERE coverage = ''")
    con.commit()

karyotypes = {}
for js in glob.glob(os.path.dirname(os.path.abspath(__file__)) + "/../data/*.json"):
    kt = open(js, 'r')
    karyotypes[os.path.basename(js).split('.')[0]] = json.load(kt)

# --------------------------------------------------------------------------- #
ret = cur.execute("SELECT COUNT(*) FROM signal").fetchone()
info = {'total': list(ret)[0]}
echo('Total signals: %d\n' % info['total'])

cur.execute("SELECT COUNT(*), dataset, genome_version FROM target GROUP BY dataset")
info['ds'] = {}
echo('Datasets: \n')
for cnt, ds, genome_version in cur.fetchall():
    info['ds'][ds] = {'genome': genome_version}
    echo(' > %s - files: %d\n' % (ds, cnt), color='33')

for ds in info['ds']:
    echo('Dataset: %s\n' % ds)

    cur.execute(f"SELECT COUNT(*), population FROM target WHERE dataset = '{ds}' GROUP BY population")
    info['ds'][ds]['populations'] = {population:cnt for cnt, population in cur.fetchall()}
    echo(' > Populations: %d\n' % len(info['ds'][ds]['populations']), color='33')

    cur.execute(f"SELECT COUNT(signal.id), signal.type FROM signal "
                f"LEFT JOIN target ON target.id = signal.target_id "
                f"WHERE target.dataset = '{ds}' GROUP BY signal.type")
    info['ds'][ds]['types'] = {t:cnt for cnt,t in cur.fetchall()}
    echo(' > Types: %d\n' % len(info['ds'][ds]['types']), color='33')

    info['ds'][ds]['density'] = {}
    chrom = karyotypes[ info['ds'][ds]['genome'] ]
    for chr in chrom:
        chr_len = chrom[chr][-1][1]
        step = round(chr_len/(1000-1))
        cur.execute(f"SELECT COUNT(*), cast((`start`+256)/{step} as int) AS ro FROM signal "
                    f"LEFT JOIN target ON target.id = signal.target_id "
                    f"WHERE (signal.chr = '{chr}' or signal.chr = 'chr{chr}') and target.dataset = '{ds}' GROUP BY ro")
        density = {int(pos):cnt for cnt, pos in cur.fetchall()}
        all = [(0 if i not in density else density[i]) for i in range(0, 1000)]
        c = chr.replace('chr','')
        info['ds'][ds]['density'][c] = {'l': all, 'step': step}

with open('build/overview.json', "w") as h:
        json.dump(info, h)

# --------------------------------------------------------------------------- #
if not os.path.isdir('build/models'):
    os.mkdir('build/models')

echo('Models: \n')
for ds in info['ds']:
    for side in ['L', 'R', 'C']:
        for type in info['ds'][ds]['types']:
            matrix, hmm, total = models(cur, type, side, ds)
            echo(' > %s - %s [%s] (total:%d)\n' % (ds, type, side, total), color='33')
            if total < 32:
                continue
            hmm_plot(hmm, matrix, 'build/models/plot.%s-%s-%s.svg' % (ds, type, side))
            with open('build/models/mat.%s-%s-%s.json' % (ds, type, side), "w") as h:
                json.dump(matrix, h)
            with open('build/models/hmm.%s-%s-%s.json' % (ds, type, side), "w") as h:
                json.dump(hmm, h)

echo('Done\n')
