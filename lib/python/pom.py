#!/usr/bin/python
from array import array
from lxml import etree
import glob, os, sys, getopt
import re
from shutil import copyfile
import sys
from pprint import pprint
import io
import pprint
import common
from tabulate import tabulate
from collections import OrderedDict, Callable
import types
from common import getStrippedText, expand_properties, hashabledict

nsmap = {'m': 'http://maven.apache.org/POM/4.0.0'}

def parentPomIdToStr(pomId, sep = "/", ver = False, prop = {}, missing_prop = set() ) :
    if ( pomId["parentGroupId"] is not None ) and ( pomId["parentArtifactId"] is not None ) and ( pomId["parentVersion"] is not None ) :
        if ver : 
            return expand_properties(pomId["parentGroupId"], prop, missing_prop) + sep + expand_properties(pomId["parentArtifactId"],prop, missing_prop) + sep + expand_properties(pomId["parentVersion"],prop, missing_prop)
        else :
            return expand_properties(pomId["parentGroupId"],prop, missing_prop) + sep + expand_properties(pomId["parentArtifactId"],prop, missing_prop)
    else :
        return ""

def pomIdToStr(pomId, sep = "/", ver = False, prop = {}, missing_prop = set() ) :    
    if ver : 
        return expand_properties(pomId["groupId"], prop, missing_prop) + sep + expand_properties(pomId["artifactId"],prop, missing_prop) + sep + expand_properties(pomId["version"],prop, missing_prop)
    else :
        return expand_properties(pomId["groupId"], prop, missing_prop) + sep + expand_properties(pomId["artifactId"],prop, missing_prop)

def getPomId(pomFile):
    tag = etree.QName(pomFile.getroot().tag)
    nsmap = {'m': tag.namespace if tag.namespace is not None else '' }
    artifactId = getStrippedText(pomFile.find('m:artifactId', nsmap));    
    groupId = getStrippedText(pomFile.find('m:groupId', nsmap));
    version = getStrippedText(pomFile.find('m:version', nsmap));
    parent = getStrippedText(pomFile.find('m:parent', nsmap));
    parentGroupId = getStrippedText(pomFile.find('m:parent/m:groupId', nsmap));
    parentArtifactId = getStrippedText(pomFile.find('m:parent/m:artifactId', nsmap));
    parentVersion = getStrippedText(pomFile.find('m:parent/m:version', nsmap));
    
    if groupId is None :
        groupId = parentGroupId
    if version is None : 
        version = parentVersion
    if not groupId is None :
        groupId = groupId.strip() 
    if artifactId is not None :
        artifactId = artifactId.strip()
    if version is not None :
        version = version.strip() 
    return { "groupId" : groupId, "artifactId" : artifactId, "version" : version, "parent" : parent ,"parentGroupId" : parentGroupId, "parentArtifactId" : parentArtifactId, "parentVersion" : parentVersion   }

def forEachPom(command, error, sources = [ "." ]) :
    for source in sources :
        for root, dirs, files in os.walk(source):    
            parser = etree.XMLParser(strip_cdata=False, recover=True)    
            for file in files:
                if "target" + os.path.sep not in os.path.join(root, file) :
                    if file == "pom.xml":
                        ret = None
                        try:
                            pomFile = etree.parse(os.path.join(root, file), parser)
                            if pomFile is None or pomFile.getroot() is None : 
                                ret = error ( root, "Xml Document too damaged")                            
                            else :
                                ret = command( root, file, pomFile )
                        except etree.XMLSyntaxError, e :
                            ret = error ( root, "XMLSyntaxError : " + str(e))
                        except etree.ParserError, e:
                            ret = error ( root, "ParserError : " + str(e))
                        except etree.DocumentInvalid, e :
                            ret = error ( root, "DocumentInvalid : " + str(e))
                        except AssertionError, e  :
                            ret = error ( root, "Xml Document too damaged : " + str(e))
                        except IOError, e:
                            ret = error ( root, "IOError :" + str(e))
                        if ret is not None :
                            if not ret :
                                return

def forCurrentPom(command, error) :
        parser = etree.XMLParser(strip_cdata=False, recover=True)    
        root="."
        try:
            pomFile = etree.parse(root+"/pom.xml", parser)
            command( root, file, pomFile )
        except etree.XMLSyntaxError, e :
            error ( root, "XMLSyntaxError : " + str(e))
        except etree.ParserError, e:
            error ( root, "ParserError : " + str(e))
        except etree.DocumentInvalid, e :
            error ( root, "DocumentInvalid : " + str(e))
        except IOError, e :
            error ( root, "IOError : " + str(e))
        except AssertionError :
            error ( root, "Xml Document too damaged")

def getFeatureDependencies(featureFile) :
    result=set()
    nsmap = {'k': 'http://karaf.apache.org/xmlns/features/v1.0.0'}
    repositoryNodes = featureFile.findall("k:repository", nsmap)    
    for repositoryNode in repositoryNodes :
        m=re.match("mvn\:(.*)\/(.*)\/(.*)\/xml\/features", getStrippedText(repositoryNode))
        if m :
            dependencyId={ "groupId": m.group(1), "artifactId": m.group(2), "version": m.group(3) }
            result.add( hashabledict(dependencyId) )
    return result

def getFeatureBundle(featureFile) :
    result=set()
    nsmap = {'k': 'http://karaf.apache.org/xmlns/features/v1.0.0'}
    bundleNodes = featureFile.findall("k:feature/k:bundle", nsmap)    
    for bundleNode in bundleNodes :
        m=re.match("(wrap\:)?mvn\:(.*)\/(.*)\/(.*)", getStrippedText(bundleNode))
        if m :
            dependencyId={ "groupId": m.group(2), "artifactId": m.group(3), "version": m.group(4) }
            result.add( hashabledict(dependencyId) )
        else :
            print (  'not match ' + getStrippedText(bundleNode) )

    return result

def getProperties(pomFile):
    result=dict()
    nsmap = {'m': 'http://maven.apache.org/POM/4.0.0'}
    propertiesNodes = pomFile.findall("m:properties", nsmap)
    for propertiesNodes in propertiesNodes:
        for propertyNode in propertiesNodes.getchildren():
            if not "Comment" in str( type ( propertyNode )):
                name=etree.QName(propertyNode).localname;
                value=propertyNode.text;
                result[name]=value
    return result

def getDependencies(pomFile, dependencyManagement = False ):
    result=set()
    pomId=getPomId(pomFile)
    if dependencyManagement :
        path = "m:dependencyManagement/m:dependencies/m:dependency"
    else :
        path = "m:dependencies/m:dependency"
    dependencyNodes = pomFile.findall(path, nsmap)
    for dependencyNode in dependencyNodes:
        dependencyId= { "groupId": '', "artifactId": '', "version": '' }
        for child in dependencyNode.findall('*'):
            if 'artifactId' in child.tag:
                dependencyId["artifactId"] = child.text
            if 'groupId' in child.tag:
                dependencyId["groupId"] = child.text
            if 'version' in child.tag:
                dependencyId["version"] = child.text
        if 'project.groupId' in dependencyId["groupId"] :
            dependencyId["groupId"] = pomId["groupId"]
        if 'project.version' in dependencyId["version"] :
            dependencyId["version"] = pomId["version"]
        result.add( hashabledict(dependencyId) )
    return result

def setVersion(root, file, pomFile, newVersion):
    nsmap = {'m': 'http://maven.apache.org/POM/4.0.0'}
    pomVersionNode = pomFile.find('m:version', nsmap);
    parentPomVersionNode = pomFile.find('m:parent/m:version', nsmap);
    if pomVersionNode is not None:
        pomVersionNode.text = newVersion
    else :
        if parentPomVersionNode is not None:
            parentPomVersionNode.text = newVersion
        else :
            print ( ' --> No artifact version or parent version found for ' +  pomFile )
    print ( ' --> for file ' + os.path.join(root,file))
    copyfile(os.path.join(root,file), os.path.join(root,file + '.bak'))
    pomFile.write(os.path.join(root, file), xml_declaration=True, encoding="utf-8", standalone="yes")
    return 'None';


def setParentVersion(root, file, pomFile, newVersion):
    nsmap = {'m': 'http://maven.apache.org/POM/4.0.0'}
    parentPomVersionNode = pomFile.find('m:parent/m:version', nsmap);
    pomId=getPomId(pomFile)    
    mvnId=pomIdToStr(pomId)
    if parentPomVersionNode is None:
        print ( 'no parent version defined for ' +  mvnId )
    else :
        parentPomVersionNode.text = newVersion
    print ( 'Updating file ' + os.path.join(root,file))
    copyfile(os.path.join(root,file), os.path.join(root,file + '.bak'))
    pomFile.write(os.path.join(root, file), xml_declaration=True, encoding="utf-8", standalone="yes")
    return 'None';

def setParent(root, file, pomFile, parentGroupId, parentArtifactId, parentVersion ):
    nsmap = {'m': 'http://maven.apache.org/POM/4.0.0'}
    pomId=getPomId(pomFile)
    parentMvnId=parentPomIdToStr(pomId)
    print ( 'Updating file ' + os.path.join(root,file) + ' setting parent pom')
    print ( ' from ' + parentMvnId )
    print ( '   to ' + parentGroupId + "/" + parentArtifactId + "/" + parentVersion )
    parentNode = pomFile.find('m:parent', nsmap);
    if parentNode is None :            
        rootNode = pomFile.getroot()                        
        parentQName=etree.QName(( etree.QName(rootNode.tag) ).namespace, "parent");
        parentNode=etree.SubElement(rootNode, parentQName, nsmap=rootNode.nsmap)
        rootNode.text="\n    "
        parentNode.tail="\n    "
        parentNode.text="\n        "
        rootNode.insert(0, parentNode)
    parentArtifiactIdNode = pomFile.find('m:parent/m:artifactId', nsmap);
    parentGroupIdNode = pomFile.find('m:parent/m:groupId', nsmap);
    parentVersionNode = pomFile.find('m:parent/m:version', nsmap);
    if parentArtifiactIdNode is None :            
        artifactIdQName=etree.QName(( etree.QName(rootNode.tag) ).namespace, "artifactId");
        parentArtifiactIdNode=etree.SubElement(parentNode, artifactIdQName, nsmap=parentNode.nsmap)                
        parentArtifiactIdNode.tail="\n        "
        rootNode.tail="\n"
    if parentGroupIdNode is None :                    
        groupIdQName=etree.QName(( etree.QName(rootNode.tag) ).namespace, "groupId");
        parentGroupIdNode=etree.SubElement(parentNode, groupIdQName, nsmap=parentNode.nsmap)                
        parentGroupIdNode.tail="\n        "
    if parentVersionNode is None :            
        versionQName=etree.QName(( etree.QName(rootNode.tag) ).namespace, "version");
        parentVersionNode=etree.SubElement(parentNode, versionQName, nsmap=parentNode.nsmap)                           
        parentVersionNode.tail="\n    "
        
    parentArtifiactIdNode.text=parentArtifactId
    parentGroupIdNode.text=parentGroupId
    parentVersionNode.text=parentVersion
    print ( 'Updating file ' + os.path.join(root,file))
    copyfile(os.path.join(root,file), os.path.join(root,file + '.bak'))
    pomFile.write(os.path.join(root, file), xml_declaration=True, encoding="utf-8", standalone="yes")

def set_property( pomFilePath, property_name, property_value, property_from_value, log_prefix="" ) :
    parser = etree.XMLParser(strip_cdata=False)
    pomFile = etree.parse(pomFilePath, parser)
    updated=updateProperties(pomFile, property_name, property_value, property_from_value, log_prefix)
    if updated :
        print ( log_prefix + 'Saving ' + pomFilePath )
        copyfile(pomFilePath, pomFilePath + '.bak')
        pomFile.write(pomFilePath, xml_declaration=True, encoding="utf-8", standalone="yes")

def updateProperties(pomFile, updateName, updateValue, fromValue, log_prefix="" ) :
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
                            print ( log_prefix + "updateProperty : " + name + "'"+value+"' -> '"+updateValue+"'" )
                            updated = True
                            propertyNode.text = updateValue
    return updated


