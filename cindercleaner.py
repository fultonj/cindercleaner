# Filename:                cindercleaner.py
# Description:             cleans orphaned cinder volumes
# Supported Langauge(s):   Python 2.7.x
# Time-stamp:              <2015-09-06 15:30:42 jfulton> 
# See README.md at https://github.com/fultonj/cindercleaner
# -------------------------------------------------------
import openstackclient
import hp3parclient 
import sys

if __name__ == "__main__":
    print len(sys.argv)
    print sys.argv
    sys.exit(0)
