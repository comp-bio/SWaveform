import sys, re
import json
import vcf
from _functions import echo

def simplify(regions):
    inf = float('inf')
    A, B = (-inf, -inf)
    for a, b in sorted(regions):
        if a > B + 1:
            if A > -inf and B > -inf:
                yield [A, B]
            A, B = (a, b)
            continue
        if b > B:
            B = b
    if A > -inf and B > -inf:
        yield [A, B]

class Variants:
    def __init__(self, filename):
        self.reader = vcf.Reader(filename=filename)

    def get(self):
        while True:
            try:
                read = next(self.reader, None)
                if read is None:
                    break
                yield read
            except:
                pass

    def info(self):
        for record in self.get():
            chr, start, stop, sv_type, rec = (record.CHROM, record.POS, record.POS, 'UND', record)

            if 'SVTYPE' in record.INFO:
                sv_type = record.INFO['SVTYPE']

            if 'SVLEN' in record.INFO:
                if isinstance(record.INFO['SVLEN'], list):
                    stop = start + record.INFO['SVLEN'][0]
                else:
                    stop = start + record.INFO['SVLEN']

            if sv_type == 'UND' and len(record.ALT) == 1:
                o = re.match(r'([A-Z]+)\:(.+)', record.ALT[0].type)
                if o: sv_type = o.group(1)
                o = re.match(r'([A-Z]+)?\:?SVSIZE=([0-9]+)\:?(.+)', record.ALT[0].type)
                if o and 'SVLEN' not in record.INFO:
                    stop = start + int(o.group(2))

            if sv_type == 'UND' and record.ID:
                o = re.match(r'([A-z]+)\_([^_]+)_([0-9]+)_([0-9]+)', record.ID)
                if o:
                    sv_type = o.group(1)
                    stop = int(o.group(4))

            L, R = (min(start, stop), max(start, stop))
            yield [chr, L, R, sv_type, rec]

class FxScore:
    def __init__(self, vcf_items=[]):
        self.offset = 300
        self.costs = {'DUP': 0.5, 'INV': 0.65, 'DEL': 0.85, 'UND': 0.75}
        self.costs = {'DUP': 0.0, 'INV': 0.00, 'DEL': 0.00, 'UND': 0.00}
        self.W = {}
        for file in vcf_items:
            self.append(file)

    def append(self, filename):
        echo("VCF file:       %s\n" % filename, '33')
        reader = Variants(filename)

        for chr, L, R, sv_type, rec in reader.info():
            if chr not in self.W:
                self.W[chr] = {1: []}
                for cost_sv_type in self.costs:
                    self.W[chr][self.costs[cost_sv_type]] = []

            # Left BND:
            self.W[chr][1].append([L - self.offset, L + self.offset])

            # Right BND:
            self.W[chr][1].append([R - self.offset, R + self.offset])

            # Middle part:
            if sv_type in self.costs:
                if R - L > 2 * self.offset:
                    self.W[chr][self.costs[sv_type]].append([L + self.offset, R - self.offset])

        for chr in self.W:
            cost = sorted([c for c in self.W[chr]])
            for cl in cost:
                self.W[chr][cl] = [R for R in simplify(self.W[chr][cl])]

    def save(self, filename):
        echo("Saved as:       %s\n" % filename, '33')
        with open(filename, "w") as h:
            json.dump(self.W, h)

class Fx:
    def __init__(self, data_file):
        with open(data_file, 'r') as h:
            self.W = json.loads(h.read())
        self.begins = {chr: 0 for chr in self.W}

    def value(self, chr, a, b):
        selected = []
        points = [a, b]
        for c in self.W[chr]:
            for A, B in self.W[chr][c][self.begins[chr]:]:
                if B < a:
                    self.begins[chr] += 1
                    continue
                if A > b:
                    break
                selected.append([A, B, c])
                points.extend([p for p in [A, A - 1, B, B + 1] if a <= p <= b])

        func = []
        for point in sorted(points):
            value = 0
            for a_, b_, c_ in selected:
                c_ = float(c_)
                if a_ <= point <= b_ and c_ > value:
                    value = c_
            func.append([value, point])

        total = 0.0
        for i, fx in enumerate(func[1:]):
            v_, p_ = func[i]
            total += (fx[1] - p_) * fx[0]

        return total / (b - a)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        echo('Usage:    python3 %s [result.json] [vcf files list]\n' % sys.argv[0])
        echo('Example:  python3 %s ../Data/HG002/hg37.score.json $(ls ../Data/HG002/hg37/*.vcf)\n\n' % sys.argv[0])
        sys.exit(1)

    score = FxScore(sys.argv[2:])
    score.save(sys.argv[1])
