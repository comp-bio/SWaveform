# -*- coding: utf-8 -*-
import os, sys, glob, sqlite3, json
from _functions import *

options = {'db': '', 'max_hist': 500, 'order': ''}
for par in sys.argv[1:]:
    k, v = (par + ':').split(':')[0:2]
    if k in options: options[k] = v

db = f"{options['db']}/index.db"
bc = f"{options['db']}/storage.bcov"
max_hist = int(options['max_hist'])
con = False
if options['db'] != '':
    con = sqlite3.connect(db)
    cur = con.cursor()

if not con or not os.path.isfile(db) or not os.path.isfile(bc):
    echo('Usage:\n')
    echo('  python3 %s \\\n' % sys.argv[0])
    echo('    db:[DB directory]\n')
    sys.exit(1)

# --------------------------------------------------------------------------- #
coverage = open(bc, 'rb')
count = cur.execute("SELECT COUNT(*) FROM signal WHERE coverage_offset = ''").fetchone()[0]
echo('No coverage signals: %d\n' % count)
cur.execute("DELETE FROM signal WHERE coverage_offset = ''")
con.commit()

root = os.path.dirname(os.path.abspath(__file__)) + "/../"
karyotypes = {}
for js in glob.glob(root + "data/*.json"):
    kt = open(js, 'r')
    karyotypes[os.path.basename(js).split('.')[0]] = json.load(kt)

# --------------------------------------------------------------------------- #
echo('Images: \n')

from tslearn.preprocessing import TimeSeriesScalerMeanVariance
from tslearn.piecewise import SymbolicAggregateApproximation
import matplotlib.pyplot as plt

if not os.path.exists(f"{options['db']}/media"):
    os.makedirs(f"{options['db']}/media")

def type_plot(data, name, code):
    fig, ax = plt.subplots(figsize=(6, 4))
    opacity = min(1, max(10/len(data), 0.002))
    for x in data:
        ax.plot(x, linewidth=1, alpha=opacity, color='k')
    ax.set_title(code.replace('_', ' ').replace('gt1', ' (het)').replace('gt2', ' (hom)'))
    ax.set_xlim((0,127))
    ax.set_ylim((0,23))
    plt.savefig(f"{options['db']}/media/{name}_{code}.plt.png", format='png', bbox_inches="tight")
    plt.close()


seed = 1337
sax = SymbolicAggregateApproximation(n_segments=128, alphabet_size_avg=24)
cur.execute("SELECT t.dataset, s.type, s.side FROM `signal` as s "
    "LEFT JOIN `target` as t ON s.target_id = t.id "
    "GROUP BY t.dataset, s.type, s.side")

datasets = {}
for name, tp, side in cur.fetchall():
    if name not in datasets: datasets[name] = []
    datasets[name].append([tp, side])

datasets_names = []
ordered = []
if options['order']:
    for code in options['order'].split(','):
        if code in datasets:
            datasets_names.append(code)
            ordered.append(code)
for code in datasets:
    if code not in ordered:
        datasets_names.append(code)

count = 800
for name in datasets:
    for tp, side in datasets[name]:
        for gt in ['1', '2']:
            cur.execute("SELECT s.coverage_offset, s.start, s.end FROM `signal` as s "
                "LEFT JOIN `target` as t ON s.target_id = t.id "
                f"WHERE t.dataset = '{name}' and s.type = '{tp}' and s.side = '{side}' and s.genotype = {gt} "
                f"ORDER BY random() LIMIT {count}")
            signals = []
            for pos, l, r in cur.fetchall():
                coverage.seek(pos * 2, 0)
                bin = coverage.read((r - l + 1) * 2)
                signals.append([(bin[i] * 256 + bin[i + 1]) for i in range(0, len(bin), 2)])
            echo(f"– img: {name} {tp}_{side}_gt{gt} (" +str(len(signals))+ ")\n")
            if len(signals) > 0:
                cls = TimeSeriesScalerMeanVariance().fit_transform(signals)
                trsf = sax.fit_transform(cls)
                type_plot(trsf, name, f"{tp}_{side}_gt{gt}")

# --------------------------------------------------------------------------- #
ret = cur.execute("SELECT COUNT(*) FROM signal").fetchone()
info = {'total': list(ret)[0], 'ds_names': datasets_names, 'ds': {}}
echo('Total signals: %d\n' % info['total'])

cur.execute("SELECT COUNT(*), dataset, genome_version FROM target GROUP BY dataset")
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
            cur.execute(f"SELECT s.side, s.start, s.end, s.coverage_offset FROM signal as s "
                        f"LEFT JOIN target as t ON t.id = s.target_id "
                        f"WHERE t.dataset = '{ds}' and t.population = '{population}' and s.type = '{tp}'")
            for side, l, r, pos in cur.fetchall():
                if side not in stat[population][tp]:
                    stat[population][tp][side] = {'hist': [0 for i in range(max_hist + 1)], 'count': 0, 'mean': 0}

                coverage.seek(pos * 2)
                bin = coverage.read((r - l + 1) * 2)
                cov = [(bin[i] * 256 + bin[i + 1]) for i in range(0, len(bin), 2)]
                stat[population][tp][side]['count'] += 1
                for v in cov:
                    stat[population][tp][side]['hist'][min(v, max_hist)] += 1
                    stat[population][tp][side]['mean'] += v/len(cov)
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

with open(f"{options['db']}/overview.json", "w") as h:
    json.dump(info, h)

echo('Done\n')
