import sys


def echo(text, color='37'):
    sys.stdout.write("\033[1;%sm%s\033[m" % (color, text))


def get_lines(path):
    with open(path) as f:
        content = f.readlines()
    for line in content:
        if line == "": continue
        yield line.replace('\n', '').replace(' ', '\t').split('\t')


def b2sig(bin):
    return [(bin[i] * 256 + bin[i + 1]) for i in range(0, len(bin), 2)]


def normal(sig, K=4, height=64, min_mean_coverage=25):
    short = [sum(sig[i:i+K])/K for i in range(0, len(sig), K)]
    top = max(2 * sum(short)/len(short), min_mean_coverage)
    return [min(height - 1, round(v * height / top)) for v in short]


def norm_matrix(matrix):
    n_matrix = []
    for col in matrix:
        s = sum(col)
        n_matrix.append([(0 if s == 0 else (i/s)) for i in col])
    return n_matrix


def write_matrix(matrix, to, sep="\t"):
    for col in matrix:
        to.write(sep.join([str(i) for i in col]) + "\n")
