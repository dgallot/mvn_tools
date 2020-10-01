#!/usr/bin/python
import os
import sys
import subprocess
import argparse
import gitlab
import gogs_client
import errno
from inspect import getmembers
from pprint import pprint
from common import *
from mygogs import *

def main():
    parser = argparse.ArgumentParser(description = "Create Gogs project")
    parser.add_argument("-u", "--url", help = "Gog url", default=getEnv('GOGS_URL', None), required='GOGS_URL' not in os.environ )
    parser.add_argument("-t", "--token", help = "Gog token", default=getEnv('GOGS_TOKEN', None), required='GOGS_TOKEN' not in os.environ )
    parser.add_argument("-o", "--organization", help = "Organisation name", required = True)
    parser.add_argument("-n", "--name", help = "Repository name", required = True)
    parser.add_argument("-d", "--description", help = "Repository description", required = True)
    options = parser.parse_args() 
    gogs = MyGogsApi(options.url)
    token = gogs_client.Token(options.token)
    try:
        repo = gogs.create_repo(token, options.name, description=options.description, organization=options.organization)
        print ( repo.urls.ssh_url )
    except gogs_client.interface.ApiFailure, e :
        print ( "Error : " + str(e) )
        sys.exit(1)
    except  gogs_client.interface.NetworkFailure, e :
        print ( "Error : " + str(e) )
        sys.exit(1)

if __name__ == "__main__":
    main()
