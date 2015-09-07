# Filename:                cindercleaner.py
# Description:             cleans orphaned cinder volumes
# Supported Langauge(s):   Python 2.7.x
# Time-stamp:              <2015-09-07 16:03:43 jfulton> 
# See README.md at https://github.com/fultonj/cindercleaner
# -------------------------------------------------------
import openstackclient
import hp3parclient 
import sys
import argparse
import ConfigParser
import sqlalchemy
import json
import subprocess

def get_faulty_volumes():
    if args.verbose: 
        subprocess.call(["sudo", "multipath", "-ll"])

def cinder_uuid_to_block(cinder_uuid):
    """
    Given a cinder UUID, query the DB for connection_info from block_device_mapping 
      cinder UUID --> nova UUID --> connection_info JSON
    """
    if args.verbose: 
        print "Passed Cinder UUID %s" % cinder_uuid

    # Was this cinder_uuid ever attached to a nova instance?

    # need to map them later, this is just a hack to show connection to DB is working
    nova_uuid = cinder_uuid 
    
    try: # Read nova config to get database connection
        config = ConfigParser.SafeConfigParser()
        config.read('/etc/nova/nova.conf')
        db_con_str = config.get('database', 'sql_connection')
        if args.verbose:
            print "Found DB connection %s" % db_con_str
    except ConfigParser.NoSectionError:
        sys.exit("No databse connection section in /etc/nova/nova.conf")
    except ConfigParser.Error:
        sys.exit("Unable to read /etc/nova/nova.conf")

    # use nova table to map nova uuid to cinder connection_info
    engine = sqlalchemy.create_engine(db_con_str, isolation_level="READ UNCOMMITTED")
    connection = engine.connect()
    sql = "SELECT device_name, connection_info, volume_id "
    sql += "FROM block_device_mapping WHERE instance_uuid='%s'" % nova_uuid
    results = connection.execute(sql)
    connection_info_json = None
    for row in results:
        connection_info_json = row['connection_info']
        if args.verbose: # implicitly global
            print "device_name ", row['device_name']
            print "connection_info ", row['connection_info']
            print "volume_id ", row['volume_id']
    connection.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Cleans up orphaned Cinder volumes')
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_true", default=None)
    parser.add_argument("-b", "--block", action="store_true", default=None, 
                        help="given a cinder UUID return the block device(s)")
    parser.add_argument("uuid", help="a cinder UUID")
    parser.add_argument("-f", "--faulty", help="lists faulty volumes",
                        action="store_true", default=None)
    args = parser.parse_args()
    if len([x for x in (args.block, args.uuid) if x is not None]) == 1:
        parser.error('--block and uuid must be passed together')
    if args.block:
        cinder_uuid_to_block(args.uuid)
    if args.faulty:
        get_faulty_volumes()
    sys.exit(0)
