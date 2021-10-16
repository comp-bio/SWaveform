# -*- coding: utf-8 -*-

import sys, os
from _functions import *
from vcf2score import Variants

# --------------------------------------------------------------------------- #
if len(sys.argv) != 3:
    echo('Usage:   python3 %s [vcf file] [offset]\n' % sys.argv[0])
    echo('Example: python3 %s ./test.vcf.gz 200\n\n' % sys.argv[0])
    sys.exit(1)

vcf_file, offset = sys.argv[1], int(sys.argv[2])

reader = Variants(vcf_file)
f = open("%s.bed" % vcf_file, 'w')
for chr, L, R, sv_type, rec in reader.info():
    if (not rec.FILTER) or len(rec.FILTER) == 0 or 'PASS' in rec.FILTER:
        f.write("%s\t%d\t%d\n" % (chr, L - offset, L + offset))
        if L != R:
            f.write("%s\t%d\t%d\n" % (chr, R - offset, R + offset))
f.close()
echo("Done. Result: %s.bed\n" % vcf_file)