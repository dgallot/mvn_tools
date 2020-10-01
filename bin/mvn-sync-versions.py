#!/usr/bin/python

from array import array
from lxml import etree
import glob, os, sys, getopt
from shutil import copyfile

def loadDependencies(pomFile, dependencyType, nodeXpath ):
    datas=[]
    nsmap = {'m': 'http://maven.apache.org/POM/4.0.0'}
    pomId=getPomId(pomFile)
    
    artifactId = pomFile.find('m:artifactId', nsmap).text;
    groupId = pomFile.find('m:groupId', nsmap).text;
    version = pomFile.find('m:version', nsmap).text;
    parentGroupId = pomFile.find('m:parent/m:groupId', nsmap).text;
    parentArtifactId = pomFile.find('m:parent/m:artifactId', nsmap).text;
    parentVersion = pomFile.find('m:parent/m:version', nsmap).text;
    dependencyNodes = pomFile.findall(nodeXpath, nsmap)
    for dependencyNode in dependencyNodes:
        line={}
        groupId = ''
        artifactId = ''
        version = ''
        for child in dependencyNode.findall('*'):
            if 'artifactId' in child.tag:
                dependencyArtifactId = child.text
            if 'groupId' in child.tag:
                dependencyGroupId = child.text
            if 'version' in child.tag:
                dependencyVersion = child.text
        realGroupId = groupId
        if '${project.groupId}' in groupId :
            realGroupId = pomGroupId
        if '${project.groupId}' == groupId :
            realGroupId = pomGroupId
        if '${groupId}' == groupId :
            realGroupId = pomGroupId      
        line['groupId']=groupId;
        line['artifactId']=artifactId;
        line['version']=version;
        line['groupId']=parentPomGroupId;
        line['artifactId']=parentPomArtifactId;
        line['version']=pomVersion;
        line['type']=dependencyType;
        line['groupId']=realGroupId;
        line['artifactId']=artifactId;
        line['version']=version;
        datas.append(line)
    return datas


def loadProperties(pomFile):
    updated = False
    nsmap = {'m': 'http://maven.apache.org/POM/4.0.0'}
    pomArtifactId = pomFile.find('m:artifactId', nsmap).text;
    pomGroupIdNode = pomFile.find('m:groupId', nsmap);
    parentPomGroupIdNode = pomFile.find('m:parent/m:groupId', nsmap);
    pomVersionNode = pomFile.find('m:version', nsmap);    
    parentPomVersionNode = pomFile.find('m:parent/m:version', nsmap);
    if pomGroupIdNode is not None:
        pomGroupId = pomGroupIdNode.text
    else:
        if parentPomGroupIdNode is not None:
            pomGroupId = parentPomGroupIdNode.text
        else:
            pomGroupId = "N/A"
    if pomVersionNode is not None:
      pomVersion = pomVersionNode.text
    else :
        if parentPomVersionNode is not None:
            pomVersion = parentPomVersionNode.text
        else :
            pomVersion = ""
    propertiesNodes = pomFile.findall("m:properties", nsmap)
    for propertiesNodes in propertiesNodes:
        for propertyNode in propertiesNodes.getchildren():
            if not "Comment" in str( type ( propertyNode )):
                name=etree.QName(propertyNode).localname;
                value=propertyNode.text;
                if name == updateName :
                    if ( fromValue != '' ) or ( value != fromValue ) :
                        if value != updateValue :
                            print ( "updateProperty : " + name + "'"+value+"' -> '"+updateValue+"'" )
                            updated = True
                            propertyNode.text = updateValue
    return updated


dependencies=[]

for root, dirs, files in os.walk("."):    
    for file in files:
        if "target" + os.path.sep not in os.path.join(root, file) :
             if file == "pom.xml":
                 pomFile = xml.parse(os.path.join(root, file))
                 dependencies.extend( loadDependencies(pomFile, 'D', 'm:dependencies/m:dependency') )
                 dependencies.extend( loadDependencies(pomFile, 'DM', 'm:dependencyManagement/m:dependencies/m:dependency')
                 p=loadProperties(pomFile)
                 datas.extend(d)
