#!/bin/bash

DATABASE=$1
DATASET=5000
REPEATS=42

python3 ./overview.py $DATABASE F

echo "-- KMS bootstrap --"
for src in ../build/models/*.bin; do
  python3 ./Clusters_KMS_bootstrap.py src:$src dataset:$DATASET repeats:$REPEATS &
done
wait

echo "-- Group motif --"
for src in ../build/models/motif*.json; do
 python3 ./Group_motif.py $src R5K &
done
wait

if [ -d "assets" ]; then
  echo "-- Release --"
  yarn build
  NAME="sw-$(date +%d-%b-%Y)-iface.zip" && zip -r $NAME ./build server.py $DATABASE
fi

echo "Done: $NAME"
echo ""
