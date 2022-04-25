# -*- coding: utf-8 -*-
# Usage: python3 Group_motif.py motif.json run_name

import os, json, re, io, base64, warnings, time, sys
import numpy as np
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

from tslearn.piecewise import SymbolicAggregateApproximation

# ---------------------------------------------------------------------------- #
start_time = time.time()

src, code = sys.argv[1:3]

dir_ = os.path.dirname(os.path.realpath(src))
res = re.search("motif_([A-Za-z_]+)_s([0-9]+)-([0-9]+)_w([0-9]+)_d([0-9]+)_r([0-9]+).json", src)
name = res.groups()[0]
sax_w, sax_h, window, dataset, repeats = map(int, res.groups()[1:])

out = f"{dir_}/meta_{code}.{name}_s{sax_w}-{sax_h}_w{window}_d{dataset}_r{repeats}.json"
sax = SymbolicAggregateApproximation(n_segments=window, alphabet_size_avg=sax_h)
sax.fit_transform([[i] for i in range(0, window)])
bbox = dict(boxstyle="round", fc="white", alpha=0.7, ec="k", lw=1)

# ---------------------------------------------------------------------------- #

def motif_dist(M1, M2, limit=80):
    dists = []
    for o1, s1 in M1[0:limit]:
        for o2, s2 in M2[0:limit]:
            k1, k2 = (np.array(s1[o1:o1+window]).reshape(window, 1), np.array(s2[o2:o2+window]).reshape(window, 1))
            dists.append(sax.distance_sax(k1, k2))
    return np.mean(dists)


def get_groups(C):
    groups = C[0]['motif']
    for run in C[1:]:
        for M in run['motif']:
            dists = [motif_dist(G, M) for G in groups]
            k_min = np.argmin(dists)
            if dists[k_min] < 3:
                groups[k_min].extend(M)
            else:
                groups.append(M)

    groups.sort(key = len)
    groups.reverse()
    return groups


def as_base64(func):
    def tmp(*args, **kwargs):
        s = io.BytesIO()
        result = func(*args, **kwargs)
        plt.savefig(s, format='png', bbox_inches="tight")
        plt.close()
        return base64.b64encode(s.getvalue()).decode("utf-8").replace("\n", "")
    return tmp


@as_base64
def cluster_plot(C):
    fig, ax = plt.subplots(figsize=(6, 4))
    for t in C:
        x, s = (np.array(t['cls_mean']), np.array(t['cls_std']))
        opacity = 10/sum(s)/len(C)
        ax.fill_between([i for i in range(0,64)], x + s/2, x - s/2, alpha=opacity, linewidth=0, color='k')
        ax.plot(x, linewidth=1, alpha=2 * opacity, color='b')

    note = 'Size: ~{:.2f}%'.format(100 * np.mean([t['elements']/t['dataset'] for t in C]))
    ax.set(xlim=(0, 63), ylim=(-1.8, 1.8))
    ax.text(1.4, -1.68, note, ha="left", va="bottom", size=10, bbox=bbox)
    ax.set_title('Cluster')


@as_base64
def motif_plot(g, k, subs):
    opacity = min(1, max(5/len(g), 0.002))
    fig, ax = plt.subplots(figsize=(6, 4))
    
    for offset, sig in g:
        motif = sig[offset:offset + window]
        ax.plot(sig, color='k', alpha=opacity)
        ax.plot(np.arange(offset, offset + window), motif, lw=3, color='C1', alpha=opacity)

    note = '{:.2f}%'.format(100 * len(g)/subs)
    ax.text(2, 1.4, note, ha="left", va="bottom", size=10, bbox=bbox)
    ax.set(xlim=(0, 63), ylim=(0, 31))
    ax.set_title(f'{k+1} MS-motif')


def cluster2motif(C):
    subs = sum([t['subs'] for t in C])
    part = np.mean([t['elements']/t['dataset'] for t in C])
    if part < 1/3: return None

    # Cluster plot (1)
    meta = {'name': name, 'part':'{:.2f}%'.format(100 * part), 'cluster': cluster_plot(C), 'motif': []}

    # MS-Motifs plot (2-5)
    groups = get_groups(C)
    for k, g in enumerate(groups[1:5]):
        motif = np.array([sig[offset:offset + window] for offset, sig in g])
        offset = np.array([offset for offset, sig in g])

        mm = ','.join([str(int(v)) for v in motif.mean(axis=0)])
        ms = ','.join(["{:.2f}".format(v) for v in motif.std(axis=0)])

        filename = f'mt_{code}.{name}.{k+1}.motif'
        f = open(f'{dir_}/{filename}', 'w')
        f.write("\n".join([
            f'type: {name}',
            f'sax_segments: {sax_w}',
            f'sax_alphabet: {sax_h}',
            f'offset: {offset.mean()}',
            f'offset_std: {offset.std()}',
            f'dataset: {dataset}',
            f'repeats: {repeats}',
            f'motif: {mm}',
            f'motif_std: {ms}',
        ]))
        f.close()
        
        meta['motif'].append({'plot': motif_plot(g, k, subs), 'file': filename})
    return meta

# ---------------------------------------------------------------------------- #

with open(src, 'r') as f:
    A, B = json.load(f)

with open(out, "w") as f:
    json.dump([cluster2motif(A), cluster2motif(B)], f)
    
print(f"")
print(f"Result: {out}")
print(f"Time:   {int((time.time() - start_time)/60)} min.")
