
# run glm on multiple derivatives from Preprocessed Connectomes Project
# ABIDE Preprocessed ata

# we will be fetching stuff from S3, which we can do with urllib
import urllib

# get a file that contains the overall phenotype info for ABID Preproc
pheno_file_url="https://s3.amazonaws.com/fcp-indi/data/Projects/ABIDE_Initiative/Phenotypic_V1_0b_preprocessed1.csv"
pheno_file_local="Phenotypic_V1_0b_preprocessed1.csv"

# download the file
urllib.urlretrieve(pheno_file_url, pheno_file_local)


# load the pheno file to choose our participants
import pandas as pd 

pheno_df=pd.read_csv(pheno_file_local)

# choose the participants from the ABIDE paper
abide_pts_to_run = pheno_df[pheno_df['to_use']==1]

# write the outputs to a file that will be read by each node
abide_pts_to_run.write()

###

# now that we have the list of pts we are ready to setup the cluster run
import indi_

ami-12cda705