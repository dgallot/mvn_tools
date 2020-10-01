#!/usr/bin/python
from __future__ import print_function
from common import *
from karaf import *
from dumper import *
from fnmatch import fnmatch
from asciitree import LeftAligned
from asciitree.drawing import BoxStyle, BOX_LIGHT

from collections import OrderedDict as OD
from ordered_set import OrderedSet as OS
import jsonpickle
import functools
import spur
import re

def printFeatureListOfBundle( feature, bundleString ) : 
    # First seache bundle in feature
    bundles=searchBundleVersions(feature, bundleString)        
    features=set()
    for bundle in bundles :      
        featuresOfBundle=searchFeatureOfBundle(feature, bundle)
        features.update(loadParentList( featuresOfBundle ))
    for feature in features : 
        print ( feature )

def printFeatureTreeOfBundle( feature, bundleString ) : 
    # First seache bundle in feature
    bundles=searchBundleVersions(feature, bundleString)    
    root=OD()
    bundlesRoot=OD()
    root['b: ' + bundleString]=bundlesRoot
    if ( len ( bundles ) == 0 ) : 
        bundleRoot=OD()        
        bundlesRoot["Not found"]={}
    else :
        for bundle in bundles :         
            featuresOfBundle=searchFeatureOfBundle(feature, bundle)
            bundleRoot=OD()
            bundlesRoot['b: ' + bundle.toStr(ver=True)]=bundleRoot    
            loadParentTree( bundleRoot, featuresOfBundle )            
    tr = LeftAligned(draw=BoxStyle(gfx=BOX_LIGHT, label_space=0, indent=0))
    print(tr(root))
    

def loadParentList( featuresOfBundle ) :
    result=[]
    for featureOfBundle in featuresOfBundle :    
        result.append(getFeatureLabel( featureOfBundle ))
        result.extend(loadParentList(featureOfBundle.parents ))
    return result

def loadParentTree( root, featuresOfBundle ) :
    for featureOfBundle in featuresOfBundle :    
        childRoot=OD()
        root[ getFeatureLabel( featureOfBundle ) ]=childRoot
        loadParentTree( childRoot, featureOfBundle.parents )

def printFeatureTree( feature, loadDuplicateFeature ) : 
    root=OD()
    loadTree( root, feature, loadDuplicateFeature )
    tr = LeftAligned(draw=BoxStyle(gfx=BOX_LIGHT, label_space=0, indent=0))
    print(tr(root))

def printFeatureList( feature, loadDuplicateFeature ) : 
    features = set()
    bundles = set()
    loadLists( feature, features, bundles )
    headers=[ "Feature : " + feature.name, "" ]
    datas=[]
    for f in features :
        datas.append( [ "Feature", f ] )   
    for b in bundles :
        datas.append( [ "Bundle", b ] )   
    table=format_table(headers, datas, "text")
    print(table)

def searchBundleVersions( feature, bundle, featuresSeen=[], result=[] ) :    
    for featureBundle in feature.bundles :
        if featureBundle.toStr(ver=False) == bundle :
            result.append(featureBundle)
    for subFeature in feature.subFeatures :
        if subFeature not in featuresSeen :
            searchBundleVersions( subFeature, bundle, featuresSeen, result )
            featuresSeen.append(subFeature)
    return result
    
def searchFeatureOfBundle( feature, bundle, featuresSeen=[],  result=[] ) :    
    if bundle in  feature.bundles : 
        result.append(feature)
    for subFeature in feature.subFeatures :
        if subFeature not in featuresSeen :
            searchFeatureOfBundle( subFeature, bundle, featuresSeen, result )
            featuresSeen.append(subFeature)
    return result

def getFeatureLabel(feature) :
    if feature.featureVersion is None :
        fromBundle = None
    else :
        fromBundle=feature.featureVersion.bundle
    if fromBundle is None : 
        return feature.name
    else :
        return feature.name + " : " + fromBundle.toStr(ver=True)
    
def loadTree( node, feature, loadDuplicateFeature, printed=[] ) :
    if loadDuplicateFeature or ( feature.name not in printed ) :
        prefix = 'f: '
    else :
        prefix = 'F: '
    label=prefix + getFeatureLabel(feature)
    childs=OD()
    if loadDuplicateFeature or ( feature.name not in printed ) :
        for subFeature in feature.subFeatures :
            print ( subFeature.name )
            if subFeature.name != feature.name :
                loadTree( childs, subFeature, loadDuplicateFeature, printed )
        for bundle in feature.bundles :
            childs["b: " + bundle.toStr(ver=True)]={}
        printed.append(feature.name)
    else :
        childs["..."]={}
    node[label]=OD(childs)

def loadLists( feature, features, bundles ) :
    features.add(getFeatureLabel(feature))
    for subFeature in feature.subFeatures :
        loadLists( subFeature, features, bundles )
    for bundle in feature.bundles :
        bundles.add(  bundle.toStr(ver=True) )
    
def usage():
    print ( "remote-expand-features.py [-f|--feature] [-H|--hostname <hostname>] [-i|--instance <instance>] [ -m|--mode tree|list>] [-s|save <file>] [-l|load <file>] [b|bundle <bundleid>] [-d|show-duplicate]" )
    print ( "Connect to a remote karaf and expand the feature")

def main():
    showDuplicate=False
    load=None
    save=None
    instance=None
    hostname=None
    features="all"
    bundle=None
    mode="tree"
    quiet=False
    try:    
        opts, args = getopt.getopt(sys.argv[1:], "qhH:m:i:f:l:s:b:d", ["help", "quiet", "hostname=", "instance=", "mode=[tree,list]", "features=<all|installed|name[,name...]>", "load=", "safe=", "bundle=", "show-duplicate"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print ( str(err) )
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-l", "--load"):
            load = a
        elif o in ("-s", "--save"):
            save = a
        elif o in ("-H", "--hostname"):
            hostname = a
        elif o in ("-i", "--instance"):
            instance = a
        elif o in ("-f", "--features"):
            features = a
        elif o in ("-m", "--mode"):
            mode = a
        elif o in ("-d", "--show-duplicate"):
            showDuplicate = True
        elif o in ("-q", "--quiet"):
            quiet = True
        elif o in ("-b", "--bundle"):
            bundle = a
        else:
            assert False, "Unhandled option " + o
    if mode != "tree" :
        if mode != "list" :
            print ( "Invalid option, mode can be list or tree" )
            usage()        
            sys.exit(2)
    
    if load is  None :
        if instance is None :
            print( "Instance is required")
            usage()
            sys.exit(2)        
        if hostname is None :
            print( "Hostname is required")
            usage()    
            sys.exit(2)        
    if save is not None and load is not None :
        print( "Save and Load cannot be set together")
        usage()    
        sys.exit(2)        
    
    if load is not None :
        if not quiet : 
            print ( "Loading " + load )
        datas=jsonpickle.decode(open(load, 'r').read())
    else :
        if not quiet :
            print ( "Connecting to " + instance + "@" + hostname ) 
        ssh=Ssh(hostname=hostname, instance=instance)        
        karaf=Karaf(ssh)
        if not quiet : 
            print ( "Connected to " + instance + "/" + karaf.version + "@" + ssh.hostname  )

        featureTree=FeatureTree(karaf)
        allFeaturesList=featureTree.allFeatures()
        installedFeaturesList=featureTree.installedFeatures()
        featuresLoadedData=OD()
        if features is None :
            featuresLoadedList=allFeaturesList
        elif features == "all" :
            featuresLoadedList=allFeaturesList
        elif features == "installed" :            
            featuresLoadedList=installedFeaturesList
        else :
            featuresLoadedList=[]
            featuresLoadedList.extend(features.split(','))        
        if not quiet :
            print ( "Loading the features '"+features+"'" )
        for featuresLoaded in featuresLoadedList :
            f=featureTree.info(featuresLoaded)
            moveUp()
            featureTree.versions(f)
            featuresLoadedData[featuresLoaded]=f
        datas={"allFeaturesList": allFeaturesList, "installedFeaturesList": installedFeaturesList, "featuresLoadedData": featuresLoadedData }
        if save is not None :            
            if not quiet :
                print ( "Saving " + save )
            open(save, 'w').write(jsonpickle.encode(datas))
    
    allFeaturesList=datas["allFeaturesList"]
    installedFeaturesList=datas["installedFeaturesList"]
    featuresLoadedData=datas["featuresLoadedData"]
    feature2Print=[]
    if features is None :
        features2Print=allFeaturesList
    elif features == "all" :
        features2Print=allFeaturesList
    elif features == "installed" :            
        features2Print=installedFeaturesList
    else :
        features2Print=[]
        for feature in features.split(',') :
            if feature in featuresLoadedData.keys() :
                features2Print.append(feature)        
            else :
                if load is not None :
                    print("Feature '"+feature+"' not found in file " + load )
                else:
                    print("Feature '"+feature+"' not found on server " )
    
    for feature2Print in features2Print :
        featureLoadedData=featuresLoadedData[feature2Print]
        if bundle is not None :
            bundles=searchBundleVersions(featureLoadedData, bundle)    
            if ( len ( bundles ) != 0 ) : 
                if mode == "tree" :
                    if not quiet : 
                        print("Feature " + feature2Print)
                    printFeatureTreeOfBundle(featureLoadedData, bundle )
                else :
                    if not quiet : 
                        print("Feature " + feature2Print)
                    printFeatureListOfBundle(featureLoadedData, bundle )
        else :
            if mode == "tree" :
                if not quiet : 
                    print("Feature " + feature2Print)
                printFeatureTree(featureLoadedData, showDuplicate)    
            else :
                print( " ")
                printFeatureList(featureLoadedData, bundle )

if __name__ == "__main__" :
    reload(sys)
    sys.setdefaultencoding('utf-8')    
    main()
