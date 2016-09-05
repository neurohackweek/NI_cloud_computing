# NHW16 Cluster tutorial

## Get code samples and configuration files

    https://github.com/neurohackweek/NI_cloud_computing.git

## Install starcluster

This requires python 2, so we will create a virtual environment:

    conda create --name nhw16_cluster python=2.7
    source activate nhw16_cluster

Install starcluster into the virtual environment:

    pip install starcluster

Now we configure starcluster. ```starcluster/config``` contains all of the information that we will need for executing the demo, except for your credentials. You can either edit the ```config``` file to include your credentials or you can use the ```set_keys.sh``` script as an example for setting your credentials in your environment. Which makes them a little more secure. AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY should have been provided to you. You can find AWS_USER_ID by logging into AWS, clicking on the down arrow next to your name in the top right-hand corner, and then choosing ```My Account```, the number you are looking for is labeled ```Account Id:```.

To use starcluster, you will also need to generate keypairs that will be used to login to instances. you can do this by:

     starcluster -r us-east-1 createkey -o ~/.ssh/nhw16.rsa nhw16

If you choose a different path, or a different keyname (the nhw16 at the end of the command), you will need to update the config file replacing all key references containg nhw16 with the new keyname.

## Start cluster head node

You should now be ready to start the cluster head node: 

    starcluster -c config start -c smallcluster nhw16

The ```-c config``` part of the command tells starcluster which config file to use, and is required with all calls to starcluster. This can be avoided by copying the config to ~/.starcluster/config, but otherwise just make sure to use the correct path to the config file.

The ```-c smallcuster`` arguement passed to the ```start``` command indicates that you would like to start a cluster using the ```smallcluster``` template from the config file. This can be changed to refer to a custom template.

```nhw16``` at the end of the command indicates the cluster should be named nhw16, and can be replaced with any name you like.

The smallcluster template is configured to only start the head node by default. We will add other nodes to the cluster after we have submitted jobs to be run.

The head node is an inexpensive ```t2.medium``` on-demand instance. This node cannot be interrupted by the AWS system, and can persist for multiple runs.

## Configure head node for jupyter notebook access

Rather than using X to communicate with the cluster, we will use jupyter. This is to make things a bit easier to understand. The head node should already be configured to open the neccesary ports, we just need to configure a password and certificate for jupyter notebook, and then start it up. I came up with these instructions from [here](http://blog.impiyush.me/2015/02/running-ipython-notebook-server-on-aws.html):

1. Start ```ipython``` and run the following to create a password:

    from IPython.lib import passwd
    passwd()

Copy the encoded password to a safe place, and then quite ipython.

2. Create a certifacte using these commands in bash

    mkdir -p ~/certificates
    cd ~/certificates
    openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout mycert.pem -out mycert.pem

3. Create a jupyter server configuration file

    jupyter notebook --generate-config

4. Copy the following lines to the top of the configuration file, replacing ecoded_password_string with the encoding string generated in step 1. 

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

5. start the notebook server

    jupyter notebook

6. verify that you can connect using

    http://EC2_DNS_NAME:8888

You may need to accept the certificate, and then you can login using the password.

## Other things
- [Install x2go client](http://wiki.x2go.org/doku.php/download:start) to access your instance over using X windows and the [instructions here](http://fcp-indi.github.io/docs/user/cloud.html#x2go). *Note:* this requires special configuration that is available in the C-PAC and NHW16 AMIs. This probably will not work with other AMIs.
- [Install cyberduck](https://cyberduck.io/?l=en) to browse the FCP-INDI bucket using [instructions from the preprocessed connectomes project](http://preprocessed-connectomes-project.org/abide/download.html)
