#!/usr/bin/env python
import argparse
import os
import sys
import urllib
import pandas as pd
import patsy
import commands
import shutil
from create_flame_model_files import create_flame_model_files
import glob
#import nibabel
#import numpy
#from glob import glob


pipes=['ccs','cpac','dparsf','niak']
strats=['filt_global','filt_noglobal','nofilt_global','nofilt_noglobal']
derivatives=['alff','degree_binarize','degree_weighted','eigenvector_binarize',
    'eigenvector_weighted','falff','func_mean','lfcd','reho','vmhc']

def run(command, env={}):
    process = Popen(command, stdout=PIPE, stderr=subprocess.STDOUT,
        shell=True, env=env)
    while True:
        line = process.stdout.readline()
        line = str(line, 'utf-8')[:-1]
        print(line)
        if line == '' and process.poll() != None:
            break

parser = argparse.ArgumentParser(description='ABIDE Group Analysis Runner')
parser.add_argument('pheno_file', help='File containing the participant'
    'information for the analysis that will be run. This is a CSV with the'
    'participant id in the first column, the dependent variable in the'
    'second column and the remaining columns contain regressors of no interest.')
parser.add_argument('output_dir', help='The directory where the output files '
    'should be stored. If you are running group level analysis '
    'this folder should be prepopulated with the results of the'
    'participant level analysis.')
parser.add_argument('working_dir', help='The directory to use for intermediate files.')
parser.add_argument('derivative', help='a string corresponding to the derivatives'
    'that can be run. Possible values include:%s'%(", ".join(derivatives)), 
    default="reho")
parser.add_argument('analysis_id', help='A number corresponding to the'
    'ABIDE preprocessing that should be run, 0 <= n <= 15', default="1")

# get the command line arguments
args = parser.parse_args()

# Go through and check all of the arguments and decode them
analysis_id=int(args.analysis_id)
if analysis_id > 15 or analysis_id < 0:
    raise Exception("analysis id %d is out of range 0 <= n <= 16"%(analysis_id))

analysis = [pipes[analysis_id/4], strats[analysis_id%4]]

if args.derivative not in derivatives:
    print("Invalid derivative %s, valid options are %s"%(
        args.derivative,", ".join(derivatives)))
    sys.exit(1)

pheno_file=args.pheno_file
if not os.path.isfile(pheno_file):
    print("Could not find pheno file %s"%(pheno_file))
    sys.exit(1)


output_dir=args.output_dir.rstrip('/')
if not os.path.isdir(output_dir):
    print("Could not find output directory %s"%(output_dir))
    sys.exit(1)

output_dir=os.path.join(output_dir,"_".join(analysis+[args.derivative]))
if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

working_dir=args.working_dir.rstrip('/')
if not os.path.isdir(working_dir):
    print("Could not find working directory %s"%(working_dir))
    sys.exit(1)

working_dir=os.path.join(working_dir,"_".join(analysis+[args.derivative]))
if not os.path.isdir(working_dir):
    os.makedirs(working_dir)

if output_dir == working_dir:
    print("Cannot use same directory for output and working directory")
    sys.exit(1)

print ("#### Running ABIDE group analysis #%d"%(analysis_id))
print ("Derivatives being analysed (pipeline::strat): %s"
    %("::".join(analysis)))
print ("Output directory: %s"%(output_dir))
print ("Working directory: %s"%(working_dir))
print ("Pheno file: %s"%(args.pheno_file))
print ("Derivative: %s"%(args.derivative))

# read in the pheno file
pheno_df=pd.read_csv(pheno_file)
print pheno_df.head()

# add in a column that will be used to indicate dl errors
pheno_df["dl_error"] = False
pheno_df["local_file"] = pheno_df["FILE_ID"]

# configure out download string
template_str="https://s3.amazonaws.com/fcp-indi/data/Projects/ABIDE_Initiative/Outputs/[pipeline]/[strategy]/[derivative]/[file identifier]_[derivative].nii.gz"

# set the values that can be set
template_str=template_str.replace('[derivative]',args.derivative)
template_str=template_str.replace('[pipeline]',analysis[0])
template_str=template_str.replace('[strategy]',analysis[1])

# go through and download the data
for file_id in pheno_df["FILE_ID"]:
    data_str = template_str.replace('[file identifier]',file_id)
    local_file = os.path.join(working_dir,os.path.basename(data_str))

    # if the file already exists, we can skip the download
    if not os.path.isfile(local_file):
        # now download the file
        try:
            urllib.urlretrieve(data_str, local_file)
        except Exception as e:
            print "Could not download %s"%(data_str)
            pheno_df.loc[pheno_df["FILE_ID"]==file_id,"dl_error"]=True
    
    pheno_df.loc[pheno_df["FILE_ID"]==file_id,"local_file"]=local_file
    print data_str, local_file

# exclude the files that did not download from further anlaysis
pheno_df = pheno_df[pheno_df["dl_error"]==False]

# make an output file prefix
outfile_prefix=os.path.join(working_dir,"_".join(analysis))

# mrege the fines into 4D
merge_input = " ".join(pheno_df["local_file"])
merge_output = outfile_prefix + "_merge.nii.gz"

if not os.path.isfile(merge_output):
    # next we create a 4D file for the analysis using fsl merge
    merge_string = "fslmerge -t %s %s" % (merge_output, merge_input)
    
    # MERGE the outputs
    try:
        commands.getoutput(merge_string)
    except Exception as e:
        print "[!] FSL Merge failed for output: %s" % merge_output
        print "Error details: %s\n\n" % e
        raise

# now create a mask for the analysis
merge_mask_output = outfile_prefix+"_mask.nii.gz"

if not os.path.isfile(merge_mask_output):
    merge_mask_string = "fslmaths %s -abs -Tmin -bin %s" % (merge_output, merge_mask_output)
    
    # CREATE A MASK of the merged file
    try:
        commands.getoutput(merge_mask_string)
    except Exception as e:
        print "[!] CPAC says: FSL Mask failed for output: %s" % merge_mask_output
        print "Error details: %s\n\n" % e
        raise

#### now create the design.mat file

# reduce the file to just the columns that we are interested in
pheno_df=pheno_df[["SITE_ID","DX_GROUP","AGE_AT_SCAN"]]
pheno_df["AGE_AT_SCAN"]=pheno_df["AGE_AT_SCAN"]-pheno_df["AGE_AT_SCAN"].mean()
pheno_df.loc[pheno_df["DX_GROUP"]==1,"DX_GROUP"]="ASD"
pheno_df.loc[pheno_df["DX_GROUP"]==2,"DX_GROUP"]="TDC"
num_subjects = pheno_df.shape[0]

# use patsy to create the design matrix
design=patsy.dmatrix("DX_GROUP+SITE_ID+AGE_AT_SCAN-1",pheno_df)
column_names = design.design_info.column_names

# create contrasts
contrast_dict={
    "DX_GROUP[ASD]-DX_GROUP[TDC]":design.design_info.linear_constraint("DX_GROUP[ASD]-DX_GROUP[TDC]").coefs[0],
    "DX_GROUP[TDC]-DX_GROUP[ASD]":design.design_info.linear_constraint("DX_GROUP[TDC]-DX_GROUP[ASD]").coefs[0],
    }

mat_file, grp_file, con_file, fts_file = create_flame_model_files(design, \
    column_names, contrast_dict, None, [], None, [1] * num_subjects, "Treatment", \
    "_".join(analysis+[args.derivative]), args.derivative, working_dir)

print mat_file, grp_file, con_file, fts_file

rando_out_prefix=os.path.join(working_dir,"_".join(["randomise"]+analysis+[args.derivative]))

print "writing results to %s"%(rando_out_prefix)

## now we should be ready to run randomize
rando_string="randomise -i %s -o %s -d %s -t %s -m %s -n 1000 -D -T"%(merge_output, 
    rando_out_prefix, mat_file, con_file, merge_mask_output)

try:
    commands.getoutput(rando_string)
except Exception as e:
    print "[!] FSL randomise failed."
    print "Error details: %s\n\n" % e
    raise

# ## now do the clustering stuff
# fslmaths grot_tfce_corrp_tstat1 -thr 0.95 -bin -mul grot_tstat1 grot_thresh_tstat1

for i in range(1,3):
    thresh_string="fslmaths %s_tfce_corrp_tstat%d -thr 0.95 -bin -mul %s_tstat%d %s_thresh_tstat1"%(
        rando_out_prefix,i,rando_out_prefix,i,rando_out_prefix)

    try:
        commands.getoutput(thresh_string)
    except Exception as e:
        print "[!] fslmaths failed."
        print "Error details: %s\n\n" % e
        raise


# clust_string=cluster --in=grot_thresh_tstat1 --thresh=0.0001 --oindex=grot_cluster_index --olmax=grot_lmax.txt --osize=grot_cluster_size
for i in range(1,3):
    clust_string="cluster --in=%s_thresh_tstat%d --thresh=0.0001 --oindex=%s_cluster_index --olmax=%s_lmax.txt --osize=%s_cluster_size"%(
        rando_out_prefix, i, rando_out_prefix, rando_out_prefix, rando_out_prefix)
    
    try:
        commands.getoutput(clust_string)
    except Exception as e:
        print "[!] cluster failed."
        print "Error details: %s\n\n" % e
        raise

## copy results to the output directory
for f in glob.glob(rando_out_prefix+"*"):
    shutil.copy(f,output_dir)

