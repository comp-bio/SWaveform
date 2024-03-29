# -*- coding: utf-8 -*-
# Usage:   python3 Clusters_ADAKMS_align.py dir code
# Example: python3 Clusters_ADAKMS_align.py bin0427 DEL_L

import glob, json, os, sys, warnings, random, math, time, re, io, base64
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

start_time = time.time()
options = {'db': '', 'prefix': '', 'sax': 64, 'alphabet': 24, 'window': 32}
for par in sys.argv[1:]:
    k, v = (par + ':').split(':')[0:2]
    if k in options:
        options[k] = v if k in ['db', 'prefix'] else int(v)

def echo(text, color='37'):
    sys.stdout.write("\033[1;%sm%s\033[m" % (color, text))
    sys.stdout.flush()

def usage():
    echo('Usage:\n')
    echo('  python3 %s \\\n' % sys.argv[0])
    echo('    db:[DB path name] \\\n')
    echo('    prefix:[dataset name]\n')
    exit(1)

if options['db'] == '':
    echo(f"Error:\n", 31)
    echo(f"  Database not found! (db:./path-to-db)\n\n", 31)
    usage()

if options['prefix'] == '':
    echo(f"Error:\n", 31)
    echo(f"  Prefix not found! (use prefix:NAME_TYPE_SIDE)\n\n", 31)
    usage()

names = glob.glob(f"{options['db']}/adakms/{options['prefix']}*.json")
if len(names) == 0:
    echo(f"Error:\n", 31)
    echo(f"  Bootstrap results not found! (use prefix:NAME_TYPE_SIDE)\n\n", 31)
    usage()

for name in names:
    m = re.match(r'.*_s(?P<sax>\d+)-(?P<alphabet>\d+)_w(?P<window>\d+)_.+', os.path.basename(name))
    params = m.groupdict()
    for k in params:
        options[k] = int(params[k])

warnings.filterwarnings("ignore")

from tslearn.piecewise import SymbolicAggregateApproximation
from tslearn.metrics import dtw

# --------------------------------------------------------------------------- #
dir_ = f"{options['db']}/models/"
if not os.path.exists(dir_): os.makedirs(dir_)
plt_ = f"{options['db']}/media/"
if not os.path.exists(plt_): os.makedirs(plt_)

quantile_use = [0.015, 0.020, 0.025]
quantile_use = [0.015]

bbox = dict(boxstyle="round", fc="white", alpha=0.7, ec="k", lw=1)
sax = SymbolicAggregateApproximation(n_segments=options['sax'], alphabet_size_avg=options['alphabet'])
sax.fit_transform([[i] for i in range(0, options['window'])])

# --------------------------------------------------------------------------- #
def as_base64(func):
    def tmp(*args, **kwargs):
        s = io.BytesIO()
        result = func(*args, **kwargs)
        plt.savefig(s, format='png', bbox_inches="tight")
        plt.close()
        return base64.b64encode(s.getvalue()).decode("utf-8").replace("\n", "")
    return tmp


def motif_dist(M1, M2, limit=16):
    dists = []
    for o1, s1 in M1[0:limit]:
        for o2, s2 in M2[0:limit]:
            k1, k2 = (np.array(s1[o1:o1+options['window']]).reshape(options['window'], 1), np.array(s2[o2:o2+options['window']]).reshape(options['window'], 1))
            dists.append(sax.distance_sax(k1, k2))
    return np.mean(dists)


def get_groups(C, q):
    groups = None
    for run in C:
        if len(run['motif'][q]['motif']) == 0: continue
        if groups == None:
            groups = run['motif'][q]['motif']
            continue
        for M in run['motif'][q]['motif']:
            dists = [motif_dist(G, M) for G in groups]
            k_min = np.argmin(dists)
            if dists[k_min] < run['motif'][q]['threshold']:
                groups[k_min].extend(M)
            else:
                groups.append(M)
    if groups != None:
        groups.sort(key = len)
        groups.reverse()
    return groups


def motif_on_signal(ax, g, note):
    opacity = min(1, max(5/len(g), 0.002))
    for offset, sig in g[0:5000]:
        motif = sig[offset:offset + options['window']]
        ax.plot(sig, color='k', alpha=opacity)
        ax.plot(np.arange(offset, offset + options['window']), motif, lw=3, color='C1', alpha=opacity)
    if note:
        ax.text(2, 1.4, note, ha="left", va="bottom", size=10, bbox=bbox)
    ax.set(xlim=(0, 63), ylim=(0, 23))


def motif_only(ax, g):
    opacity = min(1, max(5/len(g), 0.002))
    motif_items = []
    for offset, sig in g[0:3000]:
        motif = sig[offset:offset + options['window']]
        ax.plot(motif, color='C1', alpha=opacity)
        motif_items.append(motif)
    ax.plot(np.array(motif_items).mean(axis=0), lw=3, color='r')
    ax.set(xlim=(0, 31), ylim=(0, 23))


def motif_on_signal_small(g, name):
    fig, ax = plt.subplots(figsize=(10, 6))
    plt.axis('off')
    motif_on_signal(ax, g, None)
    plt.savefig(plt_ + name, format='png', bbox_inches="tight")
    plt.close()


def motif_only_small(g, name):
    fig, ax = plt.subplots(figsize=(10, 10))
    plt.axis('off')
    motif_only(ax, g)
    plt.savefig(plt_ + name, format='png', bbox_inches="tight")
    plt.close()


@as_base64
def motif_plot_detail(gpx):
    fig = plt.figure(figsize=(24, 11))
    gs = gridspec.GridSpec(1, 3, figure=fig)
    for q in range(3):
        cnt = [len(g) for g in gpx[q]]
        gss = gs[q].subgridspec(5, 3)
        for m in range(5):
            if m < len(gpx[q]):
                ax = fig.add_subplot(gss[m, 0:2])
                if m == 0:
                    ax.set_title(f'Q: {quantile_use[q]}')
                motif_on_signal(ax, gpx[q][m], '{:.2f}%'.format(100 * len(gpx[q][m])/sum(cnt)))
                # motif
                ax = fig.add_subplot(gss[m, 2])
                motif_only(ax, gpx[q][m])


@as_base64
def cluster_plot_small(C):
    fig, ax = plt.subplots(figsize=(6, 4))
    plt.axis('off')
    opacity = 0.5
    x = np.array([t['cls_mean'] for t in C]).mean(axis=0)
    s = np.array([t['cls_std'] for t in C]).mean(axis=0)

    ax.fill_between([i for i in range(0,64)], x + s/2, x - s/2, alpha=opacity, linewidth=0, color='k')
    ax.plot(x, linewidth=1, alpha=1, color='b')
    ax.set(xlim=(0, 63), ylim=(-1.8, 1.8))


    fig, ax = plt.subplots(figsize=(6, 4))
    plt.axis('off')
    for t in C:
        x, s = (np.array(t['cls_mean']), np.array(t['cls_std']))
        opacity = max(10/sum(s)/len(C[0:2000]), 0.01)
        ax.fill_between([i for i in range(0,64)], x + s/2, x - s/2, alpha=opacity, linewidth=0, color='k')
        ax.plot(x, linewidth=1, alpha=2 * opacity, color='b')
    ax.set(xlim=(0, 63), ylim=(-1.8, 1.8))


def cluster_plot_detail(C, cls_name=None, name=''):
    fig, ax = plt.subplots(figsize=(10, 6))
    for t in C[0:2000]:
        x, s = (np.array(t['cls_mean']), np.array(t['cls_std']))
        opacity = 0.01 # max(10/sum(s)/len(C[0:2000]), 0.01)
        ax.fill_between([i for i in range(0, 64)], x + s/2, x - s/2, alpha=opacity, linewidth=0, color='k')
        ax.plot(x, linewidth=1, alpha=0.15, color='b')

    note = 'Size: ~{:.2f}%'.format(100 * np.mean([t['elements']/t['dataset'] for t in C]))
    ax.set(xlim=(0, 63), ylim=(-1.8, 1.8))
    ax.text(1.4, -1.68, note, ha="left", va="bottom", size=10, bbox=bbox)
    if cls_name == None: cls_name = ''
    ax.set_title(f'Cluster {cls_name}')
    plt.savefig(plt_ + name, format='png', bbox_inches="tight")
    plt.close()


def cluster2motif(C, cls_name):
    part = np.mean([t['elements']/t['dataset'] for t in C])
    if part < 1/3: return None

    threshold = np.mean([run['motif'][0]['threshold'] for run in C])
    print(f"Threshold for cls {cls_name}: {threshold}")
    # gpx = [get_groups(C, q) for q in range(3)]
    # g = gpx[0][0]
    gp = get_groups(C, 0)
    if not gp:
        print(f"Motif not found for class: {cls_name}")
        return
    g = gp[0]

    motif = np.array([sig[offset:offset + options['window']] for offset, sig in g])
    offset = np.array([offset for offset, sig in g])

    mm = ','.join([str(int(v)) for v in motif.mean(axis=0)])
    ms = ','.join(["{:.2f}".format(v) for v in motif.std(axis=0)])

    filename = f"{dir_}mt_{options['prefix']}.{cls_name}.motif"
    f = open(filename, 'w')
    f.write("\n".join([
        f"type: {options['prefix']}",
        f"sax_segments: {options['sax']}",
        f"sax_alphabet: {options['alphabet']}",
        f'offset: {offset.mean()}',
        f'offset_std: {offset.std()}',
        f'motif: {mm}',
        f'motif_std: {ms}',
        f'threshold: {threshold}'
    ]))
    f.close()
    print(f"Motif: {filename}")

    cl_x = [float(i) for i in np.array([t['cls_mean'] for t in C]).mean(axis=0)]
    cl_s = [float(i) for i in np.array([t['cls_std'] for t in C]).mean(axis=0)]

    info = {
        'cluster_name': cls_name,
        'code': options['prefix'],
        'part': '{:.2f}%'.format(100 * part),
        'cluster_x': cl_x,
        'cluster_s': cl_s,
        'motif_signal': f"{options['prefix']}.{cls_name}.motif_signal.png",
        'motif': f"{options['prefix']}.{cls_name}.motif.png",
        'threshold': threshold
    }

    motif_on_signal_small(g, info['motif_signal'])
    motif_only_small(g, info['motif'])

    out = f"{dir_}{options['prefix']}.{cls_name}.small.json"
    with open(out, "w") as f:
        json.dump(info, f)
    print(f"Motif plot: {out}")

    info['cluster_detail'] = f"{options['prefix']}.{cls_name}.cluster_detail.png"
    cluster_plot_detail(C, cls_name, info['cluster_detail'])
    #info['motif_detail'] = motif_plot_detail(gpx)

    out = f"{dir_}{options['prefix']}.{cls_name}.detail.json"
    with open(out, "w") as f:
        json.dump(info, f)
    print(f"Motif plot [full]: {out}")



# --------------------------------------------------------------------------- #
# Load all runs
data = []
for src in names:
    with open(src, 'r') as f:
        data.extend(json.load(f))
print(f"Files: " + str(len(names)))
print(f"Runs:  " + str(len(data)))

if len(data) == 0:
    print(f"Skip")
    sys.exit(0)

# Align Clusters
A, B = ([data[0][0]], [data[0][1]])
k = 'cls_mean'
for a, b in data[1:]:
    fr = sum([dtw(t[k], a[k]) for t in A]) + sum([dtw(t[k], b[k]) for t in B])
    rr = sum([dtw(t[k], a[k]) for t in B]) + sum([dtw(t[k], b[k]) for t in A])
    run = [a, b] if fr < rr else [b, a]
    A.append(run[0])
    B.append(run[1])

cluster2motif(A, 'A')
cluster2motif(B, 'B')

sec_ = int(time.time() - start_time)
min_ = int(sec_/60)
print(f"Time:   {min_} min. ({sec_} sec.)\n")
