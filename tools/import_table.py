# -*- coding: utf-8 -*-

import sys, os, re
import sqlite3
from _functions import *

# --------------------------------------------------------------------------- #
if len(sys.argv) < 3:
    echo('Usage:   python3 %s [DB sqlite file] [table]\n' % sys.argv[0])
    echo('Example: python3 %s ./signal.db GEL_Quality.info\n\n' % sys.argv[0])
    sys.exit(1)

# --------------------------------------------------------------------------- #
db_file, src_table = sys.argv[1:3]
offset = 256

# --------------------------------------------------------------------------- #
# Init DB
con = sqlite3.connect(db_file)
cur = con.cursor()
loc = os.path.dirname(os.path.realpath(__file__))
with open("%s/../data/schema.sql" % loc, 'r') as sql:
    for req in sql.read().replace('\n', '').split(';'):
        cur.execute(req)

# --------------------------------------------------------------------------- #
signals = []
targets = []
info = get_lines(src_table)
head = next(info)
for line in info:
    i = dict(zip(head, line))
    for k in ['population', 'region', 'sex', 'gt']:
        if k not in i: i[k] = ''
    obj = cur.execute(f"SELECT * FROM target WHERE name = '{i['name']}' and dataset = '{i['dataset']}'").fetchone()
    if obj:
        target_id = obj[0]
    if obj is None:
        cur.execute("INSERT INTO target VALUES (?,?,?,?,?,?,?,?)",
            (None, i['name'], i['sample'], i['dataset'], i['population'], i['region'], i['sex'], i['meancov'],))
        target_id = cur.lastrowid
        targets.append(i['name'])

    L, R = [int(i['start']), int(i['end'])]
    if R - L <= 32:
        C = round(R - L / 2)
        signals.append((None, target_id, i['chr'], C - offset, C + offset - 1, i['type'], 'C', i['gt'], ''))
    else:
        if L - offset > 0:
            signals.append((None, target_id, i['chr'], L - offset, L + offset - 1, i['type'], 'L', i['gt'], ''))
        signals.append((None, target_id, i['chr'], R - offset, R + offset - 1, i['type'], 'R', i['gt'], ''))

cur.executemany("INSERT INTO signal VALUES (?,?,?,?,?,?,?,?,?)", signals)
con.commit()

echo('Done%s\n' % (" " * 60))
echo('> Signals:    %d\n' % len(signals))
echo('> New targets: %d\n' % len(targets))
