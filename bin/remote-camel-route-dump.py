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
    print ( "remote-camel-route-dump.py [-f|--filter] [-H|--hostname <hostname>] [-i|--instances <instances,...>]" )
    print ( "Connect to a remote karaf and dump all routes" )

def main():
    bundles=set()
    bundlesMaps={}
    output=None
    format="grid"
    filter="*"    
    instances=None
    hostname=None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:H:i:F:o:", ["help", "filter=", "hostname=", "instances"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print ( str(err) )
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-f", "--filter"):
            filter = a
        elif o in ("-H", "--hostname"):
            hostname = a
        elif o in ("-i", "--instances"):
            instances = a.split(',')
        else:
            assert False, "Unhandled option " + o
    print ("filter :" + filter)
    if instances is None :
        print( "Instances are required")
        usage()
        sys.exit(2)        
    if hostname is None :
        print( "Hostname is required")
        usage()    
        sys.exit(2)        
    for instance in instances :
        print ( "Connecting to " + instance + "@" + hostname )
        ssh=Ssh(hostname=hostname, instance=instance)
        print( ssh )
        version=ssh.run("version")
        print ( "Connected to " + instance + "/" + version + "@" + ssh.hostname  )
        karaf=Karaf(ssh)
        camelRoute=CamelRoute(karaf)
        routesByName=camelRoute.list()        
        for route in routesByName :
            if fnmatch( route, filter ) :
                camelRouteInfo=camelRoute.info(route)
                print( route );
                print( camelRouteInfo.definition )
                print( "----------------------------------------------------------------------------------------------------");
        
if __name__ == "__main__" :
    main()
