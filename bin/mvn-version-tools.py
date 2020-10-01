#!/usr/bin/python

from __future__ import print_function
from common import *
import functools
import sys
from fnmatch import fnmatch, translate
from pom import *
from pprint import *
import os.path
from colorama import init, Fore, Back, Style

class UnknownVersionWorkItem :
    mvn_id = None
    dtype = None
    def __init__(self, dtype, pomId, dependencyId, err) :
        self.dtype=dtype
        self.pomId=pomId
        self.dependencyId=dependencyId
        self.err = err
    def __str__(self) :
        return "[!!!MANUAL] File: %s. Unable to deduce version of %s [%s] found in %s : %s." % ( self.pomId["file"], pomIdToStr(self.dependencyId, ver = False), self.dtype, pomIdToStr(self.pomId, ver = False), self.err )    
    def update(self) :
        return None

class UnknownPropertyWorkItem :
    ownerPomId = None
    property_name = None
    lastParentId = None 
    def __init__(self, ownerPomId, property_name, lastParentId) :
        self.ownerPomId=ownerPomId
        self.property_name=property_name
        self.lastParentId = lastParentId

    def __str__(self) :
        if self.lastParentId is None :
            return "File: %s. Property definition not found for ${%s}." % ( self.ownerPomId["file"], self.property_name )
        else :
            return "File: %s. Property definition not found for ${%s}. Missing parent %s" % ( self.ownerPomId["file"], self.property_name, pomIdToStr(self.lastParentId, ver = False) )

    def update(self) :
        return None

class FeatureWorkItem :
    ownerPomId = None
    ftype = None
    featurefile = None
    groupId = None
    artifactId = None
    version = None
    
    def __init__(self, featurefile, ftype, ownerPomId, groupId, artifactId, current_version, new_version) :
        self.ftype=ftype
        self.featurefile=featurefile
        self.ownerPomId=ownerPomId
        self.groupId=groupId
        self.artifactId=artifactId
        self.current_version=current_version
        self.new_version=new_version        
    
    def __str__(self) :
        return "[!!!MANUAL] File: %s. Set feature dependency [%s]  %s/%s => %s [ -> %s ] " % ( self.featurefile, self.ftype, self.artifactId, self.groupId, self.current_version, self.new_version )
    
    def update() :
        # set_feature( featurefile, artifactId, groupId, version )
        None

class PropertyWorkItem :
    ownerPomId = None
    current_property_value = None
    property_name = None
    new_property_value = None
    def __init__(self, ownerPomId, property_name, current_property_value, new_property_value) :
        self.ownerPomId=ownerPomId
        self.property_name=property_name
        self.current_property_value=current_property_value
        self.new_property_value=new_property_value
        if new_property_value == current_property_value :
            raise ValueError
    def __str__(self) :
        if  self.property_name == "project.version" :
            return "[Manual!!] File: %s. Check project version hierarchy" % ( self.ownerPomId["file"] )
        else :
            return "File %s. Set property ${%s} from %s to %s" % ( self.ownerPomId["file"], self.property_name, self.current_property_value, self.new_property_value )
    
    def update(self) :
        if  self.property_name == "project.version" :
            return "[Manual!!] File: %s. Check project version hierarchy" % ( self.ownerPomId["file"] )
        else :
            set_property( self.ownerPomId["file"], self.property_name, self.new_property_value, self.current_property_value, "    " )

class DependencyWorkItem :
    ownerPomId = None
    dtype = None
    groupId = None
    artifactId = None
    version = None
    
    def __init__(self, dtype, ownerPomId, groupId, artifactId, current_version, new_version) :
        self.ownerPomId=ownerPomId
        self.groupId=groupId
        self.artifactId=artifactId
        self.current_version=current_version
        self.new_version=new_version        
        print ( self )
    
    def __str__(self) :
        return "File: %s. Set dependency [%s]  %s/%s => %s [ -> %s ] " % ( self.ownerPomId["file"], self.dtype, self.artifactId, self.groupId, self.current_version, self.new_version )
    
    def update() :
        set_dependency( pom_file, artifactId, groupId, version )

def error(root, error) :
    print("Error : " + root + " - " + error )
    
def usage():
    print ( "mvn_version_tools [-b|--bundle <bundleid> [-u|--update <version>] [-g|--green <pattern>] [-r|--red <pattern>] [-c|--colorversion <pattern>] [v|--verbose] [-f|--features] [-d|--dependencies] [-s|--sources <sources>] [-i|--include <include_dir>]" )

def main():
    bundle="*/*"
    showDependencies=False
    showFeatures=False
    coloRegExs={}
    verbose=False
    sources=["."]
    poms_properties={}
    all_poms_dependencies={}
    all_poms_dependencies_management={}
    pomIds={}
    updateVersion=None
    includes=["."]
    short=False
    workItems= []
    quiet=False
    green=None
    red=None
    colorversion=None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hb:fdvu:i:s:r:g:c:q", ["help", "bundle=", "dependencies", "features", "verbose", "colorversion=", "red=", "green=", "update=", "quiet", "include=", "sources="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print ( str(err) )
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-d", "--dependencies"):
            showDependencies=True
        elif o in ("-v", "--verbose"):
            verbose=True
        elif o in ("-u", "--update"):
            updateVersion=a
        elif o in ("-f", "--features"):
            showFeatures=True
        elif o in ("-g", "--green"):
            green=a
        elif o in ("-r", "--red"):
            red=a
        elif o in ("-c", "--colorversion"):
            colorversion=a
        elif o in ("-b", "--bundle"):
            bundle=a
        elif o in ("-i", "--include"):
            if os.path.isfile(a) :
                with open(a) as f:
                    includes=[x.strip() for x in f.readlines()]
            else:
                includes=a.replace(' ',',').split(',')            
        elif o in ("-q", "--quiet"):
            quiet=True
        elif o in ("-s", "--sources"):
            if os.path.isfile(a) :
                with open(a) as f:
                    sources = [x.strip() for x in f.readlines()]
            else:
                sources=a.replace(' ',',').split(',')
        else:
            assert False, "Unhandled option " + o
    if showDependencies == False and showFeatures == False :
        showDependencies=True
        showFeatures=True
    if "*" in bundle :
        if updateVersion is not None :
            print ( "You can only set the version of a single bundlet at a time" )
            usage()
            sys.exit(2)
    if red is not None :
        coloRegExs["red"]=translate(red)
    if green is not None :
        coloRegExs["green"]=translate(green)
    if colorversion is not None :
        coloRegExs["colorversion"]=translate(colorversion)
    missingParents=set()
    forEachPom(functools.partial(load_properties, pomIds, poms_properties ), error, includes )
    forEachPom(functools.partial(load_all_poms_dependencies, all_poms_dependencies, all_poms_dependencies_management ), error, includes )
    forEachPom(functools.partial(process, pomIds, workItems, poms_properties, all_poms_dependencies, all_poms_dependencies_management, bundle, showDependencies, showFeatures, missingParents, quiet, verbose, coloRegExs, updateVersion), error,   )
    c=0
    if updateVersion is not None :
        if len( workItems ) != 0 :
            print ( "Changes :" )
            for idx, workItem in enumerate(workItems):
                print ( "  %i : %s " % ( idx , workItem ) )
            print ( "please enter the number of the items you want to execute" )
            with open("/dev/tty", "r") as i :
                 choices=i.readline();             
            for choice in choices.replace(' ',',').split(',') :                
                workItem=workItems[int(choice)]
                print ( "  Executing : %s " % ( workItem ) )
                workItem.update()
            

def getLocationProperty(pomId, pomIds, poms_properties, missingParents, property_name ) :
    keys=poms_properties[pomIdToStr(pomId, ver = False)].keys()
    parentId=parentPomIdToStr(pomId, ver = False)
    if property_name in keys :
        return pomId
    else :
        if parentId in pomIds :             
            return getLocationProperty(pomIds[parentId], pomIds, poms_properties, missingParents, property_name )
        else :
            if parentId is not None :
                missingParents.append(parentId)
            return None

def getRecProperties(pomId, pomIds, missingParents, poms_properties) :
    result=poms_properties[pomIdToStr(pomId, ver = False)]
    parentId=parentPomIdToStr(pomId, ver = False)
    if parentId is not  None :
        if parentId in pomIds : 
            result=merge_two_dicts( getRecProperties( pomIds[parentId], pomIds, missingParents, poms_properties), result )
        else :
            missingParents.add(parentId)
    return result

def load_properties( pomIds, poms_properties, root, file, pomFile ) :
    pomId=getPomId(pomFile)
    pomId["file"]=os.path.abspath(os.path.join(root, file))
    pomIds[ pomIdToStr(pomId, ver = False) ] = pomId
    poms_properties[ pomIdToStr(pomId, ver = False) ] = getProperties(pomFile)

def load_all_poms_dependencies( all_poms_dependencies, all_poms_dependencies_management, root, file, pomFile ) :
    pomId=getPomId(pomFile)
    all_poms_dependencies[ pomIdToStr(pomId, ver = False) ] = getDependencies(pomFile)
    all_poms_dependencies_management[ pomIdToStr(pomId, ver = False) ] = getDependencies(pomFile, dependencyManagement=True)

def findInPomIdArray( pomsIds, pomIdStr ) :
    for pomId in pomsIds :
        if pomIdStr == pomIdToStr(pomId, ver = False) :
            return pomId
    return None

def getVersionFromParent(parentPomId, depPomId, pomIds, missingParents, poms_properties, all_poms_dependencies, all_poms_dependencies_management, quiet, coloRegExs ) :
    parentPomIdStr=pomIdToStr(parentPomId, ver = False)
    if not pomIdToStr(parentPomId, ver = False) in pomIds :
        missingParents.add(pomIdToStr(parentPomId, ver = False))
        if quiet :
            return ""
        else :
            return " [Missing parent "+parentPomIdStr+"]"
    resolvedParentPomId=pomIds[ pomIdToStr(parentPomId, ver = False) ]
    merged_properties=getRecProperties(resolvedParentPomId, pomIds, missingParents, poms_properties)
    merged_properties["project.groupId"]=resolvedParentPomId["groupId"]
    merged_properties["project.version"]=resolvedParentPomId["version"]
    if parentPomIdStr in all_poms_dependencies :        
        foundDepPomId=findInPomIdArray(all_poms_dependencies[parentPomIdStr], pomIdToStr(depPomId, ver = False))
        if foundDepPomId is not None :
            rawVersion=foundDepPomId["version"]            
            if rawVersion != "" :
                if quiet :
                    return hightlight_version(expand_properties(foundDepPomId["version"],merged_properties), coloRegExs)
                else :
                    return hightlight_version(expand_properties(foundDepPomId["version"],merged_properties), coloRegExs) + " -> from parent " + parentPomIdStr
    if parentPomIdStr in all_poms_dependencies_management :                
        foundDepPomId=findInPomIdArray(all_poms_dependencies_management[parentPomIdStr], pomIdToStr(depPomId, ver = False))
        if foundDepPomId is not None :
            rawVersion=foundDepPomId["version"]            
            if rawVersion != "" :
                if quiet :
                    return hightlight_version(expand_properties(foundDepPomId["version"],merged_properties), coloRegExs)
                else :
                    return hightlight_version(expand_properties(foundDepPomId["version"],merged_properties), coloRegExs) + " from [" + parentPomIdStr + "]"
    if resolvedParentPomId["parentGroupId"] is not None :
        parentPomId={ "groupId" : resolvedParentPomId["parentGroupId"], "artifactId" : resolvedParentPomId["parentArtifactId"], "version" : resolvedParentPomId["parentVersion"] } 
        return getVersionFromParent(parentPomId, depPomId, pomIds, missingParents, poms_properties, all_poms_dependencies, all_poms_dependencies_management, quiet, coloRegExs )
    else:
        return ""

def hightlight_version(version, coloRegExs) :
    if "colorversion" in coloRegExs :
        if re.compile(coloRegExs["colorversion"] ).match(version) :
            return Fore.GREEN + Style.BRIGHT + version + Fore.RESET + Style.RESET_ALL;
        else :
            return Fore.RED + Style.BRIGHT + version + Fore.RESET + Style.RESET_ALL;
    return version
            

def pomIdToStrVerboseColor(pomId, properties, quiet, coloRegExs) :
    sep='/'
    bundleId=expand_properties(pomId["groupId"], properties ) + sep + expand_properties(pomId["artifactId"],properties)    
    rawVersion=pomId["version"]
    expandedVersion=expand_properties(pomId["version"],properties)
    
    if rawVersion == expandedVersion :
        result=bundleId + sep + hightlight_version(rawVersion, coloRegExs)
    else:
        if quiet :
            result=bundleId + sep + hightlight_version(expandedVersion, coloRegExs)
        else :
            result=bundleId + sep + rawVersion + " -> " + bundleId + sep + hightlight_version(expandedVersion, coloRegExs)
    if len(coloRegExs) != 0 :
        return hightlights(result, coloRegExs)
    else :
        return hightlights(result, coloRegExs)
    
    
def dependencyPomIdToStrVerboseColor(pomId, depPomId, pomIds, missingParents, poms_properties, all_poms_dependencies, all_poms_dependencies_management, properties, quiet, coloRegExs) :
    sep='/'
    bundleId=expand_properties(depPomId["groupId"], properties ) + sep + expand_properties(depPomId["artifactId"],properties)
    rawVersion=depPomId["version"]
    if rawVersion == "" :
        if pomId["parentGroupId"] is not None :
            parentPomId={ "groupId" : pomId["parentGroupId"], "artifactId" : pomId["parentArtifactId"], "version" : pomId["parentVersion"] } 
            versionFromParent=getVersionFromParent(parentPomId, depPomId, pomIds, missingParents, poms_properties, all_poms_dependencies, all_poms_dependencies_management, quiet, coloRegExs)
            if quiet :
                result=bundleId + sep + hightlight_version(versionFromParent, coloRegExs)
            else :
                result=bundleId + " -> " + hightlight_version(versionFromParent, coloRegExs) 
            if len(coloRegExs) != 0 :
                return hightlights(result, coloRegExs)
            else :
                return hightlights(result, coloRegExs)              
    expandedVersion=expand_properties(rawVersion,properties)
    if rawVersion == expandedVersion :
        result=bundleId + sep + hightlight_version( rawVersion, coloRegExs) 
    else:
        if quiet :
            result=bundleId + sep + hightlight_version(expandedVersion, coloRegExs) 
        else :
            result=bundleId + sep + rawVersion + " -> " + bundleId + sep + hightlight_version(expandedVersion, coloRegExs) 
    if len(coloRegExs) != 0 :
        return hightlights(result, coloRegExs)
    else :
        return hightlights(result, coloRegExs)            

def check_features_workitem( ftype, feature_file, pomId, dependencyId, featureDependencies, pomIds, poms_properties, workItems, updateVersion ) :
    missingParents=set()
    merged_properties=getRecProperties(pomId, pomIds, missingParents, poms_properties)
    merged_properties["project.groupId"]=pomId["groupId"]
    merged_properties["project.version"]=pomId["version"]
    bundleId=expand_properties(dependencyId["groupId"], merged_properties ) + '/' + expand_properties(dependencyId["artifactId"],merged_properties)
    if dependencyId["version"] == "" :
        workItems.append( UnknownVersionWorkItem( "Feature", pomId, dependencyId, "Missing version " + pomIdToStr(dependencyId, ver = False) + " in " + pomIdToStr(pomId, ver = False) ))
        return
    version=expand_properties(dependencyId["version"], merged_properties)    
    if not dependencyId["version"] == version :
        # the version has not been set using properties
        properties_name=extract_properties_name(dependencyId["version"])        
        if len(properties_name) == 0 :
            workItems.append( FeatureWorkItem( ftype, feature_file, pomId, dependencyId["groupId"], dependencyId["artifactId"], dependencyId["version"], updateVersion ) )
        else :
            if len(properties_name) == 1 :
                missingParents=[]
                propertyPomid=getLocationProperty(pomId, pomIds, poms_properties, missingParents, properties_name[0] )
                if len(missingParents) == 0 :
                    if propertyPomid is None :
                        workItems.append( UnknownPropertyWorkItem( pomId, properties_name[0], None ))
                    else :
                        locationOfPomId=propertyPomid["file"]
                        if merged_properties[properties_name[0]] != updateVersion :
                            workItems.append( PropertyWorkItem( propertyPomid, properties_name[0], merged_properties[properties_name[0]], updateVersion ))
                else :
                    workItems.append( UnknownPropertyWorkItem( pomId, properties_name[0], missingParents[0] ))
            else :
                workItems.append( UnknownVersionWorkItem( dtype, pomId, dependencyId, "Version has multiple property, this is not supported" ))
    
def check_dependency_workitem( dtype, all_poms_dependencies, all_poms_dependencies_management, pomId, dependencyId, pomIds,  poms_properties, workItems, updateVersion )  :
    missingParents=set()
    merged_properties=getRecProperties(pomId, pomIds, missingParents, poms_properties)
    merged_properties["project.groupId"]=pomId["groupId"]
    merged_properties["project.version"]=pomId["version"]
    bundleId=expand_properties(dependencyId["groupId"], merged_properties ) + '/' + expand_properties(dependencyId["artifactId"],merged_properties)
    if dependencyId["version"] == "" :
        if pomId["parentGroupId"] is not None :
            parentPomId={ "groupId" : pomId["parentGroupId"], "artifactId" : pomId["parentArtifactId"], "version" : pomId["parentVersion"] } 
            parentPomIdStr=pomIdToStr(parentPomId, ver = False)
            if not pomIdToStr(parentPomId, ver = False) in pomIds :
                workItems.append( UnknownVersionWorkItem( dtype, pomId, dependencyId, "Missing parent " + parentPomIdStr ))
                return
            else :
                resolvedParentPomId=pomIds[ pomIdToStr(parentPomId, ver = False) ]
                foundDepPomId=findInPomIdArray(all_poms_dependencies[parentPomIdStr], pomIdToStr(dependencyId, ver = False))
                if foundDepPomId is not None :
                    check_dependency_workitem("D", all_poms_dependencies, all_poms_dependencies_management, resolvedParentPomId, foundDepPomId, pomIds, poms_properties, workItems, updateVersion )
                    return
                else :
                    foundDepPomId=findInPomIdArray(all_poms_dependencies_management[parentPomIdStr], pomIdToStr(dependencyId, ver = False))
                    if foundDepPomId is not None :
                        check_dependency_workitem("DL", all_poms_dependencies, all_poms_dependencies_management, resolvedParentPomId, foundDepPomId, pomIds, poms_properties, workItems, updateVersion )
                        return
                    else :
                        workItems.append( UnknownVersionWorkItem( dtype, pomId, dependencyId, "Missing parent " + parentPomIdStr ))
                        return
    version=expand_properties(dependencyId["version"], merged_properties)    
    if not dependencyId["version"] == version :
        # the version has not been set using properties
        properties_name=extract_properties_name(dependencyId["version"])        
        if len(properties_name) == 0 :
            workItems.append( DependencyWorkItem( dtype, pomId, dependencyId["groupId"], dependencyId["artifactId"], dependencyId["version"], updateVersion ) )
        else :
            if len(properties_name) == 1 :
                missingParents=[]
                propertyPomid=getLocationProperty(pomId, pomIds, poms_properties, missingParents, properties_name[0] )
                if len(missingParents) == 0 :
                    if propertyPomid is None :
                        workItems.append( UnknownPropertyWorkItem( pomId, properties_name[0], None ))
                    else :
                        locationOfPomId=propertyPomid["file"]
                        if merged_properties[properties_name[0]] != updateVersion :
                            workItems.append( PropertyWorkItem( propertyPomid, properties_name[0], merged_properties[properties_name[0]], updateVersion ))
                else :
                    workItems.append( UnknownPropertyWorkItem( pomId, properties_name[0], missingParents[0] ))
            else :
                workItems.append( UnknownVersionWorkItem( dtype, pomId, dependencyId, "Version has multiple property, this is not supported" ))

                              
def process( pomIds, workItems, poms_properties, all_poms_dependencies, all_poms_dependencies_management, bundle, showDependencies, showFeatures, missingParents, quiet, verbose, coloRegExs, updateVersion, root, file, pomFile )  :
    pomId=pomIds[ pomIdToStr(getPomId(pomFile), ver = False) ] 
    parser = etree.XMLParser(strip_cdata=False, recover=True)
    merged_properties=getRecProperties(pomId, pomIds, missingParents, poms_properties)
    merged_properties["project.groupId"]=pomId["groupId"]
    merged_properties["project.version"]=pomId["version"]
    dependencies=getDependencies(pomFile)
    dependenciesManagement=getDependencies(pomFile, dependencyManagement=True)
    featureDependencies=[]
    featureBundle=[]    
    if os.path.isfile(root + "/src/main/resources/features.xml") :
        featureFile = etree.parse(root + "/src/main/resources/features.xml", parser)            
        featureDependencies=getFeatureDependencies(featureFile)
        featureBundle=getFeatureBundle(featureFile)
    pomIdPrinted=False
    headerPrinted=False
    if quiet :
        header=root + " " + pomIdToStr(pomId, ver = True)
    else :
        header=root + " : " + pomIdToStr(pomId, ver = True)
    
    if showDependencies : 
        for l in dependencies :
            if fnmatch(  pomIdToStr(l,  prop = merged_properties ), bundle ) :
                if not headerPrinted :
                    if not pomIdPrinted :
                        if not quiet :
                            print ( header )
                        pomIdPrinted=True
                    if not quiet :
                        print ('  Dependencies')
                    headerPrinted=True
                if updateVersion is not None :
                    check_dependency_workitem( "D",   all_poms_dependencies, all_poms_dependencies_management, pomId, l, pomIds, poms_properties, workItems, updateVersion )
                if not quiet :       
                    print ( "    " + dependencyPomIdToStrVerboseColor(pomId, l, pomIds, missingParents, poms_properties, all_poms_dependencies, all_poms_dependencies_management, merged_properties, quiet, coloRegExs ) )
                else :
                    print ( header+"\tDependencies\t" + dependencyPomIdToStrVerboseColor(pomId, l, pomIds, missingParents, poms_properties, all_poms_dependencies, all_poms_dependencies_management, merged_properties, quiet, coloRegExs ) )
        headerPrinted=False
        for l in dependenciesManagement :
            if fnmatch(  pomIdToStr(l), bundle ) :
                if not headerPrinted :
                    if not pomIdPrinted :
                        if not quiet :
                            print ( header )
                        pomIdPrinted=True
                    if not quiet :
                        print ('  DependenciesManagement')
                    headerPrinted=True
                if not quiet :                
                    print ( "    " + dependencyPomIdToStrVerboseColor(pomId, l, pomIds, missingParents, poms_properties, all_poms_dependencies, all_poms_dependencies_management, merged_properties, quiet, coloRegExs ) )
                else :
                    print ( header+"\tDependenciesManagement\t" + dependencyPomIdToStrVerboseColor(pomId, l, pomIds, missingParents, poms_properties, all_poms_dependencies, all_poms_dependencies_management, merged_properties, quiet, coloRegExs ) )
                if updateVersion is not None :
                    check_dependency_workitem( "DL",  all_poms_dependencies, all_poms_dependencies_management, pomId, l, pomIds, poms_properties, workItems, updateVersion )
        headerPrinted=False
    if showFeatures :             
        for l in featureDependencies :
            if fnmatch(  pomIdToStr(l,  prop = merged_properties ), bundle ) :
                if not headerPrinted :
                    if not pomIdPrinted :
                        if not quiet :
                            print ( header )
                        pomIdPrinted=True
                    if not quiet :                    
                        print ('  FeatureDependencies')
                    headerPrinted=True
                if updateVersion is not None :
                    check_features_workitem( 'FD', root + "/src/main/resources/features.xml", pomId, l, featureDependencies, pomIds, poms_properties, workItems, updateVersion )
                if not quiet :                
                    print ( "    " + pomIdToStrVerboseColor(l, merged_properties, quiet, coloRegExs ) )
                else :
                    print ( header+"\tFeatureDependencies\t" + pomIdToStrVerboseColor(l, merged_properties, quiet, coloRegExs ) )
        headerPrinted=False
        for l in featureBundle :
            if fnmatch(  pomIdToStr(l,  prop = merged_properties ), bundle ) :
                if not headerPrinted :
                    if not pomIdPrinted :
                        if not quiet :
                            print ( header )
                        pomIdPrinted=True
                    if not quiet :                
                        print ('  FeatureBundle')
                    headerPrinted=True
                if updateVersion is not None :
                    check_features_workitem( 'FB', root + "/src/main/resources/features.xml", pomId, l, featureDependencies, pomIds, poms_properties, workItems, updateVersion )
                if not quiet :                
                    print ( "    " + pomIdToStrVerboseColor(l, merged_properties, quiet, coloRegExs ) )
                else :
                    print ( header+"\tFeatureBundle\t" + pomIdToStrVerboseColor(l, merged_properties, quiet, coloRegExs ) )
    if not pomIdPrinted :
        if fnmatch(  pomIdToStr(pomId ), bundle ) :
            if not quiet :
                print ( header )

if __name__ == "__main__" :
    main()
