#!/usr/bin/python
from __future__ import print_function
from common import *
from pom import *
from fnmatch import fnmatch
import re;
from git import Repo
from git.exc import InvalidGitRepositoryError

def usage():
    print ( "mvn_resolve [-v|--ver] [-h|--help] [-s|--sep <sep>] [g|--git] ids_file" )

def find(ids_list, root, pom, sep, ver, gitUrl ) :
    pomId=getPomId(pom)
    mvnId=pomIdToStr(pomId, "/", True)
    if pomIdToStr(pomId, "/", False) in ids_list :
        if gitUrl :
            try :
                repo = Repo(root, search_parent_directories=True)
                print (root + "\t" + pomIdToStr(pomId, sep, ver) + "\t" + repo.git.rev_parse("--show-toplevel") + "\t" + repo.remotes.origin.url)         
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
    ids_list = None    
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
        if os.path.isfile(args[0]) :
            with open(args[0]) as f:
                ids_list = []
                for l in [ x.strip() for x in f.readlines() ] :
                    m=re.match("([^\/]*\/[^\/]*)", l)
                    if m :
                        ids_list.append(m.group())
        else :
            print ( "ids_file : " + args[0] + " not found" )
            usage()
            sys.exit(2)  
    elif len(args) == 0 :
            print ( "ids_file is mandatory" )
            usage()
            sys.exit(2)  
    elif len(args) != 0 :
        print ( "Unkown options : " + str(args) )
        usage()
    forEachPom(  lambda root, file, pom : find( ids_list, root, pom, sep, ver, git ), lambda root, error : None );

if __name__ == "__main__":
    main()    