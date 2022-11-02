# -*- coding: utf-8 -*-
# pip3 install matplotlib numpy tslearn
# Usage: python3 Clusters_ADAKMS_bootstrap.py \
#   src:signals.bin sax:128 alphabet:32 window:32 dataset:50 repeats:100

import sqlite3
import tracemalloc
import sys, os, base64, io, math, time
import random, json, warnings

# --------------------------------------------------------------------------- #
start_time = time.time()
options = {'db': '', 'name': '', 'type': '', 'side': 'BP', 'sax': 64, 'alphabet': 24, 'window': 32, 'dataset': 400, 'repeats': 20, 'seed': 1337}
for par in sys.argv[1:]:
    k, v = (par + ':').split(':')[0:2]
    if k in options:
        options[k] = v if k in ['db', 'type', 'side', 'name'] else int(v)

db = f"{options['db']}/index.db"
bc = f"{options['db']}/storage.bcov"

def echo(text, color='37'):
    sys.stdout.write("\033[1;%sm%s\033[m" % (color, text))
    sys.stdout.flush()

def usage():
    echo('Usage:\n')
    echo('  python3 %s \\\n' % sys.argv[0])
    echo('    db:[DB path name] \\\n')
    echo('    name:[dataset name] \\\n')
    echo('    type:[SV type. ex: DEL] \\\n')
    echo('    side:[SV side. L, R or BP] \\\n')
    echo('    sax:[SAX-transform width, default: 64] \\\n')
    echo('    alphabet:[SAX-transform height (alphabet size), default: 24] \\\n')
    echo('    window:[motif width, default: 32] \\\n')
    echo('    dataset:[signals count for each run, default: 400] \\\n')
    echo('    repeats:[repeats count for bootstrap, default: 20] \\\n')
    echo('    seed:[seed for K-means]\n')
    exit(1)

if options['db'] == '':
    echo(f"Error:\n", 31)
    echo(f"  Database not found! (db:./path-to-db)\n\n", 31)
    usage()

con = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
cur = con.cursor()
coverage = open(bc, 'rb')

if options['type'] == '':
    cur.execute("SELECT t.dataset, s.type, s.side FROM `signal` as s "
        "LEFT JOIN `target` as t ON s.target_id = t.id "
        "GROUP BY t.dataset, s.type, s.side")

    names = {}
    for name, tp, side in cur.fetchall():
        if name not in names: names[name] = []
        names[name].append([tp, side])
    echo(f"Types for {options['db']}:\n")
    for name in names:
        echo(f"  name:{name}\n")
        for tp, side in names[name]:
            echo(f"    type:{tp} side:{side}\n")
    echo('\n')
    usage()

# --------------------------------------------------------------------------- #
import numpy as np
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
tracemalloc.start()

from tslearn.preprocessing import TimeSeriesScalerMeanVariance
from tslearn.piecewise import SymbolicAggregateApproximation
from tslearn.clustering import TimeSeriesKMeans
from tslearn.metrics import dtw

INF = 999999
CACHE = {}

def read_random(count=100):
    cur.execute("SELECT s.coverage_offset, s.start, s.end FROM `signal` as s "
        "LEFT JOIN `target` as t ON s.target_id = t.id "
        f"WHERE t.dataset = '{options['name']}' and s.type = '{options['type']}' and s.side = '{options['side']}' "
        f"ORDER BY random() LIMIT {count}")
    signals = []
    for pos, l, r in cur.fetchall():
        coverage.seek(pos * 2, 0)
        bin = coverage.read((r - l + 1) * 2)
        if (len(bin) != 1024):
            print(pos * 2, r, l, len(bin), 'ALARM')
            sys.exit(1)
        signals.append([(bin[i] * 256 + bin[i + 1]) for i in range(0, len(bin), 2)])
    return signals


def basis(size, func):
    R = np.arange(0, 2 * math.pi, 2 * math.pi / size)
    return np.array([func(v) for v in R])


def compress(sig, K=2):
    return [sum(sig[i:i+K])/K for i in range(0, len(sig), K)]


def make_matrix(subs, result, sax):
    Z = np.zeros((sax.n_segments, sax.alphabet_size_avg))
    for i in result:
        for k, v in enumerate(subs[i].raw):
            Z[k][v[0]] += 1
    return [list(i) for i in Z/len(result)]


def results_save(subs, results):
    mtx = []
    for result in results[0:12]:
        mt_one = []
        for i in result:
            mt_one.append([subs[i].offset, [int(v[0]) for v in subs[i].src]])
        mtx.append(mt_one)
    return mtx


def saxdist(idx, idy):
    d_key = f'{min(idx,idy)}:{max(idx,idy)}'
    if d_key not in CACHE:
        CACHE[d_key] = sax.distance_sax(subs[idx].raw, subs[idy].raw)
    return CACHE[d_key]


def clusters_dist(C1, C2):
    sm = INF
    for idx in C1:
        for idy in C2:
            sm = min(sm, saxdist(idx, idy))
    return sm


def diam(C):
    mx = 0
    for a in range(0, len(C) - 1):
        for b in range(a, len(C)):
            mx = max(mx, saxdist(C[a], C[b]))
    return mx


def find_KMS_v5(subs, seed, **kwargs):
    if not sax or not sax_motif:
        return False

    cnt = len(subs)
    dms = subs[0].raw.shape[0]

    ref_A, ref_B = sax_motif.fit_transform([basis(dms, math.sin), basis(dms, math.cos)])
    d2ref = np.array([[i, sax.distance_sax(obj.raw, ref_A), sax.distance_sax(obj.raw, ref_B)] for i, obj in enumerate(subs)]).reshape(cnt, 3)

    argss = d2ref[:, 1].argsort()
    min_index_dist = 4
    default = np.array([[0] for i in range(options['window'])])

    CACHE = {}
    saxs = []
    use_cnt = max(int(cnt/20), 90)
    for i in range(0, use_cnt):
        for j in range(i, use_cnt):
            sd = saxdist(i, j)
            if sd > 0: saxs.append(saxdist(i, j))
    quantile_use = [0.015, 0.020, 0.025]
    quantile_use = [0.015]
    #print(saxs)
    #print(np.quantile(saxs, 0.015))

    info = []
    for q in quantile_use:
        threshold = np.quantile(saxs, q)
        threshold = max(threshold, 0.1)

        sys.stdout.write('\033[1;%sm%s\033[m' % (33, f'R {rep+1}/{options["repeats"]}  T:{threshold:.2f}  Q:{q}   \r'))
        sys.stdout.flush()
        links = np.array([-1 for i in range(cnt)])

        for i, idx in enumerate(argss[:-1]):
            for idy in argss[i+1:]:
                A, B = (d2ref[idx], d2ref[idy])
                if abs(A[0] - B[0]) < min_index_dist: continue
                if abs(A[1] - B[1]) > 2 * threshold: break
                if abs(A[2] - B[2]) > 2 * threshold: break

                trv = sax.distance_sax(subs[idy].raw - np.min(subs[idy].raw), default)
                # (subs[idy].raw - np.mean(subs[idy].raw)).mean()
                if trv < 2 * threshold: continue

                dst = saxdist(idx, idy)
                if dst > threshold: continue

                parent = max(links[idx], links[idy])
                if parent == -1:
                    parent = max(idx, idy)
                for cng in [idx, idy]:
                    if links[cng] == -1:
                        links[cng] = parent
                    if links[cng] != parent:
                        links[links == links[cng]] = parent

        motif = {}
        for idx in links[links != -1]:
            if idx not in motif: motif[idx] = 0
            motif[idx] += 1

        siz = np.array([[motif[v], v] for v in motif])
        if len(siz) == 0:
            info.append({
                'quantile': q,
                'threshold': threshold,
                'motif': []
            })
            continue

        mtf = siz[(-siz[:,0]).argsort()]
        results = [np.where(links == idx)[0] for cnt, idx in mtf]

        info.append({
            'quantile': q,
            'threshold': threshold,
            'motif': results_save(subs, results[0:5])
        })
    return info


# --------------------------------------------------------------------------- #
sax = SymbolicAggregateApproximation(
    n_segments=options['sax'],
    alphabet_size_avg=options['alphabet'])

sax_motif = SymbolicAggregateApproximation(
    n_segments=options['window'],
    alphabet_size_avg=options['alphabet'])

window_step = max(1, int(options['window']/8))

runs = []
for rep in range(0, options['repeats']):
    data = np.array(read_random(options['dataset']))
    if (len(data) == 0):
        echo(f"[!] No coverage data found for: {options['type']}\n")
        continue
    scld = TimeSeriesScalerMeanVariance().fit_transform([compress(sig, 8) for sig in data])

    model = TimeSeriesKMeans(n_clusters=2, n_init=1, metric="dtw", random_state=options['seed'], n_jobs=32)
    pred = model.fit_predict(scld)

    results = []
    for cls_index in [0, 1]:
        cls = TimeSeriesScalerMeanVariance().fit_transform(data[pred == cls_index])
        trsf = sax.fit_transform(cls)
        subs = []
        for k, signal in enumerate(trsf):
            for i in range(0, len(signal) - options['window'] + 1, window_step):
                obj = {'raw': signal[i:(i + options['window'])], 'offset': i, 'src': trsf[k]}
                subs.append(type('new_dict', (object,), obj))
        mt = find_KMS_v5(subs, seed=options['seed'])
        results.append({
            'cls': cls_index, 
            'cls_mean': [v[0] for v in np.mean(scld[pred == cls_index], axis=0)],
            'cls_std': [v[0] for v in np.std(scld[pred == cls_index], axis=0)],
            'dataset': options['dataset'], 
            'elements': len(cls), 
            'subs': len(subs),
            'motif': mt
        })

    runs.append(results)

# Export
if not os.path.exists(f"{options['db']}/adakms"): os.makedirs(f"{options['db']}/adakms")
name = "_".join([options['name'], options['type'], options['side']])
out = f"{options['db']}/adakms/{name}_s{options['sax']}-{options['alphabet']}_w{options['window']}_d{options['dataset']}_r{options['repeats']}_s{options['seed']}.json"
with open(out, "w") as f:
    json.dump(runs, f)

m_cur, m_max = tracemalloc.get_traced_memory()
sec_ = int(time.time() - start_time)
min_ = int(sec_/60)

echo(f"Time:   {min_} min. ({sec_} sec.)\n")
echo(f"Memory: {int(m_max/1024/1024)}MB\n")
echo(f"Result: {out}\n\n")
