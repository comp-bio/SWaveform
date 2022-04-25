# -*- coding: utf-8 -*-
import sqlite3

con = sqlite3.connect('signal.db')
cur = con.cursor()

# 10 signals from the 1.3M-3M interval of the 1chr with reference to the sample
chr, start, end = ('chr1', 1300000, 3000000, )
cur.execute("SELECT s.id, s.start, s.end, s.type, s.side, s.coverage, t.name, t.population, t.meancov FROM signal as s "
            "LEFT JOIN target AS t ON t.id = s.target_id "
            "WHERE s.chr = ? AND s.start < ? AND s.end > ? LIMIT 10",
            (chr, end, start,))

names = list(map(lambda x: x[0], cur.description))
for row in cur.fetchall():
    obj = dict(zip(names, row))
    bin = obj['coverage']
    # Conversion of BLOB data to integer coverage values:
    obj['coverage'] = [(bin[i] * 256 + bin[i + 1]) for i in range(0, len(bin), 2)]
    print(obj)


cur.execute("SELECT count(*), start - end as t  from signal group by t")


