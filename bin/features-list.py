#!/usr/bin/python

from __future__ import print_function
from common import *
import functools
import sys
from fnmatch import fnmatch, translate
from pom import *
from pprint import *
import os.path

class UnknownVersionWorkItem :
    mvn_id = None
    def __init__(self, mvn_id, err) :
        self.mvn_id=mvn_id
        seld.err = err
    def __str__(self) :
        return "Unable to deduce version of %s. %s." % ( mvn_id, err )
    
    def update() :
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

    def update() :
        set_property( pom_file, property_name, property_value )
    
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

    def __str__(self) :
        return "File: %s. Set property ${%s} from %s to %s" % ( self.ownerPomId["file"], self.property_name, self.current_property_value, self.new_property_value )
    
    def update() :
        set_property( pom_file, property_name, property_value )

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

class FeatureWorkItem :
    ownerPomId = None
    feature = None
    groupId = None
    artifactId = None
    current_version = None
    new_version = None
    file = None
    
    def __init__(self, ownerPomId, feature, groupId, artifactId, current_version, new_version) :
        self.ownerPomId=ownerPomId
        self.feature=feature
        self.groupId=groupId
        self.artifactId=artifactId
        self.current_version=current_version
        self.new_version=new_version
        print ( self )
    
    def __str__(self) :
        return "File: %s. Set feature %feature %s/%s %s => %s " % ( self.ownerPomId["file"], self.feature, self.groupId, self.artifactId, self.current_version, self.new_version )
    
    def update() :
        set_dependency( pom_file, artifactId, groupId, version )        

def error(root, error) :
    print("Error : " + root + " - " + error )
    
def usage():
    print ( "mvn_version_tools [-b|--bundle <bundleid> -u|--update] [--no-color] [v|--verbose] [-f|--features] [-d|--dependencies] " )

def main():
    bundle="*/*"
    showDependencies=False
    showFeatures=False
    color=True
    verbose=False
    poms_properties={}
    pomIds={}
    updateVersion=None
    short=False
    workItems= []
    quiet=False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hb:fdvu:q", ["help", "bundle=", "dependencies", "features", "verbose", "no-color", "update=", "quiet"])
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
        elif o in ("-b", "--bundle"):
            bundle=a
        elif o in ("-q", "--quiet"):
            quiet=True
        elif o in ("--no-color"):
            color=False
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
    missingParents=set()
    forEachPom(functools.partial(load_properties, pomIds, poms_properties ), error )
    forEachPom(functools.partial(process, pomIds, workItems, poms_properties, bundle, showDependencies, showFeatures, missingParents, quiet, verbose, color, updateVersion), error  )
    c=0
    if updateVersion is not None :
        if len( workItems ) != 0 :
            print ( "Changes" )
            for workItems in workItems :                
                print ( "  %i : %s " % ( c , workItems ) )
                c=c+1

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
            result=merge_two_dicts( result, getRecProperties( pomIds[parentId], pomIds, missingParents, poms_properties) )
        else :
            missingParents.add(parentId)
    return result
    
def load_properties( pomIds, poms_properties, root, file, pomFile ) :
    pomId=getPomId(pomFile)
    pomId["file"]=os.path.join(root, file)
    pomIds[ pomIdToStr(pomId, ver = False) ] = pomId
    poms_properties[ pomIdToStr(pomId, ver = False) ] = getProperties(pomFile)

def pomIdToStrVerboseColor(pomId, properties, quiet, color, coloRegEx) :
    sep='/'
    bundleId=expand_properties(pomId["groupId"], properties ) + sep + expand_properties(pomId["artifactId"],properties)
    if color :
        result=hightlight(bundleId, coloRegEx)
    else :
        result=bundleId
    rawVersion=pomId["version"]
    expandedVersion=expand_properties(pomId["version"],properties)
    if rawVersion == expandedVersion :
        return result + sep + rawVersion
    else:
        if quiet :
            return result + sep + expandedVersion
        else :
            return result + sep + rawVersion + " -> " + result + sep + expandedVersion


def check_dependency_workitem( dtype, pomId, dependencyId, pomIds, pom_merged_properties, poms_properties, workItems, updateVersion )  :
    bundleId=expand_properties(dependencyId["groupId"], pom_merged_properties ) + '/' + expand_properties(dependencyId["artifactId"],pom_merged_properties)
    version=expand_properties(dependencyId["version"], pom_merged_properties)    
    if not pomId["version"] == version :
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
                        workItems.append( PropertyWorkItem( propertyPomid, properties_name[0], pom_merged_properties[properties_name[0]], updateVersion ))
                else :
                    workItems.append( UnknownPropertyWorkItem( pomId, properties_name[0], missingParents[0] ))
            else :
                workItems.append( UnknownVersionWorkItem( dtype, pomId, dependencyId, "Version has multiple property, this is not supported" ))

                              
def process( pomIds, workItems, poms_properties, bundle, showDependencies, showFeatures, missingParents, quiet, verbose, color, updateVersion, root, file, pomFile )  :
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
    if showDependencies : 
        for l in dependencies :
            if fnmatch(  pomIdToStr(l,  prop = merged_properties ), bundle ) :
                if not headerPrinted :
                    if not pomIdPrinted :
                        if not quiet :
                            print ( root + " : " + pomIdToStr(pomId, ver = True) )                    
                        pomIdPrinted=True
                    if not quiet :
                        print ('  Dependencies')
                    headerPrinted=True
                if updateVersion is not None :
                    check_dependency_workitem( "D", pomId, l, pomIds, merged_properties, poms_properties, workItems, updateVersion )
                if not quiet :                
                    print ( "    " + pomIdToStrVerboseColor(l, merged_properties, quiet, color, translate(bundle) ) )
                else :
                    print ( "Dependencies : " + pomIdToStrVerboseColor(l, merged_properties, quiet, color, translate(bundle) ) )
        headerPrinted=False
        for l in dependenciesManagement :
            if fnmatch(  pomIdToStr(l), bundle ) :
                if not headerPrinted :
                    if not pomIdPrinted :
                        if not quiet :
                            print ( root + " : " + pomIdToStr(pomId, ver = True) )                    
                        pomIdPrinted=True
                    if not quiet :
                        print ('  DependenciesManagement')
                    headerPrinted=True
                if not quiet :                
                    print ( "    " + pomIdToStrVerboseColor(l, merged_properties, quiet, color, translate(bundle) ) )
                else :
                    print ( "DependenciesManagement : " + pomIdToStrVerboseColor(l, merged_properties, quiet, color, translate(bundle) ) )
                if updateVersion is not None :
                    check_dependency_workitem( "DM", pomId, l, pomIds, merged_properties, poms_properties, workItems, updateVersion )
        headerPrinted=False
    if showFeatures :             
        for l in featureDependencies :
            if fnmatch(  pomIdToStr(l,  prop = merged_properties ), bundle ) :
                if not headerPrinted :
                    if not pomIdPrinted :
                        if not quiet :
                            print ( root + " : " + pomIdToStr(pomId, ver = True) )                    
                        pomIdPrinted=True
                    if not quiet :                    
                        print ('  FeatureDependencies')
                    headerPrinted=True
                if not quiet :                
                    print ( "    " + pomIdToStrVerboseColor(l, merged_properties, quiet, color, translate(bundle) ) )
                else :
                    print ( "FeatureDependencies : " + pomIdToStrVerboseColor(l, merged_properties, quiet, color, translate(bundle) ) )
        headerPrinted=False
        for l in featureBundle :
            if fnmatch(  pomIdToStr(l,  prop = merged_properties ), bundle ) :
                if not headerPrinted :
                    if not pomIdPrinted :
                        if not quiet :
                            print ( root + " : " + pomIdToStr(pomId, ver = True) )                    
                        pomIdPrinted=True
                    if not quiet :                
                        print ('  FeatureBundle')
                    headerPrinted=True
                if not quiet :                
                    print ( "    " + pomIdToStrVerboseColor(l, merged_properties, quiet, color, translate(bundle) ) )
                else :
                    print ( "FeatureBundle : " + pomIdToStrVerboseColor(l, merged_properties, quiet, color, translate(bundle) ) )
    if not pomIdPrinted :
        if fnmatch(  pomIdToStr(pomId ), bundle ) :
            print ( root + " : " + pomIdToStrVerboseColor(pomId, {}, verbose, color, translate(bundle) ) )                    

if __name__ == "__main__" :
    main()
