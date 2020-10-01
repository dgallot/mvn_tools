#!/usr/bin/python
from __future__ import print_function
from common import *
from pom import *
import getopt, sys

def usage():
    print ( "mvn_set_parent [-h|--help] mvn_id" )

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print ( str(err) )
        usage()
        sys.exit(2)
    parentMvnId = None    
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        else:
            assert False, "Unhandled option"    
    if len(args) == 0 : 
        print("Missing parent id")
        usage()
        sys.exit()
    parentMvnIds=args[0].split("/")
    if not len(parentMvnIds) == 3 :
        print("Parent id is invalid, correct format is group/artifact/version")
        usage()
        sys.exit()        
    parentGroupId=parentMvnIds[0]
    parentArtifactId=parentMvnIds[1]
    parentVersion=parentMvnIds[2]    
    print ( "changing pom's parent to " + parentGroupId + "/" + parentArtifactId +"/" + parentVersion)
    forEachPom( lambda root, file, pom : updatePomParentVersionV2(root,file,pom,parentGroupId,parentArtifactId,parentVersion), lambda root, error : print(root + "\t Error : " + error ) )

def updatePomParentVersion(root,file,pom,parentGroupId,parentArtifactId,parentVersion):
    pomId=getPomId(pom)
    pomMvnId=pomIdToStr(pomId)
    pomParentMvnId=parentPomIdToStr(pomId)
    print ( "Changing pom : " + pomMvnId )
    if pomId["parentGroupId"] is not None :
        if pomId["parentGroupId"] != parentGroupId :
            print ("Cannot set new parent pom, pom has already a parent pom : " + pomParentMvnId )
    if pomId["parentArtifactId"] is not None :
        if pomId["parentArtifactId"] != parentGroupId :
            print ("Cannot set new parent pom, pom has already a parent pom : " + pomParentMvnId )
    if pomId["parentVersion"] is not None :
        print ("Updating parent from '" + pomParentMvnId + "' to '"+ parentGroupId + "/" + parentArtifactId +"/" + parentVersion +"'" )
        setParentVersion(root,file,pom,parentVersion)
    else :
        setParent(root,file,pom,parentGroupId, parentArtifactId, parentVersion)

def updatePomParentVersionV2(root,file,pom,parentGroupId,parentArtifactId,parentVersion):
    pomId=getPomId(pom)
    pomMvnId=pomIdToStr(pomId)
    pomParentMvnId=parentPomIdToStr(pomId)
    changePom="true"
    print ( "[] Changing pom : " + pomMvnId  + " []")
    if pomId["parent"] is None :
        setParent(root,file,pom,parentGroupId, parentArtifactId, parentVersion)
    else :
        if pomId["parentGroupId"] is not None :
            if pomId["parentGroupId"] != parentGroupId :
                print ("    GroupId--> Cannot set new parent pom, pom has already a parent pom : " + pomParentMvnId )
                changePom="false"
        if pomId["parentArtifactId"] is not None :
            if pomId["parentArtifactId"] != parentArtifactId :
                print ("    ArtifactId--> Cannot set new parent pom, pom has already a parent pom : " + pomParentMvnId )
                changePom="false"
        if pomId["parentVersion"] is not None :
            if changePom == "true" :
                print ("    --> Updating parent from '" + pomParentMvnId + "' to '"+ parentGroupId + "/" + parentArtifactId +"/" + parentVersion +"'" )
                setParentVersion(root,file,pom,parentVersion)



if __name__ == "__main__":
    main()