#!/bin/bash
# Usage: ./init.sh [cram-and-vcf-files-root]

SDIR=$1

function log {
  echo -e "\033[0;33m$1\033[0m"
}

log "Start: [$(date)]"


# --------------------------------------------------------------------------- #
# 1. Download the repository with tools for creating a database

if [ -d "SWaveform" ]; then
  log "Repository update"
  cd "SWaveform"
  git pull
  cd ../
else
  log "Downloading the repository"
  git clone 'https://github.com/latur/SWaveform.git'
fi

# --------------------------------------------------------------------------- #
# 2. Download reference genome

REF='http://ftp.ensembl.org/pub/current_fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.toplevel.fa.gz'
REFx=$(basename ${REF/.gz/})
if [ ! -f $REFx ]; then
  if [ ! -f $REFx".gz" ]; then
    log "File not found. Downloading: [$REFx]"
    wget "$REF"
  fi
  gzip -d $REFx".gz"
fi

# --------------------------------------------------------------------------- #
# 3. Download `mosdepth`
MOS='https://github.com/brentp/mosdepth/releases/download/v0.3.3/mosdepth'
if [ ! -f './mosdepth' ]; then
  log "File not found. Downloading: [./mosdepth]"
  wget "$MOS"
  chmod +x './mosdepth'
fi

# --------------------------------------------------------------------------- #
# 4. Extract depth-of-coverage from .cram files

log "Extracting depth-of-coverage"
mkdir -p './DOC'
for crm in $(ls $SDIR/*.cram); do
  code=$(basename $crm | awk -F"." {'print $1'})
  log "- ${crm} -> ./DOC/${code}"
  ./mosdepth -t 24 -f "$REFx" "./DOC/${code}" "$crm"
done;

# --------------------------------------------------------------------------- #
# 5. Converting depth-of-coverage (.bed.gz) to .bcov

log "Converting .bed.gz -> .bcov"
cd "./DOC"
for crm in $(ls $SDIR/*.cram); do
  code=$(basename $crm | awk -F"." {'print $1'})
  mkdir -p "${code}" && cd "${code}"
  log "- ${code}.bed.gz -> ./DOC/${code}/*.bcov"
  gzip -cd ../"$code".per-base.bed.gz | ../../SWaveform/bed2cov/bed2cov
  cd ../
done;
cd ../

# --------------------------------------------------------------------------- #
# 6. The .meta file

echo "sample_accession sample population sex meancov" > CHM.meta
for d in HG00514 HG00733 NA19240; do
  mcv=$(cat ./DOC/${d}.mosdepth.summary.txt | grep "total" | awk {'print $4'})
  echo "${d} ${d} Default U ${mcv}" >> CHM.meta
done

# --------------------------------------------------------------------------- #
# 7. Import VCF files and create database

log "Virtual env [swf]"
if [ ! -d './swf' ]; then
  virtualenv -p python swf
fi
source swf/bin/activate
pip install PyVCF3

log "Importing vcf files"
for vcf in $(ls $SDIR/*.vcf); do
  python ./SWaveform/tools/import_vcf.py db:_CHM vcf:$vcf meta:CHM.meta name:"CHM"
done

# --------------------------------------------------------------------------- #
# 8. Import DOC

log "Importing depth-of-coverage"
python ./SWaveform/tools/import_coverage.py db:_CHM path:./DOC/ name:"CHM"

pip install tslearn matplotlib h5py
python ./SWaveform/tools/overview.py db:_CHM


# --------------------------------------------------------------------------- #
log "Done: [$(date)]"
