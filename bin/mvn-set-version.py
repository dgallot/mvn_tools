#!/usr/bin/python
from __future__ import print_function
from common import *
from pom import *
import getopt, sys

def usage():
    print ( "mvn_set_version $version" )

def main():
    ver = True
    sep = "/"
    args=sys.argv[1:]
    if len(args) == 0 :
        usage()
        sys.exit(2)        
    version=args[0]
    print ( " --> Changing pom's version to " + version)
    forEachPom( lambda root, file, pom : setVersion(root,file,pom,version), lambda root, error : print(root + "\t Error : " + error ) )

if __name__ == "__main__":
    main()

