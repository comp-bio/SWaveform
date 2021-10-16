# -*- coding: utf-8 -*-
from _functions import *

def models(cur, type, side):
    full = [{} for i in range(0, 512)]
    matrix = [[0 for j in range(0, 32)] for i in range(0, 64)]
    hmm = [{} for i in range(0, 63)]

    cur.execute(f"SELECT chr, coverage FROM signal WHERE type = ? AND side = ?", (type, side,))
    for chr, bin in cur.fetchall():
        if len(bin) == 0:
            continue

        # Original
        sig = b2sig(bin)
        for i,v in enumerate(sig):
            if v not in full[i]: full[i][v] = 0
            full[i][v] += 1

        # Normalized
        n64 = normal(sig, 8, 32)
        for i,v in enumerate(n64):
            matrix[i][v] += 1

        # Markov model
        # n64 = normal(sig, 8, 32)
        for i in range(0, len(n64)-1):
            a, b = (n64[i], n64[i+1])
            if a not in hmm[i]: hmm[i][a] = {}
            if b not in hmm[i][a]: hmm[i][a][b] = 0
            hmm[i][a][b] += 1

    return (full, matrix, hmm, )
