#!/usr/bin/env python
import argparse
import os
import sys
import urllib
import pandas as pd
import patsy
import shutil
from create_flame_model_files import create_flame_model_files
import glob
import json
import numpy as np
import subprocess
#import nibabel
#import numpy
#from glob import glob

__version__ = 0.1


def run(command, env={}):
    merged_env = os.environ
    merged_env.update(env)
    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, shell=True,
                               env=merged_env)
    while True:
        line = process.stdout.readline()
        line = line.encode('utf-8')[:-1]
        print(line)
        if line == '' and process.poll() != None:
            break
    if process.returncode != 0:
        raise Exception("Non zero return code: %d"%process.returncode)
 
parser = argparse.ArgumentParser(description='ABIDE Group Analysis Runner')

parser.add_argument('bids_dir', help='The directory with the input dataset '
                    'formatted according to the BIDS standard.')
parser.add_argument('output_dir', help='The directory where the output files '
                    'should be stored. If you are running group level analysis '
                    'this folder should be prepopulated with the results of the'
                    'participant level analysis.')
parser.add_argument('working_dir', help='The directory where intermediary files '
                    'are stored while working ont them.')
parser.add_argument('analysis_level', help='Level of the analysis that will be performed. '
                    'Multiple participant level analyses can be run independently '
                    '(in parallel) using the same output_dir.',
                    choices=['participant', 'group'])
parser.add_argument('model_file', help='JSON file describing the model and contrasts'
                    'that should be.')
parser.add_argument('--participant_label', help='The label(s) of the participant(s) that should be analyzed. The label '
                   'corresponds to sub-<participant_label> from the BIDS spec '
                   '(so it does not include "sub-"). If this parameter is not '
                   'provided all subjects should be analyzed. Multiple '
                   'participants can be specified with a space separated list.',
                   nargs="+")
parser.add_argument('-v', '--version', action='version',
                    version='BIDS-App example version {}'.format(__version__))
                    

args = parser.parse_args()


model_file=args.model_file
if not os.path.isfile(model_file):
    print("Could not find model file %s"%(model_file))
    sys.exit(1)

output_dir=args.output_dir.rstrip('/')
if not os.path.isdir(output_dir):
    print("Could not find output directory %s"%(output_dir))
    sys.exit(1)

working_dir=args.working_dir.rstrip('/')
if not os.path.isdir(working_dir):
    print("Could not find working directory %s"%(working_dir))
    sys.exit(1)

bids_dir=args.bids_dir.rstrip('/')
if not os.path.isdir(working_dir):
    print("Could not find bids directory %s"%(bids_dir))
    sys.exit(1)

print ("\n")
print ("## Running randomize pipeline with parameters:")
print ("Output directory: %s"%(bids_dir))
print ("Output directory: %s"%(output_dir))
print ("Working directory: %s"%(working_dir))
print ("Pheno file: %s"%(args.model_file))
print ("\n")

# read in the pheno file
pheno_df=pd.read_csv(os.path.join(bids_dir, 'participants.tsv'),sep='\t')

# remove rows that have empty elements
pheno_df=pheno_df.dropna()

# go through data, verify that we can find a corresponding entry in
# the pheno file, and keep track of the indices so that we can 
# reorder the pheno to correspond
file_list=[]
pheno_key_list=[]
for root, dirs, files in os.walk(bids_dir):
    for filename in files:
        if not filename.endswith(".nii.gz"):
            continue
        f_chunks = (filename.split(".")[0]).split("_")
        # make a dictionary from the key-value chunks
        f_dict = {chunk.split("-")[0]:"-".join(chunk.split("-")[1:]) for chunk in f_chunks[:-1]}
        pheno_flags=pheno_df["participant_id"]==("-".join(["sub",f_dict["sub"]]))
        if pheno_flags.any():
            pheno_key_list.append(np.where(pheno_flags)[0][0])
            file_list.append(os.path.join(root,filename))

# merge the fines into 4D
merge_input = " ".join(file_list)
merge_output = os.path.join(working_dir,"rando_pipe") + "_merge.nii.gz"

print "merging",merge_output

if not os.path.isfile(merge_output):
    # next we create a 4D file for the analysis using fsl merge
    merge_string = "fslmerge -t %s %s" % (merge_output, merge_input)
    
    # MERGE the outputs
    try:
        run(merge_string)
    except:
        print "[!] FSL Merge failed for output" 
        raise
else:
    print "%s already exists, skipping merge"%(merge_output)

# now create a mask for the analysis
merge_mask_output = os.path.join(working_dir,"rando_pipe")+"_mask.nii.gz"

print "Masking",merge_mask_output
if not os.path.isfile(merge_mask_output):
    merge_mask_string = "fslmaths %s -abs -Tmin -bin %s" % (merge_output, merge_mask_output)
    
    # CREATE A MASK of the merged file
    try:
        run(merge_mask_string)
    except:
        print "[!] FSL Mask failed for output" 
        raise

#### now create the design.mat file
# reduce to the rows that we are using, and reorder to match the file list
pheno_df=pheno_df.iloc[pheno_key_list,:]

# load in the model 
with open(model_file) as model_fd:    
    model_dict = json.load(model_fd)

incols=model_dict["model"].replace("-1","").replace("-","+").split("+")

# reduce the file to just the columns that we are interested in
pheno_df=pheno_df[incols]

#de mean all numberic columns
for df_ndx in pheno_df.columns:
    if np.issubdtype(pheno_df[df_ndx].dtype,np.number):
        pheno_df[df_ndx]-=pheno_df[df_ndx].mean()

# use patsy to create the design matrix
design=patsy.dmatrix(model_dict["model"],pheno_df,NA_action='raise')
column_names = design.design_info.column_names

# create contrasts
contrast_dict={}
num_contrasts=0
for k in model_dict["contrasts"]:
    num_contrasts+=1
    contrast_dict[k]=design.design_info.linear_constraint(k.encode('ascii')).coefs[0]

num_subjects=len(file_list)
mat_file, grp_file, con_file, fts_file = create_flame_model_files(design, \
    column_names, contrast_dict, None, [], None, [1] * num_subjects, "Treatment", \
    "repro_pipe_model", [], working_dir)

rando_out_prefix=os.path.join(working_dir,"rando_pipe")

print "writing results to %s"%(rando_out_prefix)

## now we should be ready to run randomize
rando_string="randomise -i %s -o %s -d %s -t %s -m %s -n 10 -D -T"%(merge_output, 
    rando_out_prefix, mat_file, con_file, merge_mask_output)

try:
    run(rando_string)
except:
    print "[!] FSL randomise failed."
    raise

# ## now do the clustering stuff
# fslmaths grot_tfce_corrp_tstat1 -thr 0.95 -bin -mul grot_tstat1 grot_thresh_tstat1

for i in range(1,num_contrasts+1):
    thresh_string="fslmaths %s_tfce_corrp_tstat%d -thr 0.95 -bin -mul %s_tstat%d %s_thresh_tstat%d"%(
        rando_out_prefix,i,rando_out_prefix,i,rando_out_prefix,i)

    try:
        print "Threshold tstat%d"%(i)
        run(thresh_string)
    except:
        print "[!] FSL fslmaths thresh failed."
        raise

# clust_string=cluster --in=grot_thresh_tstat1 --thresh=0.0001 --oindex=grot_cluster_index --olmax=grot_lmax.txt --osize=grot_cluster_size
for i in range(1,num_contrasts+1):
    clust_string="cluster --in=%s_thresh_tstat%d --thresh=0.0001 --oindex=%s_cluster_index --olmax=%s_lmax.txt --osize=%s_cluster_size"%(
        rando_out_prefix, i, rando_out_prefix, rando_out_prefix, rando_out_prefix)
    
    try:
        run(clust_string)
    except:
        print "[!] FSL cluster failed."
        raise

## copy results to the output directory
for f in glob.glob(rando_out_prefix+"*"):
    shutil.copy(f,output_dir)
