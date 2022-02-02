#!/bin/bash
### DRAFT ###

name=$1; src=$2
n=14

~/mosdepth -t 24 "$name" "$src"
mkdir -p "$name";
cd "$name" || exit;
gzip -cd "../""$name"".per-base.bed.gz" | ~/convert_Linux
rm -f "../""$name"".per-base"*

coverage=$(grep "total" "../""$name".mosdepth.summary.txt | awk {'print $4'})
for chr in $(ls *.bcov | grep -vP "chr[M|X|Y|Un*|EBV]" | grep -v "_random"); do
  ~/las_Linux "$chr" "$n" "$coverage" ${chr/\.bcov/} > "$chr"".14.las" &
done
wait

echo "#chr start end FFT_dF DWT_Energy_Entropy" > "../$name.$n.las"
cat *.las >> "../$name.$n.las"
rm -f *.las

cd ../

dst='./coverage'

execute() {
  for bam in $@; do ./mosdepth -t 32 $(basename "$bam") "$bam" &; done
  wait && echo "Done: $@"
}

mkdir -p "$dst" && cd "$dst"
echo $(ls ../bam/*.bam) | xargs -n 24 | while read data; do execute "$data"; done



    gzip -cd "$dst"/"$name"".per-base.bed.gz" | ./convert_Linux &
