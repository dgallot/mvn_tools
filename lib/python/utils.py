#!/usr/bin/python
from array import array
from lxml import etree
import glob, os, sys, getopt
from shutil import copyfile
import sys, paramiko
from pprint import pprint
import paramiko
import csv
import io
import getpass
import re
from colorama import Fore, init
from tabulate import tabulate
from git import Repo
from git.exc import InvalidGitRepositoryError
from collections import OrderedDict, Callable

def hightlight( str, regex ) :
    init()
    return re.sub('(' + regex + ')', Fore.RED + r'\1' + Fore.RESET, str )

def merge_two_dicts(x, y):
    z = x.copy()   
    z.update(y)  
    return z

def moveUp():
    #sys.stdout.write("\x1b[A")
    #sys.stdout.write("\x1b[K")
    return 0
        
def getEnv(name, default=None):
    if name in os.environ :
        return os.environ[name]
    else:
        return default

def getText(node):
    if node is not None :
        return node.text
    else :
        return None

def getStrippedText(node) :
    if node is not None :
        result=node.text
        if result is not None :
            return result.strip()
    return None

def infos(str, prefix):    
    for l in str.splitlines( ):
        info(prefix+l + "\n")

def info(line):
    sys.stdout.write ( "\033[95m" + line)

def error(line):
    sys.stdout.write ( "\033[95m" + line)

def mkdirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

def getGitUrl(root) :
    try :
        repo = Repo(root, search_parent_directories=True)
        return repo.remotes.origin.url
    except InvalidGitRepositoryError:
        return "N/A"

def getGitBranch(root) :
    try :
        repo = Repo(root, search_parent_directories=True)
        return repo.active_branch.name
    except InvalidGitRepositoryError:
        return "N/A"

SSH_KEY = os.path.join(os.environ['HOME'], ".ssh", "id_rsa")
SSH_CONFIG = os.path.join(os.environ['HOME'], ".ssh", "config")            
def get_ssh_keys():
    agent = paramiko.Agent()
    if len(agent.get_keys()) > 0:
      return agent.get_keys()
    try:
        return [paramiko.RSAKey.from_private_key_file(SSH_KEY)]
    except paramiko.PasswordRequiredException:
        passwd = getpass.getpass("Enter passphrase for %s: " % SSH_KEY)
        try:
            return [paramiko.RSAKey.from_private_key_file(filename=SSH_KEY,
                                                         password=passwd)]
        except paramiko.SSHException:
            print "Could not read private key; bad password?"
            raise SystemExit(1)

def  format_table(headers, rows, format) :
    if format == "csv" :
        output = io.BytesIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, delimiter=',')
        writer.writerow(headers)
        writer.writerows(rows)
        return output.getvalue()    
    elif format == "tsv" :
        output = io.BytesIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, delimiter='\t')
        writer.writerow(headers)
        writer.writerows(rows)
        return output.getvalue()
    else:
        return tabulate(rows, headers=headers, tablefmt=format)

def extract_properties_name(expression):
    def replace_properties(m):
        print ( "Value: " + m.group(1) )
        value=m.group(1) + "\n"
        return value
    reVar = r'[^\$\{}]*\$\{([^}]*)\}[^\$\{}]*'
    if re.match(reVar, expression) :
        return [ x for x in re.sub(reVar, replace_properties, expression).split('\n') if x ];
    else :
        return []

def expand_properties(expression, properties, missing_properties=set(), skip_escaped=True):
    def replace_properties(m):
        value=None
        name = m.group(1)
        if name is not None :
            if name in properties :
                value=properties[name]
        if value is None :
            value = m.group(0)
            missing_properties.add(m.group(0))
        if value is None :
            value = ''
        return value
    reVar = r'\$\{([^}]*)\}'
    return re.sub(reVar, replace_properties, expression)

class Ssh :
    shell=None
    def __init__(self, hostname, instance = None, port=22, username=None, keyfile='~/.ssh/id_rsa', keyfile_password=None):
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        ssh_config = paramiko.SSHConfig()
        user_config_file = os.path.expanduser("~/.ssh/config")
        if os.path.exists(user_config_file):
            with open(user_config_file) as f:
                ssh_config.parse(f)
        if keyfile_password is None :
            keyfile_password = getpass.getpass("Enter passphrase for %s: " % keyfile)
        try:
            key = paramiko.RSAKey.from_private_key_file(os.path.expanduser(keyfile), password=keyfile_password)
        except paramiko.PasswordRequiredException:
            keyfile_password = getpass.getpass("Enter passphrase for %s: " % SSH_KEY)
            key = paramiko.RSAKey.from_private_key_file(os.path.expanduser(keyfile), password=keyfile_password)
        
        user_config = ssh_config.lookup(hostname)
        if 'hostname' in user_config:
            hostname = user_config['hostname'] 
        if 'user' in user_config:
            username = user_config['user'] 
        if 'port' in user_config:
            port = int( user_config['port'] )
        self.client.connect(hostname=hostname, port=port, username=username, pkey=key)        
        stdin, stdout, stderr = self.client.exec_command("hostname")
        self.hostname = stdout.read().strip()
        self.instance = instance
    
    def run( self, cmd ) :
        if self.instance is not None :
            cmd = "ssh " + self.instance + " "+ cmd
        stdin, stdout, stderr = self.client.exec_command(cmd)
        return stdout.read()
    
    def shell_send( self, cmd ) :
        if self.shell is None : 
            self.shell = session.invoke_shell(term='vt100', width=300, height=100, width_pixels=1024, height_pixels=800)
            if self.instance is not None :
                cmd = "ssh " + self.instance
                
    def shell_recv( self, cmd ) :
        return chan.recv(1024)
    
    def close( self ):
        self.client.close()

class DefaultOrderedDict(OrderedDict):
    # Source: http://stackoverflow.com/a/6190500/562769
    def __init__(self, default_factory=None, *a, **kw):
        if (default_factory is not None and
           not isinstance(default_factory, Callable)):
            raise TypeError('first argument must be callable')
        OrderedDict.__init__(self, *a, **kw)
        self.default_factory = default_factory

    def __getitem__(self, key):
        try:
            return OrderedDict.__getitem__(self, key)
        except KeyError:
            return self.__missing__(key)

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = value = self.default_factory()
        return value

    def __reduce__(self):
        if self.default_factory is None:
            args = tuple()
        else:
            args = self.default_factory,
        return type(self), args, None, None, self.items()

    def copy(self):
        return self.__copy__()

    def __copy__(self):
        return type(self)(self.default_factory, self)

    def __deepcopy__(self, memo):
        import copy
        return type(self)(self.default_factory,
                          copy.deepcopy(self.items()))

    def __repr__(self):
        return 'OrderedDefaultDict(%s, %s)' % (self.default_factory, OrderedDict.__repr__(self))

class hashabledict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))

