#!/usr/bin/env python
import argparse
import os
#import nibabel
#import numpy
#from glob import glob
from subprocess import Popen, PIPE
from shutil import rmtree
import subprocess
import yaml
import CPAC.utils as cpac_utils

print("hello!")


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
parser.add_argument('analysis_id', help='A number corresponding to the'
    'ABIDE preprocessing that should be run', default="1")

# get the command line arguments
args = parser.parse_args()


print ("#### Running ABIDE group analysis #%d"%(args.analysis_id))
print ("Derivatives being analysed (pipeline::filtering::global): %s"
    %("::".join(anlaysis[args.analysis_id])))
print ("Output directory: %s"%(args.output_dir))
print ("Pheno file: %s"%(args.pheno_file))


# read in the directory to find the input files



#
#
#subjects_to_analyze = []
## only for a subset of subjects
#if args.participant_label:
    #subjects_to_analyze = args.participant_label
## for all subjects
#else:
    #subject_dirs = glob(os.path.join(args.bids_dir, "sub-*"))
    #subjects_to_analyze = \
        #[subject_dir.split("-")[-1] for subject_dir in subject_dirs]
#
## running participant level
#if args.analysis_level == "participant":
    ## find all T1s and skullstrip them
    #for subject_label in subjects_to_analyze:
        ## grab all T1s from all sessions
        #input_args = " ".join(["-i %s"%f for f in \
            #glob(os.path.join(args.bids_dir,"sub-%s"%subject_label,"anat",
                #"*_T1w.nii*")) + \
            #glob(os.path.join(args.bids_dir,"sub-%s"%subject_label,"ses-*",
                #"anat", "*_T1w.nii*"))])
        #cmd = "echo 'CPAC participant analysis: %s %s %s'"%(subject_label,
            #args.output_dir, input_args)
        #print(cmd)
        #if os.path.exists(os.path.join(args.output_dir, subject_label)):
            #rmtree(os.path.join(args.output_dir, subject_label))
        #run(cmd)
#
   ## Import packages
    #import commands
    #commands.getoutput('source ~/.bashrc')
    #import yaml
    #
    #
    ## Try and load in the subject list
    #try:
        #sublist = yaml.load(open(os.path.realpath(subject_list_file), 'r'))
    #except:
        #raise Exception ("Subject list is not in proper YAML format. Please check your file")
    #
    ## Grab the subject of interest
    #sub_dict = sublist[int(indx)-1]
    #sub_id = sub_dict['subject_id']
#
    #try:
        ## Build and run the pipeline
        #prep_workflow(sub_dict, c, pickle.load(open(strategies, 'r')), 1, p_name, plugin=plugin, plugin_args=plugin_args)
    #except Exception as e:
        #print 'Could not complete cpac run for subject: %s!' % sub_id
        #print 'Error: %s' % e
#
#
#
#elif args.analysis_level == "group":
    ## running group level
    ## generate study specific template
    #cmd = "echo 'CPAC group analysis " +  " ".join(subjects_to_analyze) + "'"
    #print(cmd)
    #run(cmd, env={"SUBJECTS_DIR": args.output_dir})
