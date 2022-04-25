# -*- coding: utf-8 -*-
# Usage: python3 Clusters_Compress.py filename repeats

import sys, os, time
import random, json, warnings

warnings.filterwarnings("ignore")
seed = 3 * 1337
K = 8

from tslearn.clustering import TimeSeriesKMeans
from tslearn.preprocessing import TimeSeriesScalerMeanVariance


def read_coverage(f, num = 0):
    fh = open(f, "rb")
    fh.seek(num * 1024)
    bin = fh.read(1024)
    return [(bin[i] * 256 + bin[i + 1]) for i in range(0, len(bin), 2)]


def read_random(f, count=100, seed=0):
    random.seed(seed)
    index_range = range(int(os.path.getsize(f)/1024))
    return [read_coverage(f, i) for i in random.sample(index_range, min(count, len(index_range) - 1))]


def compress(sig, K=2):
    return [sum(sig[i:i+K])/K for i in range(0, len(sig), K)]


def fit(data, seed):
    model = TimeSeriesKMeans(n_clusters=2, n_init=1, metric="dtw", random_state=seed, n_jobs=32)
    return model.fit_predict(TimeSeriesScalerMeanVariance().fit_transform(data))


def test(dataset_size, K, repeats, seed):
    S, C = ([],[],)
    for r in range(repeats):
        dt = read_random(src, dataset_size, seed + r)
        C0 = fit(dt, seed + r)
        C1 = fit(dt, seed + r + 1)
        C2 = fit([compress(sig, K) for sig in dt], seed + r)
        S.append(max(sum(C0 == C1), sum(C0 != C1))/dataset_size)
        C.append(max(sum(C0 == C2), sum(C0 != C2))/dataset_size)
    return [dataset_size, S, C]


# ---------------------------------------------------------------------------- #
src, repeats = (sys.argv[1], int(sys.argv[2]),)
dir, name = (os.path.dirname(os.path.realpath(src)), os.path.basename(src).replace("_filterd.bin", ""))

start_time = time.time()
dataset_sizes = [2, 100]
stat = [test(size, K, repeats, seed) for size in dataset_sizes]

out = f"{dir}/compress_{name}.json"
with open(out, "w") as f:
    json.dump(stat, f)

print(f"Repeats:  {repeats}")
print(f"Time:     {int((time.time() - start_time)/60)} min.\n")
