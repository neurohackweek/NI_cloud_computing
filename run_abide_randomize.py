### Example of calling a BIDS-APP to analyze your data
### in the AWS cloud, using a cluster, with multiple
### runs in parallel

# Download the phenotype file, so we know whats what
import urllib
import time
import os
import commands
import pandas as pd
import json


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

# reduce the dataframe to just the columns we are interested in                        
pheno_df = pheno_df[['FILE_ID','SITE_ID','DX_GROUP','AGE_AT_SCAN','func_mean_fd']]
pheno_df.columns=[u'participant_id',u'site_id',u'dx',u'age',u'mean_fd']

for ndx in pheno_df.index:
    new_sub=pheno_df.loc[ndx,u'participant_id']
    new_sub=new_sub.replace("_","")
    pheno_df.loc[ndx,'participant_id']='-'.join(['sub', new_sub])
    if pheno_df.loc[ndx,'dx']==1:
        pheno_df.loc[ndx,'dx']='ASD'
    else:
        pheno_df.loc[ndx,'dx']='TDC'

model_desc = dict(
    model='dx+site_id+age+mean_fd-1',
    contrasts=['dx[ASD]-dx[TDC]','dx[TDC]-dx[ASD]'])


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
local_file_name = "sub-%(sub_id)s/ses-%(sess_id)s/func/" + \
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

            dl_ndx=[]
            for (ndx,row) in pheno_df.iterrows():
                data_dl_config = dict(pipe_str='_'.join([pipe, strat]),
                                      sess_id=1,
                                      sub_id=(row['participant_id'].split('-'))[1],
                                      deriv_tag=deriv_vals[0])

                data_dl_string = abide_dl_link % data_dl_config
                data_local= os.path.join(deriv_in_dir, local_file_name % data_dl_config)
   
                dl_failed=False
                if not os.path.isdir(os.path.dirname(data_local)):
                    os.makedirs(os.path.dirname(data_local))
             
                if not os.path.isfile(data_local):
                    try:
                         urllib.urlretrieve(data_dl_string, data_local)
                    except:
                        print "could not download %s to %s"%(data_dl_string,data_local)
                        dl_failed = True
                
                if not dl_failed:
                    dl_ndx.append(ndx)
                    
            # add the participants.tsv to the outdir
            (pheno_df.loc[dl_ndx,]).to_csv(os.path.join(deriv_in_dir,"participants.tsv"),
                sep='\t',index=False)
            
            with open(os.path.join(deriv_in_dir,'model.json'), 'w') as outfile:
                json.dump(model_desc, outfile)

            break

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
