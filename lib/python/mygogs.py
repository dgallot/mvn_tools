#!/usr/bin/python
import os
import sys
import subprocess
import argparse
import gogs_client
import errno
from inspect import getmembers
from pprint import pprint

class MyGogsApi(gogs_client.GogsApi):
    # class code follows...
    def __init__(self, base_url):
        gogs_client.GogsApi.__init__(self,  base_url)
    def repos(self, auth, org):
        path = "/user/repos"
        response = self._get(path, auth=auth)
        raw = [gogs_client.GogsRepo.from_json(repo_json) for repo_json in response.json()]
        filtered = filter( lambda repo: repo.owner.json['login'] == org, raw ) if org is not None else raw
        return filtered 


