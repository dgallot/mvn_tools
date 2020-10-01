#!/usr/bin/python

from array import array
from lxml import etree
import glob, os, sys, getopt
from shutil import copyfile
from subprocess import call
from copy import deepcopy
from os.path import expanduser

def updateProperty(pomFile, name, value):
    updated = False
    found = False
    nsmap = {'m': 'http://maven.apache.org/POM/4.0.0'}
    propertiesNodes = pomFile.findall("m:properties", nsmap)
    for propertiesNodes in propertiesNodes:
        for propertyNode in propertiesNodes.getchildren():
            if not "Comment" in str( type ( propertyNode )):
                currentName=etree.QName(propertyNode).localname;
                currentValue=propertyNode.text;
                if currentName == name :
                    found = True
                    if currentValue != value :
                        print ( "udpateProperty : " + name + "'"+currentValue+"' -> '"+value+"'" )
                        updated = True
                        propertyNode.text = value
    if not found :
        parentNode = pomFile.find("m:properties", nsmap)
        if parentNode is None :            
            rootNode = pomFile.getroot()                        
            propertiesName=etree.QName(( etree.QName(rootNode.tag) ).namespace, "properties");
            parentNode=etree.SubElement(rootNode, propertiesName, nsmap=rootNode.nsmap)            
        parentNodeName=etree.QName(parentNode);
        name=etree.QName(parentNodeName.namespace, name);
        propertyNode=etree.SubElement(parentNode, name, nsmap=parentNode.nsmap)
        propertyNode.text = value
        updated=True
    return updated


def updateProperties(pomFile, templatePomFile):
    updated = False
    print ( etree.tostring(templatePomFile, pretty_print=True) )
    nsmap = {'m': 'http://maven.apache.org/POM/4.0.0'}
    propertiesNodes = templatePomFile.findall("m:properties", nsmap)
    for propertiesNodes in propertiesNodes:
        for propertyNode in propertiesNodes.getchildren():
            if not "Comment" in str( type ( propertyNode )):
                currentName=etree.QName(propertyNode).localname;
                currentValue=propertyNode.text;
                print ("Checking property '"+currentName+"' with value '"+currentValue+"'")
                updated = updated or updateProperty(pomFile, currentName, currentValue)
    return updated

def updateBuildPlugins(pomFile, templatePomFile):
    updated = False
    nsmap = {'m': 'http://maven.apache.org/POM/4.0.0'}
    pluginsNodes = templatePomFile.findall("m:build/m:plugins", nsmap)
    for pluginsNode in pluginsNodes:
        for pluginElement in pluginsNode.getchildren():
            artifactId = pluginElement.find('m:artifactId', nsmap).text;
            groupId = pluginElement.find('m:groupId', nsmap).text;
            print ("Checking plugin  '"+artifactId+"/"+ groupId+"'")
            updated = updated or updateBuildPlugin(pomFile, pluginElement, artifactId, groupId)
    return updated

def updateBuildPlugin(pomFile, pluginElement, artifactId, groupId):
    found = False
    nsmap = {'m': 'http://maven.apache.org/POM/4.0.0'}
    pluginsNodes = pomFile.findall("m:build/m:plugins", nsmap)
    for pluginsNode in pluginsNodes:
        for currentPluginElement in pluginsNode.getchildren():
            currentArtifactIdNode = currentPluginElement.find('m:artifactId', nsmap)
            if currentArtifactIdNode is not None :
                currentArtifactId = currentArtifactIdNode.text
            else :
                print ("ERROR : Error in plugins section of pom. missing artifactId in plugin definition")
                currentArtifactId = "None"
            currentGroupIdNode = currentPluginElement.find('m:groupId', nsmap)
            if currentGroupIdNode is not None :
                currentGroupId = currentGroupIdNode.text
            else :
                print ("ERROR : Error in plugins section of pom. missing groupId in plugin definition")
                currentGroupId = "None"
            if ( currentArtifactId == artifactId ) and ( currentGroupId == groupId ) :
                print("Updating plugins  '"+artifactId+"/"+ groupId+"'")
                found = True
                for children in currentPluginElement.getchildren():
                    currentPluginElement.remove(children)
                for children in pluginElement.getchildren():
                    currentPluginElement.append(deepcopy(children))                
    if not found :
        rootNode = pomFile.getroot()
        buildParentNode = pomFile.find("m:build", nsmap)
        if buildParentNode is None :
            buildName=etree.QName(( etree.QName(rootNode.tag) ).namespace, "build");
            buildParentNode=etree.SubElement(rootNode, buildName, nsmap=rootNode.nsmap)
        pluginsParentNode = pomFile.find("m:build/m:plugins", nsmap)
        if pluginsParentNode is None :
            pluginsParentNode=etree.SubElement(buildParentNode, "plugins", nsmap=buildParentNode.nsmap)
        pluginsParentNode.append(deepcopy(pluginElement))
        updated=True        
    return True

def usage():
    print ('mvn-add-jgitflow [-h] [-t|--test] [-q|--quiet] [f|--templatefile jgitflow.xml|scm.xml] ' )
    sys.exit(2)

def main(argv):
    testMode = False
    quiet = False
    template_file = None 
    try:
        opts, args = getopt.getopt(argv,"hqtf:",["test", "quiet", "templatefile="])
    except getopt.GetoptError:
        usage()
    
    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ("-t", "--test"):
            testMode = True
        elif opt in ("-q", "--quiet"):
            quiet = True
        elif opt in ("-f", "--templatefile"):
            template_file=arg
    home = expanduser("~")
    if template_file is None :
        print("Error : template file is mandatory")
        usage()
        sys.exit(2)
    print ( home+"/etc/"+template_file )
    if os.path.isfile(template_file) :
        print("Using template file '"+template_file+"'")
    elif os.path.isfile(home+"/etc/"+template_file) :
        template_file=home+"/etc/"+template_file
        print("using template file '"+template_file+"'")
    else :
        print("Error : template file not found. Checked '"+template_file+"' and '"+home+"/etc/"+template_file+"'")        
        sys.exit(2)
    parser = etree.XMLParser(strip_cdata=False)
    templatePomFile=etree.parse(template_file, parser )
    pomFile = etree.parse("./pom.xml", parser)
    updated=updateProperties(pomFile, templatePomFile)
    updated=updateBuildPlugins(pomFile, templatePomFile)
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
   
