# -*- coding: utf-8 -*-
import sqlite3, sys

# --------------------------------------------------------------------------- #
options = {
    'db': '', 'dataset': '', 'type': '', 'side': '', 'gt': '', 
    'repeats': 10, 'sample': 100
}
for par in sys.argv[1:]:
    k, v = (par + ':').split(':')[0:2]
    if k in options:
        options[k] = v

db = f"{options['db']}/index.db"
bc = f"{options['db']}/storage.bcov"

# --------------------------------------------------------------------------- #
def echo(text, color='37'):
    sys.stdout.write("\033[1;%sm%s\033[m" % (color, text))
    sys.stdout.flush()

def usage():
    echo('Usage:\n')
    echo('  python3 %s \\\n' % sys.argv[0])
    echo('    db:[DB path name] \\\n')
    echo('    dataset:[dataset name] \\\n')
    echo('    type:[SV type. ex: DEL] \\\n')
    echo('    side:[SV side. L, R or BP] \\\n')
    echo('    gt:[genotype, 0/1 (1) or 1/1 (2), all by default] \\\n')
    echo('    repeats:[integer, number of repeats, default: 10] \\\n')
    echo('    sample:[integer, count of random signals, default: 100]\n')
    exit(1)

for k in options:
    if options[k] == '':
        echo(f"Error:\n", 31)
        echo(f"  Parametr `{k}` not found!\n\n", 31)
        usage()

# --------------------------------------------------------------------------- #
con = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
cur = con.cursor()
coverage = open(bc, 'rb')


def read_random(count=100):
    WHERE = ''
    if options['gt'] == '1': WHERE = ' AND s.genotype = 1'
    if options['gt'] == '2': WHERE = ' AND s.genotype = 2'
    cur.execute("SELECT s.coverage_offset, s.start, s.end FROM `signal` as s "
        "LEFT JOIN `target` as t ON s.target_id = t.id "
        f"WHERE t.dataset = '{options['dataset']}' and s.type = '{options['type']}' and s.side = '{options['side']}' AND s.coverage_offset != '' "
        f"{WHERE} "
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

cnt = int(options['sample'])
opt = " ".join([f"{k}:{options[k]}" for k in options])
if len(read_random(cnt)) != cnt:
    echo(f"Sgnals not found: {opt}\n", 31)
    sys.exit(0)
    
# --------------------------------------------------------------------------- #

import os, time, random, json, warnings, sqlite3

warnings.filterwarnings("ignore")
seed = 2 * 1337
max_clusters = 6

from tslearn.clustering import TimeSeriesKMeans
from tslearn.clustering import silhouette_score
from tslearn.preprocessing import TimeSeriesScalerMeanVariance

def compress(sig, K=2):
    return [sum(sig[i:i+K])/K for i in range(0, len(sig), K)]

def func(clusters, dataset):
    m = TimeSeriesKMeans(n_clusters=clusters, n_init=1, metric="dtw", random_state=seed, n_jobs=32)
    m.fit_predict(dataset)
    return silhouette_score(dataset, m.labels_, metric="dtw", random_state=seed, n_jobs=32)

# ---------------------------------------------------------------------------- #
start_time = time.time()
results = []
for s_i in range(0, int(options['repeats'])):
    echo(f"{s_i+1} ", 30)
    dt = read_random(cnt)
    data = [compress(sig, 8) for sig in dt]
    tsts = TimeSeriesScalerMeanVariance().fit_transform(data)
    results.append([func(num_cls, tsts) for num_cls in range(2, max_clusters)])
echo(f"\n")

if not os.path.exists(f"{options['db']}/silhouette"): os.makedirs(f"{options['db']}/silhouette")
out = f"{options['db']}/silhouette/{options['dataset']}_{options['type']}_s{options['side']}_gt{options['gt']}_r{options['repeats']}.json"
with open(out, "w") as f:
    json.dump({'results': results, 'options': options}, f)

sec_ = int(time.time() - start_time)
min_ = int(sec_/60)

echo(f"Params:   {opt}\n")
echo(f"Time:     {min_} min. ({sec_} sec.)\n")
echo(f"Result:   {out}\n")
