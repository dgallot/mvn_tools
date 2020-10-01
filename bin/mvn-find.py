#!/usr/bin/python
from __future__ import print_function
from common import *
from pom import *
from fnmatch import fnmatch
import re;
from git import Repo
from git.exc import InvalidGitRepositoryError

def usage():
    print ( "mvn_find [-v|--ver] [-h|--help] [-s|--sep <sep>] [g|--git] <filter>" )

def find(filter, root, pom, sep, ver, gitUrl ) :
    pomId=getPomId(pom)
    mvnId=pomIdToStr(pomId, "/", True)
    if fnmatch( mvnId, filter ) :
        if gitUrl :
            try :
                repo = Repo(root, search_parent_directories=True)
                print (root + "\t" + pomIdToStr(pomId, sep, ver) + "\t" + repo.remotes.origin.url)         
            except InvalidGitRepositoryError:
                print (root + "\t" + pomIdToStr(pomId, sep, ver) + "\t" + "N/A")
        else :
            print (root + "\t" + pomIdToStr(pomId, sep, ver))

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hgs:v", ["help", "git", "sep=", "ver"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print ( str(err) )
        usage()
        sys.exit(2)
    ver = False
    git = False
    sep = "/"
    filter = "*/*"
    for o, a in opts:
        if o in ("-v", "--ver"):
            ver = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-s", "--sep"):
            sep = a
        elif o in ("-g", "--ggit"):
            git = True
        else:
            assert False, "Unhandled option"
    if len(args) == 1 :
        filterArray=map( lambda x: "*" if len(x.strip()) == 0 else x.strip(), re.split('\/|\:',args[0]))
        if len(filterArray) == 3 :            
            filter = "/".join(filterArray)
        elif len(filterArray) == 2 :            
            filter = "/".join(filterArray) + "/*"
        elif len(filterArray) == 1 :
            filter = "/".join(filterArray) + "/*"
        else:
            filter = "*/*/*"
    elif len(args) != 0 :
        print ( "Unkown options : " + str(args) )
        usage()
        sys.exit(2)  
    forEachPom(  lambda root, file, pom : find( filter, root, pom, sep, ver, git ), lambda root, error : None );

if __name__ == "__main__":
    main()    