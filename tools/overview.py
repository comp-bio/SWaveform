# -*- coding: utf-8 -*-
import os, sys, glob
import sqlite3
import json
from _functions import *
from _model import *
from _hmm_plot import *

max_hist = 500

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
if not os.path.isdir('build/models'):
    os.mkdir('build/models')

import random, json, warnings
import numpy as np
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

from tslearn.preprocessing import TimeSeriesScalerMeanVariance
from tslearn.piecewise import SymbolicAggregateApproximation


def read_coverage(f, num = 0):
    fh = open(f, "rb")
    fh.seek(num * 1024)
    bin = fh.read(1024)
    return [(bin[i] * 256 + bin[i + 1]) for i in range(0, len(bin), 2)]


def read_random(f, count=100, seed=0):
    random.seed(seed)
    index_range = range(int(os.path.getsize(f)/1024))
    return [read_coverage(f, i) for i in random.sample(index_range, min(count, len(index_range) - 1))]


def type_plot(data, name):
    fig, ax = plt.subplots(figsize=(6, 4))
    opacity = max(10/len(data), 0.002)
    for x in data:
        opacity = 10/len(data)
        ax.plot(x, linewidth=1, alpha=opacity, color='k')
    ax.set_title(os.path.basename(name).replace('_filterd.bin', ''))
    plt.savefig(f'{name}.plt.png', format='png', bbox_inches="tight")
    plt.close()


def empty_hist(size = 500):
    return [0 for i in range(size + 1)]

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

    cur.execute(f"SELECT COUNT(signal.id), signal.type, target.population FROM signal "
                f"LEFT JOIN target ON target.id = signal.target_id "
                f"WHERE target.dataset = '{ds}' GROUP BY signal.type, target.population")

    info['ds'][ds]['types'] = {}
    for cnt, tp, population in cur.fetchall():
        if tp not in info['ds'][ds]['types']: info['ds'][ds]['types'][tp] = {}
        info['ds'][ds]['types'][tp][population] = cnt
    echo(' > Types: %d\n' % len(info['ds'][ds]['types']), color='33')

    # Histogram
    stat = {}
    for population in info['ds'][ds]['populations']:
        echo(f' – {population} – ', color='33')
        stat[population] = {}
        for tp in info['ds'][ds]['types']:
            echo(f'{tp} ', color='33')
            stat[population][tp] = {}
            cur.execute(f"SELECT s.side, s.coverage FROM signal as s "
                        f"LEFT JOIN target as t ON t.id = s.target_id "
                        f"WHERE t.dataset = '{ds}' and t.population = '{population}' and s.type = '{tp}'")
            for side, bin in cur.fetchall():
                if side not in stat[population][tp]:
                    stat[population][tp][side] = {'hist': empty_hist(max_hist), 'count': 0, 'mean': 0}
                coverage = [(bin[i] * 256 + bin[i + 1]) for i in range(0, len(bin), 2)]
                stat[population][tp][side]['count'] += 1
                for v in coverage:
                    stat[population][tp][side]['hist'][min(v, max_hist)] += 1
                    stat[population][tp][side]['mean'] += v/len(coverage)
        echo('\n')

    for population in stat:
        for tp in stat[population]:
            for side in stat[population][tp]:
                stat[population][tp][side]['mean'] /= stat[population][tp][side]['count']

    info['ds'][ds]['stat'] = stat

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
echo('Images: \n')
seed = 1337

sax = SymbolicAggregateApproximation(
    n_segments=128,
    alphabet_size_avg=32)

files = {}
cur.execute(f"SELECT s.coverage, s.size, s.type, s.side FROM signal as s")
for sig, size, tp, side in cur.fetchall():
    if size < 256 and side != 'C': continue
    name = f"build/models/HGDP_{tp}_{side}_filterd.bin"
    if name not in files: files[name] = open(name, 'wb')
    files[name].write(sig)

for name in files:
    echo(f' > {name}\n', color='33')
    files[name].close()
    data = np.array(read_random(name, 5000, seed))
    cls = TimeSeriesScalerMeanVariance().fit_transform(data)
    trsf = sax.fit_transform(cls)
    type_plot(trsf, name)


echo('Done\n')
