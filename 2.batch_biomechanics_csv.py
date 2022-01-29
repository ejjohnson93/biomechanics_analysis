#!/usr/bin/env python

### Script to analyse biomechanics data - 07/09/2021 
# Python version 3.6 
# Run in the directory the data is in
# Will take all files ending in Data.xlsx as input in target directory 
# Required packages: os, pandas, numpy, terminaltables, sys, re, xlrd
# Most installations of Anaconda will include pandas and numpy 
# Terminal tables from: https://anaconda.org/conda-forge/terminaltables
# Contact Emily Johnson at ejohn16@liv.ac.uk or em.j.johnson.93@gmail.com if you're having trouble with the script 

## Load packages

import pandas as pd
import numpy as np
import os
import sys 
import re
import xlrd
import matplotlib.pyplot as plt
from terminaltables import AsciiTable

# If any packages aren't installed use package manager (preferably anaconda) to install, e.g.
# conda install -c conda-forge terminaltables

## Create empty dataframe for to output results for all samples analysed and empty array for files that couldn't be analysed
# Results dataframe
all_sample_summary = pd.DataFrame(columns=
    ['File name', 'Date', 'Sample ID', 'Replicate number', 'Sex', 'Age', 'Genotype', 
    'Sample length', 'Minimum force', 'Maximum force', 'Maximum force cycle 1', 'Maximum force cycle 5', 'Stress-relaxation', 'Rate of change of stress',
    'Hysteresis sum value', 'Hysteresis %', 'Smoothed hysteresis sum value', 'Smoothed hysteresis %', 
    'Average diameter', 'Circumference', 'Circumference, true', 'Max modulus', 'Stress at max modulus', 'Strain at max modulus', 'Failure stress (MPa)',
    'Failure strain (%)', 'Failure force (N)', 'Failure extension (mm)', 'Failure time (s)'])

# Error log array
# This will contain the names of the files that couldn't be matched to the metadata file 
error_log = []
# This will contain the names of files that threw up other errors during the processing 
error_log_2 = []

## Read in data

# Get current working directory 
dir = os.getcwd()
files = os.listdir(dir)

# Check sample metadata file exists, the script can't be ran without this
print("Checking to see if formatted sample meta-data file 'tendon_data_formatted.csv' is present in analysis directory...")

if os.path.isfile("tendon_data_formatted.csv"):
    print("Sample meta-data file found! Proceeding with analysis...")
    metadata = pd.read_csv("./tendon_data_formatted.csv", header=0)
    metadata = metadata.applymap(str)

else:
    sys.exit("Meta-data not found! Please make sure 'tendon_data_formatted.csv' is present in the same directory as the data. Terminating analysis...")

##### READ IN FILES AND CREATE DATAFRAMES #####
# Script takes in all files in the variable 'files' and interates through them
# It includes a conditional statement to make sure the file ends in 'Data.xlsx', so only the relevant files are analysed
for file in files:
        if file.endswith('Data.csv'):
            print("Carrying out analysis for dataset {}...".format(file))

            file = str(file)
            df = pd.read_csv("{}".format(file), header=0)

            ## Create seperate dataframes for each of the analyses
            # These are the equivalent of the different sheets in excel 

            precon_df = df[df['SetName'].str.contains('5x pre-conditioning')]
            stressrelax_df = df[df['SetName'].str.contains('Stress-relax')]
            failure_df = df[df['SetName'].str.contains('Failure')]

            ##### EXTRACT META-DATA #####

            name = os.path.splitext(file)[0]
            excel_annotation = re.split('(\d+)', name)
            sampleID = excel_annotation[2][-1]
            dateID = excel_annotation[1]
            replicateID = excel_annotation[3]
            sample_metadata = metadata.loc[(metadata.Date_ID == dateID) & (metadata.Sample_ID == sampleID) & (metadata.Replicate == replicateID)]

            ##### META-DATA QC #####

            # If the metadata was located in the previous step the analysis will be carried out ('sample_metadata' populated)
            # If not then the analysis will be skipped and the file name will be written to an error file ('sample_metadata' empty)

            if not sample_metadata.empty:
                try:
                    print('Found metadata matching sample file name! Continuing analysis...\n')
                    
                    ##### PRE-CONDITIONING #####

                    ## Pre-conditioning analysis - normalise/correct data

                    # Minimum force
                    minf = precon_df['Force_N'].min()

                    # Sample length
                    sample_length = precon_df.iloc[0,3]

                    # Load correction
                    precon_df['Load_correction'] = precon_df['Force_N'] - minf 
                    # Alternative: 
                    #precon_df['Load_correction'] = precon_df.iloc[:, 5] - minf

                    # Displacement correction 
                    precon_df['Displacement_correction'] = precon_df['Displacement_mm'] - minf 
                    # Alternative: 
                    #precon_df['Displacement_correction'] = precon_df.iloc[:, 4] - minf

                    # Area under curve
                    for j in range(0,precon_df.shape[0]-1):
                        precon_df.loc[precon_df.index[j],'Area_under_curve'] = (0.1*(precon_df.iloc[j+1,6] + precon_df.iloc[j,6])*(precon_df.iloc[j+1,7] - precon_df.iloc[j,7]))

                    # Load correction smooth 
                    precon_df['Load_correction_smoothed'] = precon_df['Load_correction'].rolling(window=5).mean()

                    # Area under curve smooth
                    for j in range(0,precon_df.shape[0]-1):
                        precon_df.loc[precon_df.index[j],'Area_under_curve_smooth'] = (0.1*(precon_df.iloc[j+1,9] + precon_df.iloc[j,9])*(precon_df.iloc[j+1,7] - precon_df.iloc[j,7]))

                    ## Pre-conditioning analysis - stress relaxation

                    # Max force
                    maxforce = precon_df['Force_N'].max()

                    # Max force cycle 1 and cycle 5 
                    maxforce_c1 = precon_df.loc[precon_df.Cycle.str.contains('1'), 'Force_N'].max()
                    maxforce_c5 = precon_df.loc[precon_df.Cycle.str.contains('5'), 'Force_N'].max()

                    # Stress-relaxation 
                    stress_relaxation = (((maxforce_c1-maxforce_c5)/maxforce_c1)*100)

                    ## Pre-conditioning analysis  - hysteresis 

                    # Hysteresis
                    # Sum of beginning of cycle 1 to last positive value in cycle 1
                    hysteresis_positive = precon_df.loc[(precon_df.Cycle.str.contains('1')) & (precon_df['Area_under_curve'] > 0), 'Area_under_curve'].sum()
                    # Sum of first negative value in cycle 5 to last negative value in cycle 5
                    hysteresis_negative = precon_df.loc[(precon_df.Cycle.str.contains('5')) & (precon_df['Area_under_curve'] < 0), 'Area_under_curve'].sum()
                    # Add the two together to calculate sum value
                    hysteresis_sum = hysteresis_positive + hysteresis_negative
                    # Then calculate percentage
                    percentage = (hysteresis_sum/hysteresis_positive)*100


                    # Hysteresis smooth 
                    # Repeat the same process but for the smoothed area under the curve values
                    smooth_hysteresis_positive = precon_df.loc[(precon_df.Cycle.str.contains('1')) & (precon_df['Area_under_curve_smooth'] > 0), 'Area_under_curve_smooth'].sum()
                    smooth_hysteresis_negative = precon_df.loc[(precon_df.Cycle.str.contains('5')) & (precon_df['Area_under_curve_smooth'] < 0), 'Area_under_curve_smooth'].sum()
                    smooth_hysteresis_sum = hysteresis_positive + hysteresis_negative
                    smooth_percentage = (hysteresis_sum/hysteresis_positive)*100

                    ##### STRESS-RELAXATION #####

                    stress_rate = ((stressrelax_df.iloc[0,5] - stressrelax_df.iloc[6000,5])/60)

                    ##### FAILURE #####

                    ## Failure analysis - normalise/correct data

                    # Load correction
                    #failure_df['Load_correction'] = failure_df['Force_N'] - minf 
                    failure_df['Load_correction'] = failure_df.iloc[:, 5] - failure_df.iloc[0, 5]

                    # Displacement correction 
                    #failure_df['Displacement_correction'] = failure_df['Displacement_mm'] - minf 
                    failure_df['Displacement_correction'] = failure_df.iloc[:, 4] - failure_df.iloc[0, 4]

                    # Strain % 
                    failure_df['Strain_%'] = (failure_df['Displacement_correction']/sample_length)*100

                    # Strain (mm)
                    failure_df['Strain_mm'] = failure_df['Displacement_correction']/sample_length

                    # Stress (Mpas)
                    circumference_true = float(sample_metadata.iloc[0,9])
                    # extract the true circumference value from the metadata
                    # make use of float fuction to convert string from dataframe into a float value (number with a decimal place)
                    failure_df['Stress_Mpas'] = failure_df['Load_correction']/circumference_true

                    ## Failure analysis - modulus columns

                    # Need starting point for iteration in the modulus calculation
                    # To calculate find where stretch phase begins
                    # Create index for whole failure sheet and just the stretch phase
                    stretch_index = failure_df.loc[(failure_df.Cycle.str.contains('Stretch'))]
                    stretch_index = np.array(pd.Index.tolist(stretch_index.index))
                    failure_index = np.array(pd.Index.tolist(failure_df.index))

                    # 'Stress @ 2positions before stretch as a moving value'
                    # Subtract the first value in the whole failure sheet index from the point where the stretch cycle starts, then subtract an addition 2 
                    modulus_start = (stretch_index[0] - failure_index[0]) - 2

                    # Modulus (Mpa)
                    # The moving value is 10 rows apart, starting 2 positions before stretch
                    # Hence the +5 and -4 either side of the starting position 
                    for j in range(modulus_start,failure_df.shape[0]-5):
                        failure_df.loc[failure_df.index[j],'Modulus_mpa'] = ((failure_df.iloc[j+5,10] - failure_df.iloc[j-4,10])/(failure_df.iloc[j+5,9] - failure_df.iloc[j-4,9]))

                    # Modulus - smooth 
                    failure_df['Modulus_smooth'] = failure_df['Modulus_mpa'].rolling(window=5).mean()

                    ## Failure analysis - modulus calculations 

                    # Calculate the stress value at which failure occurs
                    # Then use this to calculate strain, force and extension at which failure occurs
                    failure_stress = failure_df['Stress_Mpas'].max()
                    failure_strain_percent = failure_df.iloc[failure_df['Stress_Mpas'].argmax(), 8]
                    failure_force = failure_df.iloc[failure_df['Stress_Mpas'].argmax(), 6]
                    failure_extension = failure_df.iloc[failure_df['Stress_Mpas'].argmax(), 7]
                    failure_time = failure_df.iloc[failure_df['Stress_Mpas'].argmax(), 2]

                    #Subset failure column to remove everything after failure point for max modulus calculation
                    subset_f = failure_df.iloc[0:failure_df['Stress_Mpas'].argmax(), ]

                    # Calculate max modulus and stress/strain at max modulus on the newly subsetted version of the failure df
                    # (The full failure df will be the one saved at the end)
                    max_modulus = subset_f['Modulus_smooth'].max()
                    stress_at_max_modulus = subset_f.iloc[subset_f['Modulus_smooth'].argmax(), 10]
                    strain_at_max_modulus = subset_f.iloc[subset_f['Modulus_smooth'].argmax(), 9]

                    ##### PROCESSING #####

                    ## Create directory for output files

                    if not os.path.exists("{}/{}".format(dir, name)):
                        os.makedirs("{}/{}".format(dir, name))

                    ## Pre-conditioning output 

                    # Pre-conditioning summary tables
                    force_data = [
                        ['General summary', ''],
                        ['Sample length', sample_length],
                        ['Minimum force', minf],
                        ['Maximum force', maxforce],
                        ['Maximum force cycle 1', maxforce_c1],
                        ['Maximum force cycle 5', maxforce_c5],
                        ['Stress-relaxtion', stress_relaxation]
                    ]
                    force_table = AsciiTable(force_data)

                    hysteresis_data = [
                        ['Hysteresis', 'Cycl 1-5'],
                        ['Positive value', hysteresis_positive],
                        ['Sum value', hysteresis_sum],
                        ['Hysteresis %', percentage]
                    ]
                    hysteresis_table = AsciiTable(hysteresis_data)

                    # Processed precon table as csv
                    precon_df.to_csv("{}/{}/precon_{}.csv".format(dir, name, name), index=False)

                    # Summary data as .txt file
                    with open("{}/{}/precon_summary_{}.txt".format(dir, name, name), 'w') as f:
                        print("Summary data for {} preconditioning...\n".format(name), file=f)
                        print(force_table.table, file=f) 
                        print(hysteresis_table.table, file=f) 
                        f.close()

                    ## Failure output

                    # Failure summary table
                    modulus_data = [
                        ['Summary', ''],
                        ['Max modulus', max_modulus],
                        ['Stress at max modulus', stress_at_max_modulus],
                        ['Strain at max modulus', strain_at_max_modulus],
                        ['Failure stress (MPa)', failure_stress],
                        ['Failure strain (%)', failure_strain_percent],
                        ['Failure force (N)', failure_force],
                        ['Failure extension (mm)', failure_extension]
                    ]
                    modulus_table = AsciiTable(modulus_data)

                    # Processed failure table as csv
                    failure_df.to_csv("{}/{}/failure_{}.csv".format(dir, name, name), index=False)

                    # Summary data as .txt file
                    with open("{}/{}/failure_summary_{}.txt".format(dir, name, name), 'w') as f:
                        print("Summary data for {} failure...\n".format(name), file=f)
                        print(modulus_table.table, file=f) 
                        f.close()

                    ## Append current sample data to the overall summary
                    all_sample_summary = all_sample_summary.append({
                        'File name': name, 
                        'Date': sample_metadata.iloc[0,0], 
                        'Sample ID': sample_metadata.iloc[0,1], 
                        'Replicate number': sample_metadata.iloc[0,6], 
                        'Sex': sample_metadata.iloc[0,3], 
                        'Age': sample_metadata.iloc[0,4], 
                        'Genotype': sample_metadata.iloc[0,5], 
                        'Sample length': sample_length, 
                        'Minimum force': minf, 
                        'Maximum force': maxforce, 
                        'Maximum force cycle 1': maxforce_c1, 
                        'Maximum force cycle 5': maxforce_c5,
                        'Stress-relaxation': stress_relaxation, 
                        'Rate of change of stress': stress_rate, 
                        'Hysteresis sum value': hysteresis_sum, 
                        'Hysteresis %': percentage, 
                        'Smoothed hysteresis sum value': smooth_hysteresis_sum,
                        'Smoothed hysteresis %': smooth_percentage, 
                        'Average diameter': sample_metadata.iloc[0,7], 
                        'Circumference': sample_metadata.iloc[0,8], 
                        'Circumference, true': sample_metadata.iloc[0,9],
                        'Max modulus': max_modulus, 
                        'Stress at max modulus': stress_at_max_modulus,
                        'Strain at max modulus': strain_at_max_modulus, 
                        'Failure stress (MPa)': failure_stress,
                        'Failure strain (%)': failure_strain_percent,
                        'Failure force (N)': failure_force,
                        'Failure extension (mm)': failure_extension,
                        'Failure time (s)': failure_time}, ignore_index=True)


                except:
                    error_log_2.append(file)
                    # Write temporary sample summary
                    all_sample_summary.to_csv("{}/temp_results_summary.csv".format(dir), index=False)
                    pass
                

            # If metadata wasn't found originally... 
            else:
                print('Metadata not found - check file name against metadata \nSkipping analysis and writing file name to error log')
                error_log.append(file)
                print('Moving on to next sample...\n')


## Write final summary table as output 
all_sample_summary.to_csv("{}/results_summary.csv".format(dir), index=False)
os.remove("{}/temp_results_summary.csv".format(dir)) 

## Write error log as text file
error_log = np.reshape(error_log, (len(error_log),1))
error_log_2 = np.reshape(error_log_2, (len(error_log_2),1))
with open("{}/error_log.txt".format(dir), 'w') as f:
    print("Error log file:\n The following files couldn't be matched to any data in the metadata file.\n This is usually due to a mismatch in naming, most likely the replicate number.\n".format(name), file=f)
    print(error_log, file=f) 
    print("\n An example of a correctly named file that can be matched to the metadata is '210409 MRC Sample B1Data'.\n It begins with date ID, followed by sample ID and replicate ID and ends with 'Data'.", file=f)
    print("\n\nThe following files had some other problem with the data such as missing failure data.\n".format(name), file=f)
    print(error_log_2, file=f) 
    f.close()
