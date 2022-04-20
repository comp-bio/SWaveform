# -*- coding: utf-8 -*-
import os, json
import matplotlib.pyplot as plt
import numpy as np
import warnings

warnings.filterwarnings("ignore")

from tslearn.piecewise import SymbolicAggregateApproximation


def mat2sig(mat, sax):
    return sax.fit_transform([[sum([k * v for k, v in enumerate(col)]) for col in mat]])[0]


def group_motif(L, x=32, y=32):
    sax = SymbolicAggregateApproximation(
        n_segments=x,
        alphabet_size_avg=y)
    group = [[[m, L[0]['subs']]] for m in L[0]['motif']]
    while len(group) < 5:
        group.append([[{'m': np.zeros((x, y)), 'items': 0}, 1]])
    for t in L[1:]:
        available = [True for i in range(len(group))]
        for cand in t['motif']:
            refs = []
            mt = mat2sig(cand['m'], sax)
            for k, av in enumerate(available):
                if not av: continue
                refs.append([sax.distance_sax(mat2sig(group[k][0][0]['m'], sax), mt), k])
            if len(refs) > 0:
                refs = np.array(refs)
                add_to = int(refs[np.argsort(refs[:,0])][0][1])
                group[add_to].append([cand, t['subs']])
                available[add_to] = False
    return group


def join(L):
    J = np.array(L[0][0]['m'])
    for t in L[1:]:
        J += np.array(t[0]['m'])
    s = '~{:.2f}%'.format(np.mean([100 * t[0]['items']/t[1] for t in L]))
    return (J/len(L), s)


def plot_motif(js, suffix = '', x=32, y=32):
    with open(js, 'r') as f:
        A, B = json.load(f)
        name = os.path.basename(js).replace('motif_HGDP_', '').replace(suffix, '')
        fig, axs = plt.subplots(2, 5, figsize=(5*3, 2*3))
        for col, group, cls in zip(axs, [group_motif(A, x, y), group_motif(B, x, y)], ['A', 'B']):
            for ax, g in zip(col, group):
                mat, note = join(g)
                ax.matshow(np.transpose(mat), origin='lower')
                ax.set_title(f'{name} [{cls}] • {note}')
        fig.tight_layout()
        fig.show()
        plt.show()
        return True
