# -*- coding: utf-8 -*-
# Usage: python3 server.py signal.db

import os, sys, re, json, glob, sqlite3, warnings
from flask import jsonify, request, Flask, send_file, send_from_directory, redirect
from gevent.pywsgi import WSGIServer

# --------------------------------------------------------------------------- #
options = {'db': '', 'port': 9915, 'dev': False, 'sax': 64, 'alphabet': 24}
for par in sys.argv[1:]:
    k, v = (par + ':').split(':')[0:2]
    if k in options: options[k] = v

db = f"{options['db']}/index.db"
bc = f"{options['db']}/storage.bcov"

def echo(text, color='37'):
    sys.stdout.write("\033[1;%sm%s\033[m" % (color, text))
    sys.stdout.flush()

def usage():
    echo('Usage:\n')
    echo('  python3 %s \\\n' % sys.argv[0])
    echo('    db:[DB path name] \\\n')
    echo('    port:[server port, default: 9915] \\\n')
    echo('    dev:[dev-mode (app.run), default: false (WSGIServer)] \\\n')
    echo('    sax:[SAX-transform width for plots, default: 64] \\\n')
    echo('    alphabet:[SAX-transform height for plots (alphabet size), default: 24]\n')
    exit(1)

if options['db'] == '':
    usage()

if not os.path.isfile(db):
    echo(f"Error:\n", 31)
    echo(f"  Database not found! (db:./path-to-db)\n\n", 31)
    usage()

warnings.filterwarnings("ignore")

from tslearn.piecewise import SymbolicAggregateApproximation
from tslearn.preprocessing import TimeSeriesScalerMeanVariance

coverage = open(bc, 'rb')
app = Flask(__name__, static_url_path='', static_folder='build')
sax = SymbolicAggregateApproximation(
    n_segments=options['sax'],
    alphabet_size_avg=options['alphabet'])

# --------------------------------------------------------------------------- #
# Api
@app.route('/api/model/<fname>', methods=['GET', 'POST'])
def api_model(fname):
    model = f"{options['db']}/models/%s" % (fname)
    if os.path.isfile(model):
        return send_file(model, as_attachment=True)
    return jsonify({})

@app.route('/api/models', methods=['GET'])
def api_models():
    fx = lambda root: [os.path.basename(src) for src in sorted(glob.glob(root))]
    return jsonify({
        'models': fx(f"{options['db']}/media/*.png"),
        'meta': fx(f"{options['db']}/models/detail*.json")
    })

@app.route('/api/models/<path>', methods=['GET'])
def api_models_get(path):
    return send_from_directory(f"{options['db']}/models/", path)

@app.route('/api/media/<path>')
def api_media_get(path):
    return send_from_directory(f"{options['db']}/media/", path)

@app.route('/api/overview', methods=['GET'])
def api_overview():
    return send_file(f"{options['db']}/overview.json")

@app.route('/api/signal', methods=['GET', 'POST'])
def api_signal():
    e = request.get_json(force=True)
    con = sqlite3.connect('file:%s?mode=ro' % db, uri=True)
    cur = con.cursor()

    types = [t for t in e['types'] if e['types'][t]]
    sql_t = ','.join(['?'] * len(types))

    side = [t for t in e['side'] if e['side'][t]]
    sql_s = ','.join(['?'] * len(side))
    offset = int(e['page']) * 24
    values = [e['chr'], 'chr' + e['chr'], e['end'], e['start']] + types + side + [e['dataset']]

    filter_by_population = ""
    if e['population'] != "":
        filter_by_population = f"AND t.population = ? "
        values.append(e['population'])

    cur.execute("SELECT s.id, s.start, s.end, s.type, s.side, s.coverage_offset, t.name, t.population, t.meancov  FROM signal as s "
            "LEFT JOIN target AS t ON t.id = s.target_id "
            f"WHERE (s.chr = ? OR s.chr = ?) AND s.start < ? AND s.end > ? AND s.type IN ({sql_t}) AND s.side IN ({sql_s}) AND t.dataset = ? "
            f"{filter_by_population}"
            f"ORDER BY s.start LIMIT 24 OFFSET {offset}", tuple(values))

    result = []
    header = [i[0] for i in cur.description]
    for row in cur.fetchall():
        item = dict(zip(header, row))
        coverage.seek((item['coverage_offset']) * 2)
        bin = coverage.read((item['end'] - item['start'] + 1) * 2)
        item['coverage'] = [(bin[i] * 256 + bin[i + 1]) for i in range(0, len(bin), 2)]
        cls = TimeSeriesScalerMeanVariance().fit_transform([item['coverage']])
        item['sax'] = [int(v[0]) for v in sax.fit_transform(cls)[0]]
        result.append(item)

    return jsonify(result)


# --------------------------------------------------------------------------- #
# Application page
@app.route('/')
@app.route('/description')
@app.route('/models')
def root():
    return app.send_static_file('index.html')

@app.route('/supplement/<path>')
def supplement(path):
    return send_from_directory(f"./supplement/", path, as_attachment=True)

@app.route('/media/<path>')
def media_get(path):
    return send_from_directory(f"./build/media/", path)

@app.route('/<path>/<any>')
def get_all(path, any):
    return root()

if __name__ == "__main__":
    if options['dev']:
        app.run(debug=True, host='127.0.0.1', port=int(options['port']))
    else:
        http_server = WSGIServer(('', int(options['port'])), app)
        http_server.serve_forever()
