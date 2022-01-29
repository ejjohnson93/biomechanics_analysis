#!/bin/bash

## Script to analyse the contents of each folder with batch_biomechanics_csv.py
# 'date_index.tsv' is a .tsv file with the names of the folders corresponding to the dates

for i in $(cut -f 1 date_index.tsv); do
   echo ${i}
   cd ${i}

   cp /mnt/share/EMILYJ-CompMod/biomechanics_organised_python_analysis/tendon_data_formatted.csv ./
   python /mnt/share/EMILYJ-CompMod/biomechanics_organised_python_analysis/batch_biomechanics_csv.py

   cd ..

done
