#!/usr/bin/python

from array import array
from lxml import etree
import glob, os, sys, getopt
from shutil import copyfile


def updateDependencies(pomFile, labelExpression, findExpression, updateGroupId, updateArtifactId, updateVersion, fromVersion):
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
        if 'project.groupId' in groupId :
            groupId = pomGroupId        
        if updateGroupId in groupId:
            if updateArtifactId == artifactId:
                if version != "" :
                    if version != "${project.version}" :
                        if len(fromVersion) == 0 or version == fromVersion :
                            print ( "updateVersion : " + updateVersion + ', version = ' + version )
                            if version != updateVersion :
                                updated = True
                                print ( "Update "+labelExpression+ " " + groupId + ":" + artifactId + " from " + version + " to " + updateVersion )
                                for child in dependencyNode.findall('*'):
                                    if 'version' in child.tag:
                                        child.text = updateVersion
    return updated

def usage():
    print ('update_mavendep.py -g <group> -a <artifact> [-f <version>] -v <version>' )
    sys.exit(2)

def main(argv):
    updateGroupId = ''
    updateArtifactId = ''
    updateVersion = ''
    fromVersion = ''
    testMode = False
    try:
        opts, args = getopt.getopt(argv,"htg:a:v:f:",["test", "group=","artifact=","version=", "from="])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ("-g", "--group"):
            updateGroupId = arg
        elif opt in ("-a", "--artifact"):
            updateArtifactId = arg
        elif opt in ("-v", "--version"):
            updateVersion = arg
        elif opt in ("-f", "--from"):
            fromVersion = arg
        elif opt in ("-t", "--test"):
            testMode = True

    if updateGroupId == "" :
        print ('group is mandatory')
        usage()
    if updateArtifactId == "" :
        print ('artifact is mandatory')
        usage()
    if updateVersion == "" :
        print ('version is mandatory')
        usage()

    for root, dirs, files in os.walk("."):    
        for file in files:
            if "target" + os.path.sep not in os.path.join(root, file) :
                 if file == "pom.xml":
                     parser = etree.XMLParser(strip_cdata=False)
                     pomFile = etree.parse(os.path.join(root, file), parser)
                     updated=updateDependencies(pomFile, 'dependencies', 'm:dependencies/m:dependency', updateGroupId, updateArtifactId, updateVersion, fromVersion)
                     updated=updated | updateDependencies(pomFile, 'dependencyManagement', 'm:dependencyManagement/m:dependencies/m:dependency',  updateGroupId, updateArtifactId, updateVersion, fromVersion) 
                     if updated :
                         print ( 'Saving ' + os.path.join(root, file) )
                         copyfile(os.path.join(root, file), os.path.join(root, file) + '.bak')
                         pomFile.write(os.path.join(root, file), xml_declaration=True, encoding="utf-8", standalone="yes")

if __name__ == "__main__":
   main(sys.argv[1:])                 
   
