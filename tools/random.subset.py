# -*- coding: utf-8 -*-
import os, sys
import sqlite3

src_file, dst_file = sys.argv[1:3]

# --------------------------------------------------------------------------- #
# Init DB
con = sqlite3.connect(dst_file)
cur = con.cursor()
loc = os.path.dirname(os.path.realpath(__file__))
with open("%s/../data/schema.sql" % loc, 'r') as sql:
    for req in sql.read().replace('\n', '').split(';'):
        cur.execute(req)

# --------------------------------------------------------------------------- #
# Load all target's
con_src = sqlite3.connect(src_file)
cur_src = con_src.cursor()

cur_src.execute(f"SELECT * FROM target")
for data in cur_src.fetchall():
    cur.execute("INSERT INTO target VALUES (?,?,?,?,?,?,?,?,?)", data)

# --------------------------------------------------------------------------- #
# Load 5% of signal's
cur_src.execute(f"SELECT COUNT(*) FROM signal")
cnt = cur_src.fetchone()[0]
size = int(int(cnt) * 0.05)

cur_src.execute(f"SELECT * FROM signal WHERE id IN (SELECT id FROM signal ORDER BY RANDOM() LIMIT {size})")
for data in cur_src.fetchall():
    cur.execute("INSERT INTO signal VALUES (?,?,?,?,?,?,?,?,?)", data)

con.commit()
print(f"Done, regions: {size}, filename: {dst_file}")
