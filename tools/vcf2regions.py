# -*- coding: utf-8 -*-

from _functions import *
from vcf2score import Variants

# --------------------------------------------------------------------------- #
if len(sys.argv) < 3:
    echo('Usage:   python3 %s [high conf] [vcf files list]\n' % sys.argv[0])
    echo('Example: python3 %s highconf.bed f1.vcf f2.vcf f3.vcf\n\n' % sys.argv[0])
    sys.exit(1)

highconf_file, vcf_files = sys.argv[1], sys.argv[2:]

high_data = bed_data(highconf_file)

for filename in vcf_files:
    reader = Variants(filename)
    for chr, L, R, sv_type, rec in reader.info():
        start, stop = L - 512, L + 512
        if chr not in high_data:
            continue
        hc = 1 - intersect(high_data[chr], start, stop)
        if hc > 0.1:
            continue
        print('\t'.join([chr, sv_type, str(start), str(stop), "{:.4f}".format(hc)]))

# python3 ../../Scripts/vcf2regions.py highconf.bed $(ls hg37/*.vcf) | grep '^21\t' > hg37sv21.tsv
