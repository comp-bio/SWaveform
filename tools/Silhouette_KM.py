# -*- coding: utf-8 -*-
# Usage: python3 Silhouette_KM.py filename sample_size repeats
import sys, os, time
import random, json, warnings

warnings.filterwarnings("ignore")
seed = 2 * 1337
max_clusters = 6

from tslearn.clustering import TimeSeriesKMeans
from tslearn.clustering import silhouette_score
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


def func(clusters, dataset):
    m = TimeSeriesKMeans(n_clusters=clusters, n_init=1, metric="dtw", random_state=seed, n_jobs=32)
    m.fit_predict(dataset)
    return silhouette_score(dataset, m.labels_, metric="dtw", random_state=seed, n_jobs=32)


# ---------------------------------------------------------------------------- #
src, sample_size, repeats = (sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
dir, name = (os.path.dirname(os.path.realpath(src)), os.path.basename(src).replace("_filterd.bin", ""))

start_time = time.time()
results = []
for s_i in range(0, repeats):
    data = read_random(src, sample_size, seed + s_i)
    tsts = TimeSeriesScalerMeanVariance().fit_transform(data)
    results.append([func(num_cls, tsts) for num_cls in range(2, max_clusters)])

out = f"{dir}/silhouette_{name}.json"
with open(out, "w") as f:
    json.dump(results, f)

print(f"Size:     {sample_size}")
print(f"Repeats:  {repeats}")
print(f"Time:     %s min." % int((time.time() - start_time)/60))
print(f"Result:   {out}")
