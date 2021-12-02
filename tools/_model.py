# -*- coding: utf-8 -*-
from _functions import *

def models(cur, type, side, ds):
    matrix = [[0 for j in range(0, 32)] for i in range(0, 64)]
    hmm = [{} for i in range(0, 63)]

    cur.execute(f"SELECT signal.chr, signal.coverage FROM signal "
                f"LEFT JOIN target ON target.id = signal.target_id "
                f"WHERE signal.type = ? AND signal.side = ? AND target.dataset = ?", (type, side, ds, ))

    total = 0
    for chr, bin in cur.fetchall():
        if len(bin) == 0:
            continue

        sig = b2sig(bin)
        total += 1

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

    return (matrix, hmm, total, )
