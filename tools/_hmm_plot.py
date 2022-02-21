# import json
# with open('./data/models/hmm.DEL-L.json', 'r') as h:
#    hmm = json.loads(h.read())
# with open('./data/models/matrix.DEL-R.json', 'r') as h:
#    matrix = json.loads(h.read())

def hmm_plot(hmm, matrix, fname):
    rect = 14
    svg = open(fname, 'w')
    svg.write('<svg width="%d" height="%d" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg">' % (64 * rect, 32 * rect, 64 * rect, 32 * rect))
    svg.write('<rect x="0" y="0" width="%d" height="%d" fill="#FFF" />' % (64 * rect, 32 * rect, ))

    # Density map
    for x, col in enumerate(matrix):
        t = sum(col)
        if t == 0:
            pass
        for y, value in enumerate(col):
            y = 31 - int(y)
            color = 'rgba(102, 139, 233, %f)' % (7 * float(value)/t)
            svg.write('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" />' % (x * rect, y * rect, rect, rect, color))

    # Probability
    for x, matrix in enumerate(hmm):
        for y, src in enumerate(matrix):
            t = sum(src)
            if t == 0: continue
            for y2, dst in enumerate(src):
                val = float(dst)/t
                x1, x2 = [int(x) * rect + rect/2, (int(x) + 1) * rect + rect/2]
                y1, y2 = [(31-int(y)) * rect + rect/2, (31-int(y2)) * rect + rect/2]
                color = 'rgba(%d, 0, %d, %f)' % (180 if y1 < y2 else 0, 180 if y1 > y2 else 0, val, )
                svg.write('<line x1="%d" x2="%d" y1="%d" y2="%d" stroke="%s" stroke-width="0.7" />' % (x1, x2, y1, y2, color))

    svg.write('</svg>')
    svg.close()
