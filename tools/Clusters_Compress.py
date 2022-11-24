# -*- coding: utf-8 -*-
import sqlite3, sys

# --------------------------------------------------------------------------- #
options = {
    'db': '', 'dataset': '', 'type': '', 'side': '', 
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
    # echo('    gt:[genotype, 0/1 (1) or 1/1 (2), all by default] \\\n')
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
    #if options['gt'] == '1': WHERE = ' AND s.genotype = 1'
    #if options['gt'] == '2': WHERE = ' AND s.genotype = 2'
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

import os, time
import random, json, warnings

warnings.filterwarnings("ignore")
seed = 3 * 1337
K = 8

from tslearn.clustering import TimeSeriesKMeans
from tslearn.preprocessing import TimeSeriesScalerMeanVariance

def compress(sig, K=2):
    return [sum(sig[i:i+K])/K for i in range(0, len(sig), K)]


def fit(data, seed):
    model = TimeSeriesKMeans(n_clusters=2, n_init=1, metric="dtw", random_state=seed, n_jobs=32)
    return model.fit_predict(TimeSeriesScalerMeanVariance().fit_transform(data))

# ---------------------------------------------------------------------------- #
start_time = time.time()

S, C = ([],[],)
for r in range(int(options['repeats'])):
    echo(f"{r+1} ", 30)
    dt = read_random(cnt)
    C0 = fit(dt, seed + r)
    C1 = fit(dt, seed + r + 1)
    C2 = fit([compress(sig, K) for sig in dt], seed + r)
    S.append(max(sum(C0 == C1), sum(C0 != C1))/cnt)
    C.append(max(sum(C0 == C2), sum(C0 != C2))/cnt)

if not os.path.exists(f"{options['db']}/compress"): os.makedirs(f"{options['db']}/compress")
out = f"{options['db']}/compress/{options['dataset']}_{options['type']}_s{options['side']}_r{options['repeats']}.json"
with open(out, "w") as f:
    json.dump({'results': [S, C], 'options': options}, f)

sec_ = int(time.time() - start_time)
min_ = int(sec_/60)

echo(f"Params:   {opt}\n")
echo(f"Time:     {min_} min. ({sec_} sec.)\n")
echo(f"Result:   {out}\n")
