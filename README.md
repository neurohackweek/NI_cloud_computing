# NHW16 Cluster tutorial

## Get code samples and configuration files

    https://github.com/neurohackweek/NI_cloud_computing.git

## Install starcluster

This requires python 2, so we will create a virtual environment:

    conda create --name nhw16_cluster python=2.7
    source activate nhw16_cluster

Install starcluster into the virtual environment:

    pip install starcluster

### Edit the config file

Now we configure starcluster. ```starcluster/config``` contains all of the information that we will need for executing the demo, except for your credentials. You can either edit the ```config``` file to include your credentials or you can use the ```set_keys.sh``` script as an example for setting your credentials in your environment. Which makes them a little more secure. AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY should have been provided to you. You can find AWS_USER_ID by logging into AWS, clicking on the down arrow next to your name in the top right-hand corner, and then choosing ```My Account```, the number you are looking for is labeled ```Account Id:```.

To use starcluster, you will also need to generate keypairs that will be used to login to instances. you can do this by, replacing <keyname> with a unique string:

     starcluster -r us-east-1 createkey -o ~/.ssh/<keyname>.rsa <keyname>

*You will need to update the config file replacing all key references containg nhw16 with the new keyname*.

If you want to use this as your default config file, you can copy it to ~/.starcluster/config. Otherwise you will need to specify the full path and filename for the config file each time you execute the starcluster command. In the following instructions ```<config_path>``` must be replaced with the path to the config file.

## Start cluster head node

You should now be ready to start the cluster head node, replacing clustername with a unique name, you will need to use this for all starcluster commands: 

    starcluster -c <configpath>/config start -c smallcluster <clustername>

The ```-c config``` part of the command tells starcluster which config file to use, and is required with all calls to starcluster. This can be avoided by copying the config to ~/.starcluster/config, but otherwise just make sure to use the correct path to the config file.

The ```-c smallcuster``` arguement passed to the ```start``` command indicates that you would like to start a cluster using the ```smallcluster``` template from the config file. This can be changed to refer to a custom template.

```clustername``` at the end of the command indicates the cluster should be named clustername, and can be replaced with any name you like.

The smallcluster template is configured to only start the head node by default. We will add other nodes to the cluster after we have submitted jobs to be run.

The head node is an inexpensive ```t2.medium``` on-demand instance. This node cannot be interrupted by the AWS system, and can persist for multiple runs.

## Logging into the cluster headnode

You can connect to the cluster head node using the command ```sshmaster``` which is abbreviated as ```sm```. The ```-u``` flag specificies the username:

    starcluster -c <configpath>/config sm -u ubuntu <clustername>

## Configure head node for jupyter notebook access

Rather than using X to communicate with the cluster, we will use jupyter. This is to make things a bit easier to understand. The head node should already be configured to open the neccesary ports, we just need to configure a password and certificate for jupyter notebook, and then start it up. I came up with these instructions from [here](http://blog.impiyush.me/2015/02/running-ipython-notebook-server-on-aws.html):

First login to the head node.

Start ```ipython``` and run the following to create a password:

    from IPython.lib import passwd
    passwd()

Copy the encoded password to a safe place, and then quite ipython.

Create a certifacte using these commands in bash

    mkdir -p ~/certificates
    cd ~/certificates
    openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout mycert.pem -out mycert.pem

Create a jupyter server configuration file

    jupyter notebook --generate-config

Copy the following lines to the top of the configuration file, replacing ecoded_password_string with the encoding string generated in step 1. 

    c = get_config()
    
    # Kernel config
    c.IPKernelApp.pylab = 'inline'  # if you want plotting support always in your notebook
    
    # Notebook config
    c.NotebookApp.certfile = u'/home/ubuntu/certs/mycert.pem' #location of your certificate file
    c.NotebookApp.ip = '*'
    c.NotebookApp.open_browser = False  #so that the ipython notebook does not opens up a browser by default
    c.NotebookApp.password = u'sha1:68c136a5b064...'  #the encrypted password we generated above
    # It is a good idea to put it on a known, fixed port
    c.NotebookApp.port = 8888

Start the notebook server

Verify that you can connect using

    http://EC2_DNS_NAME:8888

You may need to accept the certificate, and then you can login using the password.

## Run cluster demo in jupyter notebook

Open another connection to AWS for debugging and other purposes

    starcluster -c <configpath>/config sm -u ubuntu <clustername>

Clone the tutorial repo into the /home/ubuntu directory on the cluster.

    cd /home/ubuntu
    git clone https://github.com/neurohackweek/NI_cloud_computing.git

In Jupyter navigate to ```abide_group_cluster.ipynb``` in the ```NI_cloud_computing``` directory.

Go through the notebook, which at the end submits jobs to the queue. In the debug terminal query SGE to determine the state of your jobs:

    qstat

Since you do not have an compute nodes yet, only the head node, the jobs should be queued but not running. On your local system add 16 compute nodes (these will be spot instances) to the cluster. This uses the ```addnode``` command, which is abbreviated ```an``` below:

    starcluster -c <configpath>/config an -n 16 <clustername>

Once the nodes come up, you should see some action on the queue

    qstat

You can use the starcluster loadbalancer to monitor your job and remove nodes once they are completed.

    starcluster -c <configpath>/config loadbalance -d -i 30 -m 20 -k 5 <clustername>

## Other things
- [Install x2go client](http://wiki.x2go.org/doku.php/download:start) to access your instance over using X windows and the [instructions here](http://fcp-indi.github.io/docs/user/cloud.html#x2go). *Note:* this requires special configuration that is available in the C-PAC and NHW16 AMIs. This probably will not work with other AMIs.
- [Install cyberduck](https://cyberduck.io/?l=en) to browse the FCP-INDI bucket using [instructions from the preprocessed connectomes project](http://preprocessed-connectomes-project.org/abide/download.html)
