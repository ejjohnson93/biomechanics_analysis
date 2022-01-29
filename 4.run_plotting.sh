#!/bin/bash

## Script to analyse the contents of each folder with 'plot_data.py'
# 'date_index.tsv' is a .tsv file with the names of the folders corresponding to the dates

for i in $(cut -f 1 date_index.tsv); do
   echo ${i}
   cd ${i}

   python /mnt/share/EMILYJ-CompMod/biomechanics_organised_python_analysis/plot_data.py

   cd ..

done
