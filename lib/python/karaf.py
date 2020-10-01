#!/usr/bin/python
from array import array
from lxml import etree
import glob, os, sys, getopt
from shutil import copyfile
import sys, paramiko
from common import *
from pprint  import *
from dumper import *
import functools
import sys
import spur
import re
from curses import *

def nothing(*args):
    pass

class Import :
    package = None
    version = None
    def __init__(self, package, version ) :
        self.package=package
        self.version=version
        
class Export :
    package = None
    version = None
    def __init__(self, package, version ) :
        self.package=package
        self.version=version        

class FeatureLocation :
    version = None
    repository = None
    repositoryUrl = None;
    bundle = None;
    def __init__(self, version, repository, repositoryUrl, bundle) :
        self.version=version
        self.repository=repository
        self.repositoryUrl=repositoryUrl
        self.bundle=bundle
        
    
class RouteInfo:
    name=None;
    definition=None
    statistics=None
    def __init__(self, name) :
        self.name=name;
        self.definition=""
        self.statistics={}
        
class Route:
    name = None
    context = None
    status = None
    def __init__(self, name, context, status ) :
        self.name = name;
        self.context = context
        self.status = status

class Bundle:
    id = None
    parent = None
    groupId = None
    artifactId = None
    version = None
    def __init__(self, parent, id, groupId, artifactId, version ) :
        self.id = id;
        self.parent = parent
        self.groupId = groupId
        self.artifactId = artifactId
        self.version = version
    def toStr(self, ver=False, sep="/") :
        if ver :
            return self.groupId + sep + self.artifactId + sep + self.version;
        else :
            return self.groupId + sep + self.artifactId;

class Karaf:
    ssh=None
    version=None
    is24=None
    is40=None
    def __init__(self, ssh) :
        self.ssh=ssh
        self.version=self.run("version").strip()
        self.is24=False
        self.is40=False
        if self.version.startswith("2.4") :
            self.is24=True
        elif self.version.startswith("4.0") :
            self.is40=True
        else :
            print ("Unexpected version " + self.version )
    def run(self, command) :        
        return self.ssh.run(command)

class Feature:
    name=None
    subFeatures=None
    bundles=None
    featureVersion=None
    parents=None
    def __init__(self, name, version) :
        self.name = name
        self.subFeatures = []
        self.bundles = []
        self.featureVersion=None
        self.parents = []
        

class CamelRoute:
    routesByName=None
    karaf=None
    def __init__(self, karaf):
        self.routesByName = {}
        self.karaf=karaf

    def list(self) :
        if self.karaf.is24 :
            output = self.karaf.run("camel:route-list")
            for line in output.splitlines() :
                self.parseRouteList24(line.strip())
            return self.routesByName
        if self.karaf.is40 :
            output = self.karaf.run("camel:route-list")
            for line in output.splitlines() :
                self.parseRouteList40(line.strip())
            return self.routesByName
        else :            
            raise EnvironmentError("Version "+self.karaf.version+" not supported ")

    def info(self, name) :
        routeInfo=RouteInfo(name);
        if self.karaf.is24 :
            output = self.karaf.run("camel:route-info " + name)
            self.parseRouteInfo24(routeInfo, output)
            return routeInfo
        if self.karaf.is40 :
            output_info = self.karaf.run("camel:route-info " + name)
            output_show = self.karaf.run("camel:route-show " + name)
            self.parseRouteInfo40(routeInfo, output_info, output_show)
            return routeInfo
        else :            
            raise EnvironmentError("Version "+self.karaf.version+" not supported ")      
            
    def parseRouteInfo24( self, routeInfo, output ) :             
        state="NONE"
        headers = { 
            ".*Properties" : "PROPERTIES",
            ".*Statistics" : "STATISTICS",
            ".*Definition" : "DEFINITION_HEADER"
        }    
        states = {
            "NONE" : nothing,
            "PROPERTIES" : nothing,
            "STATISTICS" : self.readRouteStatistics,
            "DEFINITION_HEADER" : functools.partial(self.nextState, "DEFINITION"),
            "DEFINITION" : self.readDefinition,
        }        
        for line in output.splitlines():
            for regex, new_state in headers.iteritems():
                if re.match( regex, line ) :
                    state=new_state
            new_state=states[state](state, line, routeInfo)
            if new_state is not None :
                state=new_state

    def parseRouteInfo40( self, routeInfo, output_info, output_show ) :             
        state="NONE"
        headers = { 
            ".*Statistics" : "STATISTICS",
        }    
        states = {
            "NONE" : nothing,
            "STATISTICS" : self.readRouteStatistics,
        }        
        for line in output_info.splitlines():
            for regex, new_state in headers.iteritems():
                if re.match( regex, line ) :
                    state=new_state
            new_state=states[state](state, line, routeInfo)
            if new_state is not None :
                state=new_state     
        routeInfo.definition = output_show

    def nextState( self, nextState, state, line, routeInfo ) :
        return nextState                
    def readDefinition( self, state, line, routeInfo ) :
        routeInfo.definition = routeInfo.definition + line + "\n"        
    def readRouteStatistics(self, state, line, routeInfo):
        nv=line.strip().split(":")
        if len(nv) >= 2 :
            name=nv[0].strip()
            value=nv[1].strip()
            routeInfo.statistics[name]=value           
            
    def parseRouteList24( self, line ) :
        entry = line.split()
        name=entry[1].strip()
        context=entry[0].strip()
        status=entry[2].strip()
        if name != 'Route' :
             if name != '-----' :
                 route=Route(name, context, status)
                 self.routesByName[name]=route
    
    def parseRouteList40( self, line ) :
        entry = line.split()
        name=entry[1].strip()
        context=entry[0].strip()
        status=entry[2].strip()
        route=Route(name, context, status)
        self.routesByName[name]=route        

class BundleList :
    def __init__(self, karaf):
        self.karaf=karaf
        self.bundlesById = {}
        self.featuresUrlByUrl = {}
        
    def features_list_url(self) :
        if self.karaf.is24 :
            output = self.karaf.run("features:listurl")
            for line in output.splitlines() :
                self.parseFeaturesListUrl24(line.strip())
            return self.featuresUrlByUrl
        else :
            if self.karaf.is40 :
                output = self.karaf.run("feature:repo-list")
                for line in output.splitlines() :
                    self.parseFeaturesListUrl40(line.strip())
                return self.featuresUrlByUrl
            else :
                raise EnvironmentError("Version "+self.karaf.version+" not supported ")
        
    def list(self) :
        if self.karaf.is24 :
            output = self.karaf.run("list -l")
            for line in output.splitlines() :
                self.parseBundle24(line.strip())
        else :
            if self.karaf.is40 :
                output = self.karaf.run("list -l --no-format")
                for line in output.splitlines() :
                    self.parseBundle40(line.strip())
            else :
                raise EnvironmentError("Version "+self.karaf.version+" not supported ")
        return self.bundlesById
    
    def imports(self, id) :
        result=[]
        if self.karaf.is24 :
            output = self.karaf.run("imports " + str(id) ) 
            for line in output.splitlines() :
                imp=self.parseImport24(line.strip(), line)
                if imp is not None :
                    result.append( imp )
            return result
        elif self.karaf.is40 :
            output = self.karaf.run("imports -b " + str(id))
            for line in output.splitlines() :
                imp=self.parseImport40(line.strip())
                if imp is not None :
                    result.append( imp )
            return result
        else :
            raise EnvironmentError("Version "+self.karaf.version+" not supported ")

    def exports(self, id) :
        result=[]
        if self.karaf.is24 :
            output = self.karaf.run("exports " + str(id) ) 
            for line in output.splitlines() :
                exp=self.parseExport24(line.strip(), line)
                if exp is not None :
                    result.append( exp )
            return result
        elif self.karaf.is40 :
            output = self.karaf.run("exports -b " + str(id))
            for line in output.splitlines() :
                exp=self.parseExport40(line.strip())
                if exp is not None :
                    result.append( exp )
            return result
        else :
            raise EnvironmentError("Version "+self.karaf.version+" not supported ")
            
    def parseFeaturesListUrl24( self, line ):
        m=re.match("(.*)mvn\:(.+)\/(.+?)\/(.+?)/xml/features", line)
        if m :
            bundle=Bundle(None,line.split()[1],m.group(2),m.group(3),m.group(4))
            self.featuresUrlByUrl[line.split()[1]]=bundle
    
    def parseFeaturesListUrl40( self, line, result ):
        m=re.match("(.*)mvn\:(.+)\/(.+?)\/(.+?)/xml/features", line)
        if m :
            bundle=Bundle(None,line.split()[2],m.group(2),m.group(3),m.group(4))
            self.featuresUrlByUrl[line.split()[2]]=bundle

    def parseImport24(self, line, result):
        m=re.match("(.*)\((\d+)\)\:(.+)\; version\=\"?([^\"]+)\"?$", line)
        if m :
            return Import(m.group(3),m.group(4))
        else :
            print ("+++++++++++++++++++----------------++++++++++++++++++"  + line )
        return None

    def parseImport40(self, line ):
        m=re.match("^\s*(.*?)\s*\|(.*)\|(.*)\|\s*(\d*)\s*\|(.*)$", line)
        if m :
            p=m.group(3)
            v=m.group(4)
            m=re.match("\s*\[([^\,]*).*", v)
            if m :
                v=m.group(1)
            return Import(p,v)
        else :
            print ("+++++++++++++++++++----------------++++++++++++++++++"  + line )
        return None

    def parseExport24(self, line, result):
        m=re.match("^\s*(\d)+[\s]*([^\s\;]*).*version=(.*)$", line)
        if m :
            return Export(m.group(2),m.group(3))
        return None

    def parseExport40(self, line ):
        m=re.match("^([^\s]+)[^\|]*\|\s+([^\s]+)[^\|]*\|(.*)$", line)
        if m :
            return Export(m.group(1),m.group(2))
        return None


    def parseBundle24(self, line):
        m=re.match("\[(.*?)\](.*)mvn\:(.+)\/(.+?)\/(.+?)[\/]?$", line)
        if m :
            bundle=Bundle(None,m.group(1),m.group(3),m.group(4), m.group(5))
            self.bundlesById[m.group(1)]=bundle
    
    def parseBundle40(self, line):
        m=re.match("(.*?)\s(.*)mvn\:(.+)\/(.+?)\/(.+?)[\/]?$", line)
        if m :
            bundle=Bundle(None,m.group(1),m.group(3),m.group(4), m.group(5))
            self.bundlesById[m.group(1)]=bundle

class FeatureTree :
    def __init__(self, karaf):
        self.karaf=karaf
        self.featuresByName = {} 
        self.featuresVersionsByName = {} 
        self.bundleByMvnId = {}    
    
    def installedFeatures(self) :
        result=[]
        if self.karaf.is24 :        
            output = self.karaf.run("features:list -i")
            for line in output.splitlines() :
                f=self.parseList24(line.strip())            
                if f is not None :
                    if f != 'Name' :
                        result.append(f)
        elif self.karaf.is40 :
            output = self.karaf.run("feature:list -i")
            for line in output.splitlines() :
                f=self.parseList40(line.strip())            
                if f is not None :
                    if f != 'Name' :
                        result.append(f)
        else :
            raise EnvironmentError("Version "+self.karaf.version+" not supported ")            
        return result

    def allFeatures(self) :
        result=[]
        if self.karaf.is24 :        
            output = self.karaf.run("features:list")
            for line in output.splitlines() :
                f=self.parseList24(line.strip())            
                if f is not None :
                    if f != 'Name' :
                        result.append(f)
        elif self.karaf.is40 :
            output = self.karaf.run("feature:list")
            for line in output.splitlines() :
                f=self.parseList40(line.strip())            
                if f is not None :
                    if f != 'Name' :
                        result.append(f)
        else :
            raise EnvironmentError("Version "+self.karaf.version+" not supported ")            
        return result

    def parseList24(self, line):
        m=re.match("\[(.*?)\s*\]\s*\[(.*?)\s*\]\s+(\S*)\s+(.*)", line)
        if m :
            return m.group(3)
    
    def parseList40(self, line):
        m=re.match("(.*?)\s+|(.*)?$", line)
        if m :
            return m.group(1)
        
    def getCachedFeatureByName(self, featureName, featureVersion = None):
        # Todo Handle version
        return self.featuresByName[featureName][self.featuresByName[featureName].keys()[0]]
    
    def info(self, featureName, level = 0, version = None) :
        if featureName in self.featuresByName :
            if level != 0 :        
                moveUp()
            print("Loading information for feature : " + (level*' ')+ featureName + " [cached]")
            return self.getCachedFeatureByName(featureName, version)
        else :
            if level != 0 :        
                moveUp()
            print("Loading information for : " + (level*' ')+ featureName)
        
        current=Feature(featureName, version); 
        if self.karaf.is24 :        
            if version is None :
                cmd = "features:info " + featureName
            else :
                cmd = "features:info " + featureName + " " + version
        elif self.karaf.is40 :
            if version is None :
                cmd = "feature:info " + featureName
            else :
                cmd = "feature:info " + featureName + " " + version
        else :
            raise EnvironmentError("Version "+self.karaf.version+" not supported ")            
        output=self.karaf.run(cmd)
        next_state=lambda state, line : state + 1 
        state="NONE"
        headers = { 
            "Feature not found" : "NOT_FOUND",
            "Feature "+re.escape(featureName)+" .*" : "DESCRIPTION_40",
            "Description of .* feature" : "DESCRIPTION_24",
            "Feature depends on" : "FEATURE_TITLE",
            "Feature has no dependencies" : "FEATURE_TITLE",
            "Feature.*bundles.*" : "BUNDLE_TITLE",
            "Feature.*conditionals.*" : "OTHER_TITLE"        
        }    
        states = {
            "NOT_FOUND" : self.not_found,
            "NONE" : self.nothing,
            "DESCRIPTION_24" : functools.partial(self.parseDescription24, featureName, current, level),
            "DESCRIPTION_40" : functools.partial(self.parseDescription40, featureName, current, level),
            "FEATURE_TITLE" : functools.partial(self.nextState, "FEATURE"),
            "FEATURE" : functools.partial(self.parseFeature,  current, level),
            "BUNDLE_TITLE" : functools.partial(self.nextState, "BUNDLE"),
            "BUNDLE" : functools.partial(self.parseBundle, current, level),
            "OTHER_TITLE" : self.nothing,  
        }
        for line in output.splitlines():
            for regex, new_state in headers.iteritems():
                if re.match( regex, line ) :
                    state=new_state
            new_state=states[state](state, line)
            if new_state is not None :
                state=new_state
        return current
    
    def versions(self, feature, level = 0) :
        if feature.featureVersion is None :
            if level != 0 :
                moveUp()
            print ("Loading version information for "+(level*' ')+ feature.name)
            if feature.name not in self.featuresVersionsByName :
                versions=self.listVersions(feature.name)
                if ( len( versions ) == 0 ) :
                    print ("Feature not found : "+(level*' ')+ feature.name)
                    return feature
                self.featuresVersionsByName[feature.name]=versions
            feature.featureVersion=self.featuresVersionsByName[feature.name][0];
            for subFeature in feature.subFeatures :
                self.versions(subFeature, level + 1)
        return feature
    
    def not_found(*args):
        print ("Feature not found")
    
    def nothing(*args):
        pass
    
    def parseDescription24(self, featureName, current, level, state, line):
        m=re.match("Description of "+re.escape(featureName)+" (.*) feature", line)
        current.version=m.group(1)
        if not current.name in self.featuresByName :
            self.featuresByName[current.name]={}
        self.featuresByName[current.name][current.version]=current
        return "NONE"
    
    def parseDescription40(self, featureName, current, level, state, line):
        m=re.match("Feature "+re.escape(featureName)+"\s+(.*)", line)
        current.version=m.group(1)
        if not current.name in self.featuresByName :
            self.featuresByName[current.name]={}
        self.featuresByName[current.name][current.version]=current
        return "NONE"
     
    def parseFeature(self, current, level, state, line):
        words=line.split()
        featureName=words[0]
        version=words[1]    
        if version == "0.0.0" or "[" in version :
            version = None
        if not featureName in self.featuresByName :
            feature=self.info(featureName, level + 1, version )
        else :
            feature=self.getCachedFeatureByName(featureName, version)
        if current not in feature.parents :
            feature.parents.append(current)
        current.subFeatures.append(feature)
    
    def parseBundle(self, current, level, state, line):
        words=line.split()
        mvn_id=words[0]
        m=re.match("mvn\:(.*)\/(.*)\/(.*)", mvn_id)
        if m :
            bundle=Bundle(current, None, m.group(1),m.group(2),m.group(3))
            id=m.group(1) + "/" + m.group(2)
            if not id in self.bundleByMvnId :
                self.bundleByMvnId[id]=[]
            self.bundleByMvnId[id].append(bundle)
            current.bundles.append(bundle)
#        else :    
#            print ("-:" + (" " * level ) + mvn_id)
    
    def nextState(self, nextState, state, line ):
        return nextState        
    
    def listVersions(self, name) :
        versions=[]
        if self.karaf.is24 : 
            output = self.karaf.run("features:listversions " + name)
            for line in output.splitlines() :
                featureLocation=self.parseFeatureVersion24(line.strip())
                if featureLocation is not None :
                    versions.append(featureLocation)
        elif self.karaf.is40 :                    
            output = self.karaf.run("feature:version-list " + name)
            for line in output.splitlines() :
                featureLocation=self.parseFeatureVersion40(line.strip())
                if featureLocation is not None :
                    versions.append(featureLocation)
        else :            
            raise EnvironmentError("Version "+self.karaf.version+" not supported ")
        if len( versions ) == 0 :            
            versions.append(FeatureLocation( "No Version found", "N/A", "N/A", None ))                            
        return versions
    
    def parseFeatureVersion24( self, line ):
        m=re.match("\[(.*)\](.*)(mvn\:(.+)\/(.+?)\/(.+?)/xml/features)", line)
        if m :
            version=m.group(1)
            repository=m.group(2)
            repositoryUrl=m.group(3)
            id = m.group(4)+"/"+m.group(5)+"/"+m.group(6)
            bundle=Bundle(None,id,m.group(4),m.group(5),m.group(6))
            featureLocation=FeatureLocation(version, repository, repositoryUrl, bundle) 
            return featureLocation

    def parseFeatureVersion40( self, line ):
        m=re.match("(.*)\|(.*)\|.*(mvn\:(.+)\/(.+?)\/(.+?)/xml/features)", line)
        if m :
            version=m.group(1)
            repository=m.group(2)
            repositoryUrl=m.group(3)
            id = m.group(4)+"/"+m.group(5)+"/"+m.group(6)
            bundle=Bundle(None,id,m.group(4),m.group(5),m.group(6))
            featureLocation=FeatureLocation(version, repository, repositoryUrl, bundle) 
            return featureLocation
            

            
setupterm()



