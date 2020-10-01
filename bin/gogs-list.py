#!/usr/bin/python
import os
import sys
import urlparse
import subprocess
import argparse
import giturlparse 
from mygogs import *
import gogs_client
import errno
from inspect import getmembers
from pprint import pprint
from common import *
from mygogs import *
from fnmatch import fnmatch

def main():
    parser = argparse.ArgumentParser(description = "List gogs projects")
    parser.add_argument("-u", "--url", help = "Gogs url", default=getEnv('GOGS_URL', None), required='GOGS_URL' not in os.environ )
    parser.add_argument("-t", "--token", help = "Gog token", default=getEnv('GOGS_TOKEN', None), required='GOGS_TOKEN' not in os.environ )
    parser.add_argument("-o", "--organization", help = "Organisation filter", required = False)
    parser.add_argument("-n", "--name", help = "Organisation filter", required = False)
    parser.add_argument("-f", "--format", help = "Print format. Default is '{o} {p} {s}' ( %o organisation name, %p project name, %h http url, %s ssh Url)", default="{o} {p} {s}", required = False)
        
    options = parser.parse_args() 
    gogs = MyGogsApi(options.url)
    token = gogs_client.Token(options.token)
    repos=gogs.repos( token, options.organization )

    for repo in repos :
        if options.name is not None :
            if not fnmatch( repo.name, options.name ) :
                continue
        params = {'p': repo.name,
                  'o': repo.json['owner']['username'], 
                  's': repo.urls.ssh_url,
                  'h': repo.urls.html_url}
        print options.format.format(**params)

if __name__ == "__main__":
    main()
