# -*- coding: utf-8 -*-
# Usage:   python3 Clusters_ADAKMS_align.py dir code
# Example: python3 Clusters_ADAKMS_align.py bin0427 DEL_L

import glob, json, os, sys, warnings, random, math, time, re, io, base64
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

warnings.filterwarnings("ignore")

from tslearn.piecewise import SymbolicAggregateApproximation
from tslearn.metrics import dtw

# --------------------------------------------------------------------------- #

start_time = time.time()
dir_, code = sys.argv[1:3]

window = 32
sax_h = 32
sax_w = 64
quantile_use = [0.025, 0.050, 0.100]

bbox = dict(boxstyle="round", fc="white", alpha=0.7, ec="k", lw=1)
sax = SymbolicAggregateApproximation(n_segments=window, alphabet_size_avg=sax_h)
sax.fit_transform([[i] for i in range(0, window)])

names = glob.glob(f'{dir_}/CLS2_ADAKMS_*{code}*.json')
# --------------------------------------------------------------------------- #


def as_base64(func):
    def tmp(*args, **kwargs):
        s = io.BytesIO()
        result = func(*args, **kwargs)
        plt.savefig(s, format='png', bbox_inches="tight")
        plt.close()
        return base64.b64encode(s.getvalue()).decode("utf-8").replace("\n", "")
    return tmp


def motif_dist(M1, M2, limit=80):
    dists = []
    for o1, s1 in M1[0:limit]:
        for o2, s2 in M2[0:limit]:
            k1, k2 = (np.array(s1[o1:o1+window]).reshape(window, 1), np.array(s2[o2:o2+window]).reshape(window, 1))
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
    groups.sort(key = len)
    groups.reverse()
    return groups


def motif_on_signal(ax, g, note):
    opacity = min(1, max(5/len(g), 0.002))
    for offset, sig in g[0:8000]:
        motif = sig[offset:offset + window]
        ax.plot(sig, color='k', alpha=opacity)
        ax.plot(np.arange(offset, offset + window), motif, lw=3, color='C1', alpha=opacity)
    if note:
        ax.text(2, 1.4, note, ha="left", va="bottom", size=10, bbox=bbox)
    ax.set(xlim=(0, 63), ylim=(0, 23))


def motif_only(ax, g):
    opacity = min(1, max(5/len(g), 0.002))
    motif_items = []
    for offset, sig in g[0:4000]:
        motif = sig[offset:offset + window]
        ax.plot(motif, color='C1', alpha=opacity)
        motif_items.append(motif)
    ax.plot(np.array(motif_items).mean(axis=0), lw=3, color='r')
    ax.set(xlim=(0, 31), ylim=(0, 23))


@as_base64
def motif_on_signal_small(g):
    fig, ax = plt.subplots(figsize=(8, 5))
    plt.axis('off')
    motif_on_signal(ax, g, None)


@as_base64
def motif_only_small(g):
    fig, ax = plt.subplots(figsize=(5, 5))
    plt.axis('off')
    motif_only(ax, g)


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
def cluster_plot_detail(C, cls_name=None):
    fig, ax = plt.subplots(figsize=(8, 5))
    for t in C:
        x, s = (np.array(t['cls_mean']), np.array(t['cls_std']))
        opacity = 10/sum(s)/len(C)
        ax.fill_between([i for i in range(0,64)], x + s/2, x - s/2, alpha=opacity, linewidth=0, color='k')
        ax.plot(x, linewidth=1, alpha=2 * opacity, color='b')

    note = 'Size: ~{:.2f}%'.format(100 * np.mean([t['elements']/t['dataset'] for t in C]))
    ax.set(xlim=(0, 63), ylim=(-1.8, 1.8))
    ax.text(1.4, -1.68, note, ha="left", va="bottom", size=10, bbox=bbox)
    if cls_name == None: cls_name = ''
    ax.set_title(f'Cluster {cls_name}')


@as_base64
def cluster_plot_small(C):
    fig, ax = plt.subplots(figsize=(3, 2))
    plt.axis('off')
    for t in C:
        x, s = (np.array(t['cls_mean']), np.array(t['cls_std']))
        opacity = 10/sum(s)/len(C)
        ax.fill_between([i for i in range(0,64)], x + s/2, x - s/2, alpha=opacity, linewidth=0, color='k')
        ax.plot(x, linewidth=1, alpha=2 * opacity, color='b')
    ax.set(xlim=(0, 63), ylim=(-1.8, 1.8))


def cluster2motif(C, cls_name):
    part = np.mean([t['elements']/t['dataset'] for t in C])
    if part < 1/3: return None

    gpx = [get_groups(C, q) for q in range(3)]
    g = gpx[0][0]
    motif = np.array([sig[offset:offset + window] for offset, sig in g])
    offset = np.array([offset for offset, sig in g])

    mm = ','.join([str(int(v)) for v in motif.mean(axis=0)])
    ms = ','.join(["{:.2f}".format(v) for v in motif.std(axis=0)])

    filename = f'{dir_}/MT_{code}.{cls_name}.motif'
    f = open(filename, 'w')
    f.write("\n".join([
        f'type: {code}',
        f'sax_segments: {sax_w}',
        f'sax_alphabet: {sax_h}',
        f'offset: {offset.mean()}',
        f'offset_std: {offset.std()}',
        f'motif: {mm}',
        f'motif_std: {ms}',
    ]))
    f.close()
    print(f"Motif: {filename}")

    info = {
        'cluster': cls_name,
        'code': code,
        'part':'{:.2f}%'.format(100 * part),
        'cluster': cluster_plot_small(C),
        'motif_signal': motif_on_signal_small(g),
        'motif': motif_only_small(g)
    }

    out = f"{dir_}/ADAKMS_small_{code}.{cls_name}.json"
    with open(out, "w") as f:
        json.dump(info, f)
    print(f"Motif plot: {out}")

    info['cluster_detail'] = cluster_plot_detail(C, cls_name)
    info['motif_detail'] = motif_plot_detail(gpx)
    out = f"{dir_}/ADAKMS_detail_{code}.{cls_name}.json"
    with open(out, "w") as f:
        json.dump(info, f)
    print(f"Motif plot [full]: {out}")



# --------------------------------------------------------------------------- #
# Load all runs
data = []
for src in names:
    with open(src, 'r') as f:
        data.extend(json.load(f))

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

print(f"Time: {int((time.time() - start_time)/60)} min.\n")
