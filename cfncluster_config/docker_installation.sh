#!/bin/bash

# docker installation

apt-get update && apt-get upgrade
apt-get install apt-transport-https ca-certificates
apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D

release=$(cat /etc/lsb-release | grep DISTRIB_CODENAME | cut -d "=" -f 2)

case "$release" in 
	trusty)
        repo="deb https://apt.dockerproject.org/repo ubuntu-trusty main"
        ;;

    wily)
        repo="deb https://apt.dockerproject.org/repo ubuntu-wily main"
        ;;

    xenial)
        repo="deb https://apt.dockerproject.org/repo ubuntu-xenial main"
        ;;

    *)
        echo "Unknown release: $release"
        exit 1
esac

echo "$repo" >> /etc/apt/sources.list.d/docker.list

apt-get update
apt-get purge lxc-docker
apt-cache policy docker-engine
apt-get install -y linux-headers-$(uname -r)
apt-get install -y linux-image-extra-$(uname -r) 
apt-get install linux-image-extra-virtual
apt-get install -y docker-engine

service docker start

groupadd docker
usermod -aG docker ubuntu
usermod -aG docker sgeadmin
usermod -aG docker slurm


