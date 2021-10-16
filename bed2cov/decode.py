import sys


def bcov(file, start=0):
    with open(file, 'rb') as f:
        f.seek(start * 2)
        while True:
            value = f.read(2)
            if not value: break
            yield value[0] * 256 + value[1]


print([i for i in bcov(sys.argv[1], 1)])
