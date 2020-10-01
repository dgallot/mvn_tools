#!/usr/bin/python
from __future__ import print_function
from common import *
import functools
import spur
import re
from karaf import *
from tabulate import tabulate
from fnmatch import fnmatch


def usage():
    print ( "remote-list-imports-bundle [-H|--hostname <hostname>] [-i|--instance <instance>]" )
    print ( "    Connect to a remote karaf instance and list imports of all bundle")
    
def main():
    bundles=set()
    bundlesMaps={}
    instance=None
    hostname=None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hH:i:", ["help", "hostname=", "instance"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print ( str(err) )
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-H", "--hostname"):
            hostname = a
        elif o in ("-i", "--instance"):
            instance = a
        else:
            assert False, "Unhandled option " + o    
    if instance is None :
        print( "Instances are required")
        usage()
        sys.exit(2)        
    if hostname is None :
        print( "Hostname is required")
        usage()    
        sys.exit(2)        
    print ( "Connecting to " + instance + "@" + hostname )
    ssh=Ssh(hostname=hostname, instance=instance)
    version=ssh.run("version")
    print ( "Connected to " + instance + "/" + version + "@" + ssh.hostname  )
    karaf=Karaf(ssh)        
    bundleList=BundleList(karaf)    
    BundlesById=bundleList.list()
    for id in BundlesById :        
        prefix=BundlesById[id].toStr(ver=False) + " " + BundlesById[id].version
        for imp in bundleList.imports(id) :
            print ( prefix + imp.package + " " + imp.version )
        
if __name__ == "__main__":
    main()
