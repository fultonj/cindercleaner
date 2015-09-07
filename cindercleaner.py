# Filename:                cindercleaner.py
# Description:             cleans orphaned cinder volumes
# Supported Langauge(s):   Python 2.7.x
# Time-stamp:              <2015-09-07 13:40:48 jfulton> 
# See README.md at https://github.com/fultonj/cindercleaner
# -------------------------------------------------------
import openstackclient
import hp3parclient 
import sys
import argparse
import ConfigParser
import subprocess

def cinder_uuid_to_block(uuid):
    """
    Given a cinder UUID, query the DB for connection_info from block_device_mapping 
    """
    if args.verbose: # implicitly global
        print "Passed UUID %s" % uuid
    
    try: # Read nova config to get database connection
        config = ConfigParser.SafeConfigParser()
        config.read('/etc/nova/nova.conf')
        db_connection = config.get('database', 'sql_connection')
        if args.verbose:
            print "Found DB connection %s" % db_connection
    except ConfigParser.NoSectionError:
        sys.exit("No databse connection section in /etc/nova/nova.conf")
    except ConfigParser.Error:
        sys.exit("Unable to read /etc/nova/nova.conf")
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Cleans up orphaned Cinder volumes')
    parser.add_argument("-b", "--block", action="store_true", default=None, 
                        help="given a cinder UUID return the block device(s)")
    parser.add_argument("uuid", help="a cinder UUID")
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_true", default=None)
    args = parser.parse_args()
    if len([x for x in (args.block, args.uuid) if x is not None]) == 1:
        parser.error('--block and uuid must be passed together')
    if args.block:
        cinder_uuid_to_block(args.uuid)
    sys.exit(0)
