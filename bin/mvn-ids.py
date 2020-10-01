#!/usr/bin/python
from __future__ import print_function
from common import *
from pom import *
import getopt, sys

def usage():
    print ( "mvn_id [-h|--help] [-g|--git] [-s|--sep <sep>] [-b|--branch] [-n|--nover] [-p|--parent]" )

def print_mvn(root, file, pom, ver, branch, sep, gitUrl, parent) :
    print( root, end='' )
    print( " ", pomIdToStr(getPomId(pom), sep, ver), end='' )
    if gitUrl :
        print( " " + getGitUrl(root), end='' )
    if branch :
        print( " " + getGitBranch(root), end='' )
    if parent :
        print( " " + parentPomIdToStr(getPomId(pom), sep, ver), end='' )
    print()
    
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hgs:nbp", ["help", "git", "sep=", "nover", "branch", "parent"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print ( str(err) )
        usage()
        sys.exit(2)
    ver = True
    parent = False
    branch = False
    sep = "/"
    gitUrl = False 
    for o, a in opts:
        if o in ( "-n", "--nover" ):
            ver = False
        elif o in ( "-p", "--parent" ):
            parent = True
        elif o in ( "-b", "--branch" ):
            branch = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-s", "--sep"):
            sep = a
        elif o in ("-g", "--git"):
            gitUrl = True
        else:
            assert False, "Unhandled option"
    
    forEachPom   ( lambda root, file, pom : print_mvn(root, file, pom, ver, branch, sep, gitUrl, parent), lambda root, error : print(root + "\t Error : " + error ) )

if __name__ == "__main__":
    main()


