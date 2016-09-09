import os
from indi_aws import fetch_creds
import boto3
import yaml


creds_path="/home/ubuntu/ccraddock_indi_s3.csv"
bucket_name="fcp-indi"
bucket_prefix="/data/Projects/ABIDE_Initiative/Outputs"

bucket = fetch_creds.return_bucket(creds_path, bucket_name)
s3_list=[]

with open(creds_path,'r') as infd:
    for line in infd.readlines():
        line=line.rstrip()
        if 'User' not in line:
            line=line.split(',')
            aws_access_key_id=line[1]
            aws_secret_access_key=line[2]

s3 = boto3.client('s3',aws_access_key_id=aws_access_key_id,
                  aws_secret_access_key=aws_secret_access_key)

strats=['nofilt_global', 'nofilt_noglobal', 'filt_global', 'filt_noglobal']
pipes=['cpac', 'dparsf', 'niak', 'ccs']
derivatives={'rois_tt':['timeseries','TT'],
             'rois_ho':['timeseries','HO'],
             'rois_ez':['timeseries','EZ'],
             'rois_dosenbach':['timeseries','ND160'],
             'rois_cc400':['timeseries','CC400'],
             'rois_cc200':['timeseries','CC200'],
             'rois_aal':['timeseries','AAL'],
             'reho':['reho',''],
             'lfcd':['lfcd',''],
             'func_preproc':['preproc',''],
             'func_mean':['mean',''],
             'func_mask':['mask',''],
             'falff':['falff',''],
             'eigenvector_weighted':['ecw',''],
             'eigenvector_binarize':['ecb',''],
             'dual_regression':['dr','Smith10'],
             'degree_weighted':['dcw',''],
             'degree_binarize':['dcb',''],
             'alff':['alff',''],
             'vmhc':['vmhc','']}

for strat in strats:
    for pipeline in pipes:
        pipe_str="_".join([pipeline,strat])
        for derivative,deriv_lbls in derivatives.items():
            deriv_len=len(derivative.split("_"))
            out_derive=derivative.replace("_","-")
            deriv_prefix=os.path.join('data/Projects/ABIDE_Initiative/Outputs',pipeline,strat,derivative)
            print "iterationg through %s:%s:%s"%(pipeline,strat,derivative)
            derive_objs=bucket.objects.filter(Prefix=deriv_prefix).all()
            for from_obj in derive_objs:
                out_key=from_obj.key.replace(deriv_prefix,'')
                out_key=out_key.lstrip('/')
                fvals=out_key.split('_')
                pt_str=''
                if len(fvals) - deriv_len > 2:
                    pt_str='sub-%s'%("".join([''.join(fvals[0:2]),fvals[2]]))
                else:
                    pt_str='sub-%s'%("".join([fvals[0],fvals[1]]))
                ext='.'.join((fvals[-1].split('.'))[1:])
                fname='_'.join([pt_str,'ses-1'])
                if deriv_lbls[1] != '':
                    fname='_'.join([fname,'-'.join(['variant',deriv_lbls[1]])])
                fname='_'.join([fname,deriv_lbls[0]])                
                fname='.'.join([fname,ext])
                outkey=os.path.join('data/Projects/ABIDE_Initiative/Derivatives',pipe_str,
                                    pt_str,'ses-1','func',fname)
                #print from_obj.key
                #print outkey
                s3.copy({"Bucket": bucket_name, "Key": from_obj.key}, bucket_name, outkey)
                #break
            #break
        #break
    #break

