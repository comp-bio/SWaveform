# -*- coding: utf-8 -*-
# Usage: python3 server.py signal.db

import os, sys, re
import json
import glob
import sqlite3
from flask import jsonify, request, Flask, send_file, send_from_directory
from gevent.pywsgi import WSGIServer

app = Flask(__name__, static_url_path='', static_folder='build')


# --------------------------------------------------------------------------- #
@app.route('/api/model/<variant>-<ds>-<type>-<side>', methods=['GET', 'POST'])
def model(variant, ds, type, side):
    model = './build/models/%s.%s-%s-%s.json' % (variant, ds, type, side)
    if os.path.isfile(model):
        return send_file(model, as_attachment=True)
    return jsonify({})


@app.route('/api/overview', methods=['GET', 'POST'])
def overview():
    def fx(root):
        return [os.path.basename(src) for src in sorted(glob.glob(root))]
    return jsonify({
        'models': fx(f"./build/models/*.png"),
        'meta': fx(f"./build/downloads/meta*.json")
    })
    #res = re.search("meta_(.+)\.([A-Za-z_]+)_s([0-9]+)-([0-9]+)_w([0-9]+)_d([0-9]+)_r([0-9]+).json", src)
    #code, name = res.groups()[0:2]
    #sax_w, sax_h, window, dataset, repeats = map(int, res.groups()[2:])
    #print([code, name, sax_w, sax_h, window, dataset, repeats])


@app.route('/api/signal', methods=['GET', 'POST'])
def signal():
    e = request.get_json(force=True)
    con = sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True)
    cur = con.cursor()

    types = [t for t in e['types'] if e['types'][t]]
    sql_t = ','.join(['?'] * len(types))

    side = [t for t in e['side'] if e['side'][t]]
    sql_s = ','.join(['?'] * len(side))

    # datasets = [t for t in e['datasets'] if e['datasets'][t]]
    # sql_d = ','.join(['?'] * len(datasets))
    offset = int(e['page']) * 24
    values = [e['chr'], 'chr' + e['chr'], e['end'], e['start']] + types + side + [e['dataset']]

    filter_by_population = ""
    if e['population'] != "":
        filter_by_population = f"AND t.population = ? "
        values.append(e['population'])

    cur.execute("SELECT s.id, s.start, s.end, s.type, s.side, s.coverage, t.name, t.population, t.meancov  FROM signal as s "
            "LEFT JOIN target AS t ON t.id = s.target_id "
            f"WHERE (s.chr = ? OR s.chr = ?) AND s.start < ? AND s.end > ? AND s.type IN ({sql_t}) AND s.side IN ({sql_s}) AND t.dataset = ? "
            f"{filter_by_population}"
            f"ORDER BY s.start LIMIT 24 OFFSET {offset}", tuple(values))

    result = []
    header = [i[0] for i in cur.description]
    for row in cur.fetchall():
        item = dict(zip(header, row))
        bin = item['coverage']
        item['coverage'] = [(bin[i] * 256 + bin[i + 1]) for i in range(0, len(bin), 2)]
        result.append(item)

    return jsonify(result)


# --------------------------------------------------------------------------- #
# Application page
@app.route('/')
@app.route('/description')
@app.route('/models')
def root():
    return app.send_static_file('index.html')


@app.route('/models/<path>')
def models(path):
    return send_from_directory('./build/models/', path)


@app.route('/downloads/<path>')
def downloads(path):
    return send_from_directory('./build/downloads/', path)


@app.route('/<path>/<any>')
def all(path, any):
    return root()


if __name__ == "__main__":
    port = 9915
    if len(sys.argv) > 2 and sys.argv[2] == "DEV":
        app.run(debug=True, host='127.0.0.1', port=port)
    else:
        http_server = WSGIServer(('', port), app)
        http_server.serve_forever()
