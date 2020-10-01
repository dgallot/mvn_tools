#!/usr/bin/python

from array import array
from lxml import etree
import glob, os, sys, getopt
from shutil import copyfile

def usage():
    print ('mvn-set-property.py -n <name> [-f <version>] -v <version>' )
    sys.exit(2)

def main(argv):
    updateName = ''
    updateVersion = ''
    fromVersion = ''
    testMode = False
    try:
        opts, args = getopt.getopt(argv,"htg:n:v:f:",["test=", "name=","version=", "from="])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ("-n", "--name"):
            updateName = arg
        elif opt in ("-v", "--version"):
            updateVersion = arg
        elif opt in ("-f", "--from"):
            fromVersion = arg
        elif opt in ("-t", "--test"):
            testMode = True

    if updateName == "" :
        print ('name is mandatory')
        usage()
    if updateVersion == "" :
        print ('version is mandatory')
        usage()

    for root, dirs, files in os.walk("."):    
        for file in files:
            if "target" + os.path.sep not in os.path.join(root, file) :
                 if file == "pom.xml":
                    set_property( os.path.join(root, file), updateName, updateVersion, fromVersion )

if __name__ == "__main__":
   main(sys.argv[1:])                 
   
