#!/usr/bin/python
from array import array
from lxml import etree
import glob, os, sys


def printDependencies(pomFilePath, dependencyType, findExpression, filterGroupId, filterArtifactId ):
    datas=[]
    try :
        parser = etree.XMLParser(strip_cdata=False)    
        pomFile = etree.parse(pomFilePath, parser)
    except etree.XMLSyntaxError, e :
        print ( "Error : " + pomFilePath + " : XMLSyntaxError : " + str(e))
        return datas
    except etree.ParserError, e:
        error ( "Error : " + pomFilePath + " : ParserError : " + str(e))
        return datas
    except etree.DocumentInvalid, e :
        error ( "Error : " + pomFilePath + " : DocumentInvalid : " + str(e))
        return datas
    except AssertionError, e  :
        error ( "Error : " + pomFilePath + " : Xml Document too damaged : " + str(e))
        return datas
    except IOError, e:
        error ( root, "IOError :" + str(e))        
        return  datas
    nsmap = {'m': 'http://maven.apache.org/POM/4.0.0'}
    pomArtifactIdNode = pomFile.find('m:artifactId', nsmap);
    if pomArtifactIdNode is None :
        pomArtifactId="N/A"
    else :
        pomArtifactId = pomArtifactIdNode.text    
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
    dependencyNodes = pomFile.findall(findExpression, nsmap)
    for dependencyNode in dependencyNodes:
        line={}
        groupId = ''
        artifactId = ''
        version = ''
        for child in dependencyNode.findall('*'):
            if 'artifactId' in child.tag:
                artifactId = child.text
            if 'groupId' in child.tag:
                groupId = child.text
            if 'version' in child.tag:
                version = child.text
        realGroupId = groupId
        if '${project.groupId}' in groupId :
            realGroupId = pomGroupId
        if '${project.groupId}' == groupId :
            realGroupId = pomGroupId
        if '${groupId}' == groupId :
            realGroupId = pomGroupId      
        if filterGroupId in realGroupId:
            if filterArtifactId in artifactId :
                line['pomGroupId']=pomGroupId;
                line['pomArtifactId']=pomArtifactId;
                line['pomVersion']=pomVersion;
                line['type']=dependencyType;
                line['groupId']=realGroupId;
                line['artifactId']=artifactId;
                line['version']=version;
                datas.append(line)
    return datas

filterGroupId = ''
filterArtifactId = ''
if len(sys.argv) > 1 :
    filterGroupId = sys.argv[1]
if len(sys.argv) > 2 :
    filterArtifactId = sys.argv[2]


datas=[]

for root, dirs, files in os.walk("."):    
    for file in files:
        if "target" + os.path.sep not in os.path.join(root, file) :
             if file == "pom.xml":
#                 print ( os.path.join(root, file) )
                 d=printDependencies(os.path.join(root, file), 'D', 'm:dependencies/m:dependency', filterGroupId, filterArtifactId)
                 datas.extend(d)
                 d=printDependencies(os.path.join(root, file), 'DM', 'm:dependencyManagement/m:dependencies/m:dependency', filterGroupId, filterArtifactId)
                 datas.extend(d)

versionsByartifactId={}
dmVersions={}

for item in datas:
    pomGroupId=item['pomGroupId']
    pomArtifactId=item['pomArtifactId']
    pomVersion=item['pomVersion']
    type=item['type']
    groupId=item['groupId']
    artifactId=item['artifactId']
    version=item['version']    
    realGroupId = groupId
    if '${project.groupId}' in groupId :
        realGroupId = pomGroupId
    if '${project.groupId}' == groupId :
        realGroupId = pomGroupId
    if '${groupId}' == groupId :
        realGroupId = pomGroupId      
    if type == "DM" :
        if version == "" :
            version="<ERROR>"
        else:
            dmVersions[groupId + ":" + artifactId] = version

print ( "Module dependencies" )
print ( "-------------------" )
for item in datas:
    pomGroupId=item['pomGroupId']
    pomArtifactId=item['pomArtifactId']
    pomVersion=item['pomVersion']
    type=item['type']
    groupId=item['groupId']
    artifactId=item['artifactId']
    version=item['version']    
    if version == "${project.version}" :
        continue
    if type == "DM" :
        if version == "" :
            version="<ERROR>"
    if version == "" :
       if (groupId + ":" + artifactId) in dmVersions :
           version = dmVersions[groupId + ":" + artifactId]
       else :
           version = "<ERROR MISSING DM>"
    print ( pomGroupId + ":" + pomArtifactId+"["+pomVersion+"]\t"+type+"\t"+groupId+"\t"+artifactId+"\t"+version )       
    if groupId + ":" + artifactId in versionsByartifactId :
       if version in versionsByartifactId[groupId + ":" + artifactId] :
           versionsByartifactId[groupId + ":" + artifactId][version].append(pomGroupId + ":" + pomArtifactId)
       else:
           versionsByartifactId[groupId + ":" + artifactId][version]=[]
           versionsByartifactId[groupId + ":" + artifactId][version].append(pomGroupId + ":" + pomArtifactId)
    else:
       versionsByartifactId[groupId + ":" + artifactId]={}
       versionsByartifactId[groupId + ":" + artifactId][version]=[]
       versionsByartifactId[groupId + ":" + artifactId][version].append(pomGroupId + ":" + pomArtifactId)

print ()
print ( "Module dependencies Differences" )
print ( "-------------------------------" )
for artifactId, value in versionsByartifactId.items():
    if len( value.keys() ) != 1 :
        for version, list in value.items():
          pomArtifactIds = ""
          print ( artifactId + "\t" + version + "\t" + ",".join(list))
