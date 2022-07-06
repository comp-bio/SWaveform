# -*- coding: utf-8 -*-
# Usage: python3 Clusters_KMS_bootstrap.py src:signals.bin sax:128 alphabet:32 window:32 dataset:50 repeats:100  

options = {'src': None, 'sax': 64, 'alphabet': 32, 'window': 32, 'dataset': 50, 'repeats': 1}
seed = 1337 * 3

import sys, os, base64, io, math, time
import random, json, warnings
import numpy as np
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

from tslearn.preprocessing import TimeSeriesScalerMeanVariance
from tslearn.piecewise import SymbolicAggregateApproximation
from tslearn.metrics import dtw


def read_coverage(f, num = 0):
    fh = open(f, "rb")
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


def find_KMS_v4(subs, seed, **kwargs):
    if not sax or not sax_motif: 
        return False

    random.seed(seed)
    cnt = len(subs)
    dms = subs[0].raw.shape[0]

    #ref_A = subs[random.choice(range(0, cnt))].raw
    #ref_B = subs[random.choice(range(0, cnt))].raw
    
    ref_A, ref_B = sax_motif.fit_transform([basis(dms, math.sin), basis(dms, math.cos)])
    # ref_A, ref_B = sax_motif.fit_transform([basis(dms, lambda f: -math.sin(f)), basis(dms, lambda f: -math.cos(f))])
    
    d2ref = np.array([[i, sax.distance_sax(obj.raw, ref_A), sax.distance_sax(obj.raw, ref_B)] for i, obj in enumerate(subs)]).reshape(cnt, 3)

    argss = d2ref[:, 1].argsort()
    threshold = 3
    min_index_dist = 4
    links = np.array([-1 for i in range(cnt)])
    default = np.array([[0] for i in range(options['window'])])

    for i, idx in enumerate(argss[:-1]):
        for idy in argss[i+1:]:
            A, B = (d2ref[idx], d2ref[idy])
            if abs(A[0] - B[0]) < min_index_dist: continue
            if abs(A[1] - B[1]) > 2 * threshold: break
            if abs(A[2] - B[2]) > 2 * threshold: break
            
            trv = sax.distance_sax(subs[idx].raw - np.min(subs[idx].raw), default)
            if trv < 2 * threshold: continue

            dst = sax.distance_sax(subs[idx].raw, subs[idy].raw)
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
    if len(siz) == 0: return []

    mtf = siz[(-siz[:,0]).argsort()]
    results = [np.where(links == idx)[0] for cnt, idx in mtf]
    
    return results_save(subs, results[0:12])
    #return [{'m': make_matrix(subs, result, sax_motif), 'items': len(result)} for result in results[0:5]]


# ---------------------------------------------------------------------------- #
for inp in sys.argv[1:]:
    k, v = inp.split(':')
    if k in options: options[k] = v if k == 'src' else int(v)

start_time = time.time()

sax = SymbolicAggregateApproximation(
    n_segments=options['sax'],
    alphabet_size_avg=options['alphabet'])

sax_motif = SymbolicAggregateApproximation(
    n_segments=options['window'],
    alphabet_size_avg=options['alphabet'])

window_step = int(options['window']/8)
dir_ = os.path.dirname(os.path.realpath(options['src']))
name = os.path.basename(options['src']).replace('bin0412/HGDP_','').replace('_filtred.bin', '')

runs = []
for rep in range(0, options['repeats']):
    data = np.array(read_random(options['src'], options['dataset'], seed + rep))
    cls = TimeSeriesScalerMeanVariance().fit_transform(data)
    trsf = sax.fit_transform(cls)
    
    subs = []
    for k, signal in enumerate(trsf):
        for i in range(0, len(signal) - options['window'] + 1, window_step):
            obj = {'raw': signal[i:(i + options['window'])], 'offset': i, 'src': trsf[k]}
            subs.append(type('new_dict', (object,), obj))
    mt = find_KMS_v4(subs, seed=seed)

    results = [{
        'dataset': options['dataset'], 
        'elements': len(data), 
        'subs': len(subs),
        'motif': mt
    }]

    runs.append(results)

# Export
out = f"{dir_}/motif_nocls_{name}_s{options['sax']}-{options['alphabet']}_w{options['window']}_d{options['dataset']}_r{options['repeats']}.json"
with open(out, "w") as f:
    json.dump([runs], f)

print(f"")
print(f"Result: {out}")
print(f"Time:   {int((time.time() - start_time)/60)} min.\n")
