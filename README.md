# CinderCleaner
Cleans up orphaned Cinder volumes

# Why?
The following bug is not yet resolved: https://bugzilla.redhat.com/show_bug.cgi?id=1255523

I am in the process of helping to debug it but it leaves a mess
when run by a reproducer script. We are tired of doing the clean up
by hand so I'm replacing the human process with this script. 

Disclaimer: This is not supported Red Hat Software. 

# What?
There are two cases that need to be addressed if there is a failure by
Cinder or it's driver (in this case
http://docs.openstack.org/icehouse/config-reference/content/hp-3par-driver.html).


## Faulty Multipath LUNs

- Suppose `multipath -ll` shows LUNs in a failed faulty running state. 
~~~
360002ac00000000000000bef00002de4 dm-23 3PARdata,VV
size=38G features='0' hwhandler='0' wp=rw
`-+- policy='round-robin 0' prio=0 status=active
  `- 8:0:2:3 sdr 65:16 failed faulty running
~~~
- Then we follow the "map a cinder volume to its block device" process
  in reverse (https://access.redhat.com/solutions/1579293) to get the
  nova_uuid and the cinder_uuid 
- From there we follow the same process as below (though in our
  experience the steps for stop all IO to the block device is
  sufficent). 

## Undeletable Cinder Volumes
- Suppose `cinder force-delete <volume_uuid>` returns the following in volume.log 
~~~
ERROR cinder.volume.manager Cannot delete volume $uuid: volume is busy
~~~
- Map the volume to the block device (https://access.redhat.com/solutions/1579293)
- Stop all IO to the block device:
~~~
 multipath -f 360060160045036002bee2856377ce411
 echo 1 >  /sys/block/sdi/device/delete
 echo 1 >  /sys/block/sdf/device/delete
 echo 1 >  /sys/block/sdl/device/delete
 echo 1 >  /sys/block/sdc/device/delete
~~~
- Send a removevlun to the SAN to unexport the LUN (https://pypi.python.org/pypi/hp3parclient/3.1.3)
- Send a removevv to the SAN to delete the LUN (https://pypi.python.org/pypi/hp3parclient/3.1.3)
- Delete the cinder volume (http://developer.openstack.org/api-ref-blockstorage-v2.html#deleteVolume)
- Only if that fails, should we connect to MySQL and clean it manually

# How?

## Installation

### Create a user and location for the script to reside

Create a service user to run this script so that you may add it to a
crontab without tying it to a real person who might later leave your
organization. 
~~~
sudo useradd cindercleaner
~~~
This user will need to execute a few commands normally requiring root
access like `multipath -ll` so next we run `sudo visudo` to add the
following lines to `/etc/sudoers`. 
~~~
cindercleaner ALL= NOPASSWD: MULTIPATH
Cmnd_Alias MULTIPATH=/sbin/multipath -ll
~~~
This user will also need read-access to some OpenStack configuration
files which can be arranged with the following ACL commands. 
~~~
sudo setfacl -m u:cindercleaner:r /etc/cinder/cinder.conf
sudo setfacl -m u:cindercleaner:r /etc/nova/nova.conf
~~~
Next we will use Python's virtenv to install an isolated Python in
this user's home directory. 

### Install an isolated Python with the necessary libraries

In my case I'm working on RHEL6. Because RHSCL is available to anyone
with RHEL-OSP (https://access.redhat.com/solutions/472793) I will use
RHSCL to get newer version of Python without interfering with the one
that came with the system. First install RHSCL (https://goo.gl/d4Ueyu)
and then install python27. I will also install gcc to build what I
install later with pip. You will also need to install git to get the
cindercleaner script. 
~~~
sudo subscription-manager repos --enable rhel-server-rhscl-6-rpms
sudo yum -y install python27 gcc git 
sudo su - cindercleaner
~~~
From there I will become the utility user and use scl and make an
isolated Python environment in that users with virtualenv. 
~~~
scl enable python27 bash
mkdir ~/venv
virtualenv venv/cindercleaner --no-site-packages
source venv/cindercleaner/bin/activate
pip install pip --upgrade
~~~
Next I will install my Python libraries.
~~~
pip install python-openstackclient
pip install hp3parclient
pip install ipython 
~~~
Note that ipython was optional.

After doing the above I was able to create a shell wrapper (called
cindercleaner) which calls scl to enable the python 2.7 installed 
by SCL and then use that python to call the Python created by my
virtenv and pass the arguments along so that Python can deal with
them. The resulting cindercleaner.py is then able to `import
openstackclient` and `import hp3parclient`. 

### Download and test the script

Download
~~~
sudo su - cindercleaner
git clone https://github.com/fultonj/cindercleaner.git
~~~
Run
~~~
/home/cindercleaner/cindercleaner/cindercleaner --help
~~~
The above looks redundant but can be explained as: 
~~~
/home/cindercleaner/cindercleaner/cindercleaner 
      ^ home dir    ^ proj dir    ^ actual script
~~~

### Debug in interactive Python 

If you want to interact directly with Python and the installed
libraries then you may do the following. 
~~~
sudo su - cindercleaner
scl enable python27 bash
source venv/cindercleaner/bin/activate
ipython
~~~
