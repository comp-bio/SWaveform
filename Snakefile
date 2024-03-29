import glob, os

SAMPLES = [os.path.basename(f).split('.')[0] for f in glob.glob('snakedata/*.cram')]
CHROMOSOMES = ['chr' + str(i) for i in range(1, 23)] + ['chrX', 'chrY']

rule all:
  input:
    directory("_DB/models"),
    directory("_DB/adakms"),
    "_DB/overview.json",
    "_DB/storage.bcov",
    "_DB/index.db"

rule overview:
  input:
    "_DB/storage.bcov",
    "_DB/index.db"
  output:
    "_DB/overview.json"
  shell:
    "python3 ./tools/overview.py db:_DB"

rule find_motif:
  input:
    "_DB/storage.bcov",
    "_DB/index.db"
  output:
    directory("_DB/models"),
    directory("_DB/adakms")
  params:
    "DEL INS LOC"
  shell:
    "for t in {params}; do\n"
    "  for s in 'L' 'R' 'BP' 'spBP'; do\n"
    "    python3 ./tools/Clusters_ADAKMS_bootstrap.py db:_DB "
    "      name:CHM dataset:300 repeats:1 type:$t side:$s\n"
    "    python3 ./tools/Clusters_ADAKMS_align.py db:_DB "
    "      prefix:'CHM_'$t'_'$s\n"
    "  done\n"
    "done\n"

rule import_vcf:
  input:
    expand("doc/{sample}/{chr}.bcov", sample=SAMPLES, chr=CHROMOSOMES),
    "snakedata/metafile"
  output:
    "_DB/index.db"
  shell:
    "for vcf in $(ls snakedata/*.vcf); do\n"
    "  python ./tools/import_vcf.py db:_DB vcf:$vcf meta:snakedata/metafile name:'CHM'\n"
    "done\n"

rule import_bcov:
  input:
    expand("doc/{sample}/{chr}.bcov", sample=SAMPLES, chr=CHROMOSOMES),
    "snakedata/metafile",
    "_DB/index.db"
  output:
    "_DB/storage.bcov"
  shell:
    "python ./tools/import_coverage.py db:_DB path:./doc name:'CHM'\n"

rule doc2bcov:
  input:
    expand("doc/{sample}.per-base.bed.gz", sample=SAMPLES)
  output:
    expand("doc/{sample}/{chr}.bcov", sample=SAMPLES, chr=CHROMOSOMES)
  shell:
    "cd doc\n"
    "for name in $(ls *.bed.gz); do\n"
    "  code=$(basename $name | awk -F\".\" {{'print $1'}})\n"
    "  mkdir -p $code && cd $code\n"
    "  echo \"- $code.bed.gz -> $code/*.bcov\"\n"
    "  gzip -cd ../$code.per-base.bed.gz | ../../bed2cov/bed2cov\n"
    "  cd ../\n"
    "done\n"

rule doc:
  input:
    "mosdepth",
    "Homo_sapiens.GRCh38.dna.toplevel.fa"
  output:
    expand("doc/{sample}.per-base.bed.gz", sample=SAMPLES)
  shell:
    "mkdir -p doc\n"
    "for crm in $(ls snakedata/*.cram); do\n"
    "  code=$(basename $crm | awk -F\".\" {{'print $1'}})\n"
    "  if [ ! -f doc/$code.per-base.bed.gz ]; then\n"
    "    echo \"- $crm -> doc/$code\"\n"
    "    ./mosdepth -t 24 -f Homo_sapiens.GRCh38.dna.toplevel.fa doc/$code $crm\n"
    "  fi\n"
    "done;"

rule install_mosdepth:
  output:
    "mosdepth"
  shell:
    "if [ ! -f './mosdepth' ]; then "
    "  wget 'https://github.com/brentp/mosdepth/releases/download/v0.3.3/mosdepth'; "
    "  chmod +x './mosdepth';"
    "fi"

rule download_ref:
  output:
    "Homo_sapiens.GRCh38.dna.toplevel.fa"
  shell:
    "if [ ! -f 'Homo_sapiens.GRCh38.dna.toplevel.fa' ]; then "
    "  if [ ! -f 'Homo_sapiens.GRCh38.dna.toplevel.fa.gz' ]; then "
    "    wget 'http://ftp.ensembl.org/pub/current_fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.toplevel.fa.gz'; "
    "  fi; "
    "  gzip -d 'Homo_sapiens.GRCh38.dna.toplevel.fa.gz';"
    "fi"
