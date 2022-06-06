# -*- coding: utf-8 -*-
# Usage: python3 Clusters_KMS_bootstrap.py src:signals.bin sax:128 alphabet:32 window:32 dataset:50 repeats:100  
options = {'src': None, 'sax': 64, 'alphabet': 32, 'window': 32, 'dataset': 50, 'repeats': 1, 'seed': 1337}

import glob, json, os, sys, warnings, random, math, time
import numpy as np
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

from tslearn.preprocessing import TimeSeriesScalerMeanVariance
from tslearn.piecewise import SymbolicAggregateApproximation

# ---------------------------------------------------------------------------- #
for inp in sys.argv[1:]:
    k, v = inp.split(':')
    if k in options: options[k] = v if k == 'src' else int(v)

start_time = time.time()
# ---------------------------------------------------------------------------- #

def read_coverage(f, num = 0):
    fh = open(f, 'rb')
    fh.seek(num * 1024)
    bin = fh.read(1024)
    return [(bin[i] * 256 + bin[i + 1]) for i in range(0, len(bin), 2)]


def read_random(f, count=100, seed=0):
    random.seed(seed)
    index_range = range(int(os.path.getsize(f)/1024))
    return [read_coverage(f, i) for i in random.sample(index_range, min(count, len(index_range) - 1))]


def basis(size, func):
    R = np.arange(0, 2 * math.pi, 2 * math.pi / size)
    return np.array([func(v) for v in R])


def results_save(subs, results):
    mtx = []
    for result in results[0:12]:
        mt_one = []
        for i in result:
            mt_one.append([subs[i].offset, [int(v[0]) for v in subs[i].src]])
        mtx.append(mt_one)
    return mtx

# ---------------------------------------------------------------------------- #

window_step = int(options['window']/8)

sax = SymbolicAggregateApproximation(
    n_segments=options['sax'],
    alphabet_size_avg=options['alphabet'])

sax_motif = SymbolicAggregateApproximation(
    n_segments=options['window'],
    alphabet_size_avg=options['alphabet'])

INF = 999999

def saxdist(idx, idy):
    d_key = f'{min(idx,idy)}:{max(idx,idy)}'
    if d_key not in CACHE:
        CACHE[d_key] = sax.distance_sax(subs[idx].raw, subs[idy].raw)
    return CACHE[d_key]


def clusters_dist(C1, C2):
    sm = INF
    for ixd in C1:
        for ixy in C2:
            sm = min(sm, saxdist(idx, idy))
    return sm

def diam(C):
    mx = 0
    for a in range(0, len(C) - 1):
        for b in range(a, len(C)):
            mx = max(mx, saxdist(C[a], C[b]))
    return mx


def dunn(results):
    if len(results) < 2:
        return [-1, 0, 0]
    total_items = sum([len(C) for C in results])
    D = np.mean([diam(C) for C in results])
    if D == 0: 
        return [INF, total_items, len(results[0])]
    min_dist = INF
    for i in range(0, len(results) - 1):
        for j in range(i, len(results)):
            min_dist = min(min_dist, clusters_dist(results[i], results[j]))
    return [min_dist/D, total_items, len(results[0])]


def make_matrix(subs, result, sax):
    Z = np.zeros((sax.n_segments, sax.alphabet_size_avg))
    for i in result:
        for k, v in enumerate(subs[i].raw):
            Z[k][v[0]] += 1
    return [list(i) for i in Z/len(result)]

# ---------------------------------------------------------------------------- #
repeats = []
for r in range(0, options['repeats']):
    CACHE = {}

    data = np.array(read_random(options['src'], options['dataset'], options['seed'] + r))
    cls = TimeSeriesScalerMeanVariance().fit_transform(data)
    trsf = sax.fit_transform(cls)

    subs = []
    for k, signal in enumerate(trsf):
        for i in range(0, len(signal) - options['window'] + 1, window_step):
            obj = {'raw': signal[i:(i + options['window'])], 'offset': i, 'src': trsf[k]}
            subs.append(type('new_dict', (object,), obj))
    
    cnt = len(subs)
    dms = subs[0].raw.shape[0]
    
    ref_A, ref_B = sax_motif.fit_transform([basis(dms, math.sin), basis(dms, math.cos)])
    d2ref = np.array([[i, sax.distance_sax(obj.raw, ref_A), sax.distance_sax(obj.raw, ref_B)] for i, obj in enumerate(subs)]).reshape(cnt, 3)
    argss = d2ref[:, 1].argsort()
    
    threshold = 0.0
    min_index_dist = 4
    info = []

    for threshold in np.arange(0.2, 8, 0.2):
        sys.stdout.write('\033[1;%sm%s\033[m' % (33, f'R {r+1}/{options["repeats"]}  T {threshold:.2f}/{8}\r'))
        sys.stdout.flush()
        links = np.array([-1 for i in range(cnt)])
        for i, idx in enumerate(argss[:-1]):
            for idy in argss[i+1:]:
                A, B = (d2ref[idx], d2ref[idy])
                if abs(A[0] - B[0]) < min_index_dist: continue
                if abs(A[1] - B[1]) > 2 * threshold: break
                if abs(A[2] - B[2]) > 2 * threshold: break
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
        results = []
        if len(siz) > 0:
            mtf = siz[(-siz[:,0]).argsort()]
            results = [np.where(links == idx)[0] for cnt, idx in mtf]

        info.append({
            'threshold': threshold, 
            'dunn': dunn(results),
            'm': [make_matrix(subs, result, sax_motif) for result in results[0:5]]
        })
        # objx = results_save(subs, results[0:12])
    repeats.append(info)    

# ---------------------------------------------------------------------------- #
sys.stdout.write('\033[1;%sm%s\033[m' % (33, 'Histogram...' + (' ' * 20) + '\r'))
sys.stdout.flush()
step_d = 0.2
max_d  = 20
histogram = [0 for i in range(0, int(max_d/step_d + 1))]
for k in CACHE: 
    histogram[int(min(max_d, CACHE[k])/step_d)] += 1


# ---------------------------------------------------------------------------- #
dir_ = os.path.dirname(os.path.realpath(options['src']))
name = os.path.basename(options['src']).replace('_filterd.bin', '')
out = f"{dir_}/ADA_TR_{name}.d{options['dataset']}_r{options['repeats']}_s{options['seed']}.json".replace('_filterd.bin', '')
with open(out, 'w') as f:
    json.dump(repeats, f)

print('-' * 80)
print(f'Result: {out}')
print(f'Time:   {int((time.time() - start_time)/60)} min.\n')
