### Example of calling a BIDS-APP to analyze your data
### in the AWS cloud, using a cluster, with multiple
### runs in parallel

# Download the phenotype file, so we know whats what
import urllib
import time
import os
import commands
import pandas as pd

pheno_file_url = "https://s3.amazonaws.com/fcp-indi/data/Projects/" + \
                 "ABIDE_Initiative/Phenotypic_V1_0b_preprocessed1.csv"
pheno_file_local = "Phenotypic_V1_0b_preprocessed1.csv"

urllib.urlretrieve(pheno_file_url, pheno_file_local)

# Filter the pheno data to focus on the data used in the 
# original ABIDE paper 

pheno_df = pd.read_csv(pheno_file_local)
pheno_df.head()

# find the datasets that were in the ABIDE paper, and those
# with a filename
pheno_df = pheno_df.loc[(pheno_df["SUB_IN_SMP"] == 1) &
                        (pheno_df["FILE_ID"] != "no_filename"), :]

# write out a list of the participants that meet 
pheno_df.to_csv("abide_analy_pheno.csv")

timestamp = str(time.strftime("%Y_%m_%d_%H_%M_%S"))

strats = ['nofilt_global']  # , 'nofilt_noglobal', 'filt_global', 'filt_noglobal']
pipes = ['cpac']  # , 'dparsf', 'niak', 'ccs']
derivatives = {'reho': ['reho', ''],
               'lfcd': ['lfcd', ''],
               'func_mean': ['mean', ''],
               'falff': ['falff', ''],
               'eigenvector_weighted': ['ecw', ''],
               'eigenvector_binarize': ['ecb', ''],
               'degree_weighted': ['dcw', ''],
               'degree_binarize': ['dcb', ''],
               'alff': ['alff', ''],
               'vmhc': ['vmhc', '']}

# ABIDE preproc DL template
abide_dl_link = "https://fcp-indi.s3.amazonaws.com/data/Projects/ABIDE_Initiative" + \
                "/Derivatives/%(pipe_str)s/sub-%(sub_id)s/ses-%(sess_id)s/func/" + \
                "sub-%(sub_id)s_ses-%(sess_id)s_%(deriv_tag)s.nii.gz"

inputs_dir = os.path.join(os.path.expanduser('~'), "bids_in")
if not os.path.isdir(inputs_dir):
    os.makedirs(inputs_dir)

outputs_dir = os.path.join(os.path.expanduser('~'), "bids_out")
if not os.path.isdir(outputs_dir):
    os.makedirs(outputs_dir)

cluster_files_dir = os.path.join(os.path.expanduser('~'), 'cluster_logs')
if not os.path.isdir(cluster_files_dir):
    os.makedirs(cluster_files_dir)

for strat in strats:
    for pipe in pipes:
        for (deriv, deriv_vals) in derivatives.items():

            print strat, pipe, deriv

            # make the input, output, and clusterlog directories for this processing
            deriv_in_dir = os.path.join(inputs_dir, '_'.join([pipe, strat]), deriv)
            if not os.path.isdir(deriv_in_dir):
                os.makedirs(deriv_in_dir)

            deriv_out_dir = os.path.join(outputs_dir, '_'.join([pipe, strat]), deriv)
            if not os.path.isdir(deriv_out_dir):
                os.makedirs(deriv_out_dir)

            deriv_log_dir = os.path.join(cluster_files_dir, '_'.join([pipe, strat]), deriv)
            if not os.path.isdir(deriv_log_dir):
                os.makedirs(deriv_log_dir)

            for row in pheno_df.iterrows():
                data_dl_config = dict(pipe_str='_'.join([pipe, strat]),
                                      sess_id=1,
                                      sub_id=(row[1]['FILE_ID']).replace('_', ''),
                                      deriv_tag=deriv_vals[0])

                data_dl_string = abide_dl_link % data_dl_config
                print data_dl_string
            break
            # Download all of the relevant data

exit(0)

# Batch file variables
shell = commands.getoutput('echo $SHELL')

sge_template = \
    '''#! %(shell)s
## SGE batch file - %(timestamp)s
#$ -S %(shell)s
#$ -N %(job_name)s
#$ -t 1-%(num_tasks)d
#$ -V
#$ -wd %(work_dir)s
echo "Start - TASKID " %(env_arr_idx)s " : " $(date)
%(run_cmd)s
echo "End - TASKID " %(env_arr_idx)s " : " $(date)
'''
confirm_str = '(?<=Your job-array )\d+'
exec_cmd = 'qsub'

# Set up config dictionary
config_dict = {'timestamp': timestamp,
               'shell': shell,
               'job_name': 'run_example',
               'num_tasks': 16,
               'work_dir': cluster_files_dir,
               'env_arr_idx': '$SGE_TASK_ID',
               'run_cmd': '/home/ubuntu/NI_cloud_computing/run.py /home/ubuntu/NI_cloud_computing/abide_analy_pheno.csv /home/ubuntu/NI_cloud_computing /tmp reho $SGE_TASK_ID'
               }

batch_file_contents = sge_template % config_dict

batch_filepath = '/home/ubuntu/NI_cloud_computing/cluster_run.sge'
with open(batch_filepath, "w") as outfd:
    outfd.write(batch_file_contents)

import re

# Get output response from job submission
out = commands.getoutput('%s %s' % (exec_cmd, batch_filepath))

# Check for successful qsub submission
if re.search(confirm_str, out) == None:
    err_msg = 'Error submitting %s run to sge queue' % \
              (config_dict['job_name'])
    raise Exception(err_msg)
