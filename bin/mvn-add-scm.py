#!/usr/bin/python

from array import array
from lxml import etree
import glob, os, sys, getopt
from shutil import copyfile
from subprocess import call
from copy import deepcopy
from os.path import expanduser
from common import *
from pom import *

def updateScm(pomFile, scm):
    updated=False
    nsmap = {'m': 'http://maven.apache.org/POM/4.0.0'}
    rootNode = pomFile.getroot()
    scmNode = pomFile.find("m:scm", nsmap)    
    if scmNode is None :
        scmNode=etree.SubElement(rootNode, "scm", nsmap=rootNode.nsmap)
    developerConnectionNode = pomFile.find("m:scm/m:developerConnection", nsmap)
    if developerConnectionNode is None :
        developerConnectionNode=etree.SubElement(scmNode, "developerConnection", nsmap=scmNode.nsmap)
    if developerConnectionNode.text is None :
        developerConnectionNode.text = scm
        updated = True
    elif developerConnectionNode.text != scm :
        developerConnectionNode.text = scm
        print("Updating scm to '"+scm+"'")
        updated = True
    return updated

def usage():
    print ('mvn-add-jgitflow [-h] [-t|--test] [-q|--quiet]' )
    sys.exit(2)

def main(argv):
    testMode = False
    quiet = False    
    try:
        opts, args = getopt.getopt(argv,"hqt",["test", "quiet"])
    except getopt.GetoptError:
        usage()
    
    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ("-t", "--test"):
            testMode = True
        elif opt in ("-q", "--quiet"):
            quiet = True
    home = expanduser("~")
    scm="scm:git:ssh://"+getGitUrl(".")
    parser = etree.XMLParser(strip_cdata=False)
    pomFile = etree.parse("./pom.xml", parser)
    updated=updateScm(pomFile, scm)
    if updated :
        if testMode :
            print ( 'Testmode not saving ' )
        else :
            print ( 'Saving pom.xml' )
            if not quiet :
                call(["xmllint","--format", "pom.xml", "--output", "pom.xml.bak"])
            pomFile.write("pom.xml", xml_declaration=True, encoding="utf-8", standalone="yes")
            if not quiet :
                call(["xmllint","--format", "pom.xml", "--output", "pom.xml.new"])
                call(["diff","-y","-w", "-W", "160", "--left-column", "pom.xml.bak", "pom.xml.new"])
                call(["rm","pom.xml.new"])
                call(["rm","pom.xml.bak"])
    else :
        print ( 'File already uptodate' )
if __name__ == "__main__":
   main(sys.argv[1:])                 
   
