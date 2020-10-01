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
    print ( "remote-list-bundle [-f|--filter] [-H|--hostname <hostname>]  [-F|--format <format>] [-i|--instances <instances,...>] [-o|--output <output>]" )
    print ( "    format [ plain,simple,grid,fancy_grid,pipe,orgtbl,jira,presto,psql,rst,mediawiki,moinmoin,youtrack,html,latex,latex_raw,latex_booktabs,textile ]")
    print ( "    Connect to a remote karaf instance and list bundle url")
    
def main():
    bundles=set()
    bundlesMaps={}
    output=None
    format="grid"
    filter="*/*"    
    instances=None
    hostname=None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:H:i:F:o:", ["help", "filter=", "hostname=", "instances", "format", "output"])
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
        elif o in ("-F", "--format"):
            format = a
        elif o in ("-i", "--instances"):
            instances = a.split(',')
        elif o in ("-o", "--output"):
            output = a
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
        version=ssh.run("version")
        print ( "Connected to " + instance + "/" + version + "@" + ssh.hostname  )
        karaf=Karaf(ssh)        
        bundleList=BundleList(karaf)
        BundlesById=bundleList.list()
        bundlesMaps[instance]={}
        for id in BundlesById :
            print( "[" + instance + "] " + BundlesById[id].toStr(ver=True) )                
            mvnId=BundlesById[id].toStr()
            bundles.add( mvnId )
            if mvnId not in bundlesMaps[instance] :
                bundlesMaps[instance][mvnId]=[]
            bundlesMaps[instance][mvnId].append(BundlesById[id].version)
    if format == "none" :
        return
    headers=["Bundle", "Count"]
    headers.extend(instances)
    datas=[]
    totals={}
    for instance in instances :
        totals[instance]=0

    for bundleId in sorted(bundles) :
        if fnmatch( bundleId, filter ) :
            row=[bundleId]
            c=0
            for instance in instances :
                if bundleId in bundlesMaps[instance] :                    
                    row.append( ','.join(sorted(bundlesMaps[instance][bundleId]) ))
                    c=c+1
                    totals[instance]=totals[instance]+1
                else :
                    row.append("-" )    
            row.insert(1,str(c))
            datas.append(row)
    totalRow=["", ""]
    for instance in instances :
        totalRow.append(str(totals[instance]))
    datas.append(totalRow)
    table=format_table(headers, datas, format)
    print(table)
    if output is not None :
        with open(output, "w") as text_file:
            text_file.write(table)
        print ("Written file " + output)

if __name__ == "__main__":
    main()
