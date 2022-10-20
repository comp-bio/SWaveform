# SWaveform

## Dependencies

All instruments are written using `python3`, you need to install the following dependencies before you start working

```bash
pip3 install flask gevent tslearn
pip3 install h5py tslearn matplotlib
pip3 install PyVCF3
```

We have collected a large collection of signals based on the HGDP open database (link), 
as well as a small demo collection of signals (link) based on 3 samples from GIAB (HG002, HG003, HG004). 
The following shows instructions on how to deploy a small version of the database and how to create it yourself from open sources

## How to deploy a local version of the database

Download compiled web-interface
```bash
wget https://swaveform.compbio.ru/supplement/swaveform-14-Oct-2022.zip
unzip swaveform-14-Oct-2022.zip
```

Download database and motifs
```bash
wget https://swaveform.compbio.ru/supplement/_GIAB_Ashkenazim.zip
unzip _GIAB_Ashkenazim.zip
```

Usage:
```bash
server.py \
  db:[DB path name] \
  port:[server port, default: 9915] \
  dev:[dev-mode (app.run), default: false (WSGIServer)] \
  sax:[SAX-transform width for plots, default: 64] \
  alphabet:[SAX-transform height for plots (alphabet size), default: 24]
```

Example:
```bash
python3 server.py db:_GIAB_Ashkenazim port:8888 dev:yes
# Open http://127.0.0.1:8888/
```

You can launch the web interface based on HGDP data (large) in the same way 
by substituting the required data source into the `db:` parameter


## Run a search for motifs on the signal database

We have two variants of the database built on the basis of GIAB. One, first `_GIAB_Ashkenazim`,
contains found motifs. The second, `_GIAB_Ashkenazim_nomodel`, contains only signals and does not contain motifs.
Using the second database, you can find motifs yourself using our instruments.

### 1. Download repository and database-without-motifs (_GIAB_Ashkenazim_nomodel.zip):

```bash
git clone git@github.com:latur/SWaveform.git && cd ./SWaveform
wget https://swaveform.compbio.ru/supplement/_GIAB_Ashkenazim_nomodel.zip
unzip _GIAB_Ashkenazim_nomodel.zip
```

Start collecting statistics and building distributions for the Description page:

```bash
./tools/overview.py db:./_GIAB_Ashkenazim
```

### 2. Search for motifs

The search for motifs goes in two stages:
1. Clustering and searching for motifs for each cluster using a random subsample of signals (bootstrap).
2. Combining the motifs found at the first stage

To speed up the search for a motifs, you can conduct it on different workstations and combine the results at the end.
Tool for clustering and searching for a motif in clusters: `./tools/Clusters_ADAKMS_bootstrap.py`

Usage:
```text
./tools/Clusters_ADAKMS_bootstrap.py \
  db:[DB path name] \
  name:[dataset name] \
  type:[SV type and side, ex: DEL_L] \
  sax:[SAX-transform width, default: 64] \
  alphabet:[SAX-transform height (alphabet size), default: 24] \
  window:[motif width, default: 32] \
  dataset:[signals count for each run, default: 400] \
  repeats:[repeats count for bootstrap, default: 20] \
  seed:[seed for K-means]
```

An example of searching for a motif for the Left deletion breakpoint (type:DEL_L):
```bash
./tools/Clusters_ADAKMS_bootstrap.py db:_GIAB_Ashkenazim_nomodel \
  repeats:10 dataset:800 type:DEL_L name:GIAB
# Time:   11 min. (663 sec.) 
# Memory: 178MB
# Result: _GIAB_Ashkenazim_nomodel/adakms/GIAB_DEL_L_s64-24_w32_d800_r10_s1337.json
```

Memory and speed calculations are measured for running in a single thread on a device with the following specifications:

```text
Architecture:        x86_64
CPU op-mode(s):      32-bit, 64-bit
CPU(s):              32
Thread(s) per core:  2
Core(s) per socket:  8
Model name:          Intel(R) Xeon(R) CPU E5-2640 v3 @ 2.60GHz
```

### 3. Merge

For each bootstrap run, we get 2 or 1 cluster, for each cluster there are up to 5 most significant motifs.
We combine these results into one most significant motif `./tools/Clusters_ADAKMS_align.py`:

Usage:
```bash
./tools/Clusters_ADAKMS_align.py \
  db:[DB path name] \
  prefix:[dataset name]
```

Example for DEL_L:
```bash
# Merge. After this step, the found motifs will be automatically shown in the interface
./tools/Clusters_ADAKMS_align.py db:_GIAB_Ashkenazim \
  prefix:GIAB_DEL_L
```

### Run web-interface

```bash
server.py db:_GIAB_Ashkenazim port:8888 dev:yes
# Open http://127.0.0.1:8888/
```

### Search for motifs of all types for the GIAB_Ashekenazi-database

```bash
tps='BND_L BND_R DEL_C DEL_L DEL_R DUP_C DUP_L DUP_R INS_C INV_C INV_L INV_R'
for tp in $(echo $tps); do
  ./tools/Clusters_ADAKMS_bootstrap.py db:_GIAB_Ashkenazim \
    repeats:20 dataset:800 type:$tp name:GIAB
  ./tools/Clusters_ADAKMS_align.py db:_GIAB_Ashkenazim \
    prefix:"GIAB_"$tp
done
```


## How to build your own database from sequencing data


### Prerequisites:

[Mosdepth](https://github.com/brentp/mosdepth) (in addition to the others)

Minimal hardware requirements  
- CPU 1-core
- RAM 2GB
- Free disk space: 600GB


To create a signal-database you will need:
0. Repository
1. .bam or .cram sample files
2. meta-file for matching directory names for each genome and sample names in VCF files
3. .vcf files with structural variants

### 0. Repository

```bash
git clone git@github.com:latur/SWaveform.git
cd ./SWaveform
```

### 1. Generate coverage files (.bcov) from sequencing data

Dataflow: (.bam|.cram) -> mosdepth -> (.per-base.bed.gz) -> bed2cov -> (.bcov)

Extracting depth-of-coverage (DOC) from .cram files is done using [mosdepth](https://github.com/brentp/mosdepth)  
Example for HGDP samples collection:

```bash
for crm in $(ls *.cram); do
  code=${crm/.cram/}
  ~/mosdepth -t 24 -f Homo_sapiens.GRCh38.dna.toplevel.fa "$code" "$crm"
done;
```

As a result, bed files of coverage values for each sample will be created in the `/projects/HGDP/cram/` directory.
These files need to be converted to .bcov format using a tool from our repository (`~/SWaveform/bed2cov/convert_Linux`).
Example:

```bash
cd /projects/HGDP/cram/
for crm in $(ls *.cram); do
  code=${crm/.cram/}
  mkdir -p $code && cd $code
  echo -e "\033[37m.bed -> .bcov $code [$(date)]\033[0m";
  gzip -cd ../"$code".per-base.bed.gz | ~/SWaveform/bed2cov/convert_Linux
  cd ../
done
```

### 2. Meta file

The meta file is a table, it indicates which sample in .VCF corresponds to which DOC-file (.bcov):
Columns: "sample_accession sample population sex meancov"  
`sample_accession` — sample name in vcf file  
`sample` is the name of the .bcov coverage data directory  
`population` `sex` `meancov` — fields for the database

### 3. Import VCF files and create database (tool `./tools/import_vcf.py`):

Usage:
```bash
./tools/import_vcf.py \
  db:[DB path name] \
  vcf:[vcf or vcf.gz file] \
  meta:[metadata file] \
  name:[dataset file] \
  center:[if SV size is less than specified, DO NOT keep `L` `R` ends but keep only `C` (32)] \
  all:[if SV size is less than specified, keep both BND: `L` R and `C` (256)] \
  offset:[BND offset in bases (integer, >16, default: 256)] \
  genome:[human genome version, default GRCh38]
```

Example:
```bash
for vcf in /projects/HGDP/SV/*.vcf; do
  ./tools/import_vcf.py db:_HGDP name:HGDP vcf:$vcf meta:/projects/HGDP/HGDP.metadata
done
```

After all VCF files have been imported, download the corresponding region coverage signals.
Tool: `./tools/import_coverage.py`

Usage:
```bash
./tools/import_coverage.py \
  db:[DB directory] \
  path:[coverage directory] \
  name:[dataset name]
```

Example:
```bash
./tools/import_coverage.py db:_HGDP name:HGDP path:/projects/HGDP/cram/
```


## Interface

To work on the interface, we used React. For development use hot-reload server:

```bash
yarn install #Once
yarn server
```

To build JS, use the command:

```bash
yarn build && yarn pub
```

The interface ready for publishing will be compiled into an archive like this: `swaveform-$(date +%d-%b-%Y).zip`
