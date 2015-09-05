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

## Python 

In my case I'm working on RHEL6. Because RHSCL is available to anyone
with RHEL-OSP (https://access.redhat.com/solutions/472793) I will use
RHSCL to get newer versions of Python. First install SCL 
(https://goo.gl/d4Ueyu) and then install python27. 
~~~
sudo subscription-manager repos --enable rhel-server-rhscl-6-rpms
sudo yum -y install python27
~~~
From there I will use scl and make an isolated Python environment with
virtualenv. You might want to create a dummy user to run this script
and then become that dummy user before doing the next steps. That way
you won't tie the installation of this script to a particular person
who might later leave your organization. 
~~~
scl enable python27 bash
mkdir ~/venv
virtualenv venv/cindercleaner --no-site-packages
source venv/cindercleaner/bin/activate
pip install pip --upgrade
~~~

