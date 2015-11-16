#!/usr/bin/env python
# This script takes the first command line argument and checks if it points to a valid elasticsearch cluster, and then
# starts up kibana. 

########################################################################################################################
# LIBRARY IMPORT                                                                                                       #
########################################################################################################################
# Import required libaries
import sys,os,pwd,grp   # OS Libraries
import argparse         # Parse Arguments
from subprocess import Popen, PIPE, STDOUT
                        # Open up a process

# Important required templating libarires
from jinja2 import Environment as TemplateEnvironment, \
                   FileSystemLoader, Template
                        # Import the jinja2 libaries required by this script
from jinja2.exceptions import TemplateNotFound
                        # Import any exceptions that are caught by the Templates section

# Specific to to this script
import itertools        # Required to chain the tags together properly
import OpenSSL          # SSL Library for testing certificates
from Crypto.Util import asn1 

# Variables/Consts
ssl_path = '/ls-data/ssl/'

########################################################################################################################
# ARGUMENT PARSER                                                                                                      #
# This is where you put the Argument Parser lines                                                                      #
########################################################################################################################
argparser = argparse.ArgumentParser(description='Run a docker container containing a Logstash Instance')

helptxt = 'The hash key used by Logstash. (Make sure it is consistent when running multiple instances)'
helptxt += ' (Default "docker-logstash")'

argparser.add_argument('--stdout',
                       action='store_true',
                       help='Also output logs processed to stdout for debug (Not Recommend)')

# Arguments Specific to Hashing
argparser_hash = argparser.add_argument_group('hashing','Arguments specific to hashing')
argparser_hash.add_argument('--hash-key','-k',
                       action='store',
                       nargs='?',
                       help=helptxt,
                       default="docker-logstash")

argparser_hash.add_argument('--use-sha512','-5',
                       action='store_true',
                       help='By default this container uses SHA256 for hashing, override and use SHA512.')


# Arguments specific to Elasticsearch
argparser_es = argparser.add_argument_group('elasticsearch','Arguments specific to connecting to Elasticsearch')
argparser_es.add_argument('--es-cluster-name','-c',
                          action='store',
                          nargs='?',
                          help='The name of the cluster the Elasticsearch Instance should connect to',
                          default='es-logstash')
argparser_es.add_argument('--es-node-name','-n',
                          action='store',
                          nargs='?',
                          help='The node name this logstash node should use when connecting to Elasticsearch')
argparser_es.add_argument('--es-bind-host','-b',
                          action='store',
                          nargs='?',
                          help='Override the default bind host (which is by default the first interface)')

# Lumberjack Input 
argparser_lm = argparser.add_argument_group('lumberjack',
                                             'Arguments for when you want to use Lumberjack input' )
argparser_lm.add_argument('--lm-ssl-crt', '-R',
                             action='store',
                             nargs='?',
                             help='Certificate for SSL termination, under the %s volume' % ssl_path)
argparser_lm.add_argument('--lm-ssl-key', '-K',
                             action='store',
                             nargs='?',
                             help='SSL Key for SSL termination, under the %s volume' % ssl_path)
argparser_lm.add_argument('--lm-type', '-T',
                             action='store',
                             nargs='?',
                             help='If you want the lumberjack messages to have a specific type, state it here')
argparser_lm.add_argument('--lm-tags','-t',
                             action='append',
                             nargs='*',
                             help='If you want the lumberjack messages to have tags applied, state them here')
argparser_lm.add_argument('--ignore-match-errors',
                             action='store_true',
                             help='Ignore SSL certificate match errors. (Not recommended)')

try:
    args = argparser.parse_args()
except SystemExit:
    sys.exit(0) # This should be a return 0 to prevent the container from restarting
    
########################################################################################################################
# ARGUMENT VERIRIFCATION                                                                                               #
# This is where you put any logic to verify the arguments, and failure messages                                        #
########################################################################################################################
    
# Check to make sure that the cert files and keys exist, and both were provided
if (args.lm_ssl_crt is not None) ^ (args.lm_ssl_key is not None): # ^ = xor
    print "The arguments --lm-ssl-crt and --lm-ssl_key must be provided together, terminating..."
    sys.exit(0) # This should be a return 0 to prevent the container from restarting.

for file in (args.lm_ssl_crt, 'LM Certificate'), (args.lm_ssl_key, 'LM Key'):
    if file[0] is not None and not os.path.isfile(ssl_path + file[0]):
        print "The %s file provided was not a valid valid file. Please provide a valid file, terminating..." % file[1]
        sys.exit(0) # This should be a return 0 to prevent the container from restarting
        
for pair in [(args.lm_ssl_crt, args.lm_ssl_key, 'LM')]:
    if pair[0] is None or args.ignore_match_errors:
        continue # We don't need to do this if there are no files to check
    
    # Attempt to open the files
    try:
        crt_fh = open(ssl_path + pair[0])
        key_fh = open(ssl_path + pair[1])
    except IOError as e:
        print "One of the files provided in the %s key pair could not be opened, terminating..." % pair[2]

    # Read in the files
    crt_raw = crt_fh.read()
    key_raw = key_fh.read()
    
    # Close the files
    crt_fh.close()
    key_fh.close()
    
    # Attempt to load the crt and key as objects
    try:
        crt = OpenSSL.crypto.load_certificate(OpenSSL.SSL.FILETYPE_PEM,crt_raw)
        key = OpenSSL.crypto.load_privatekey(OpenSSL.SSL.FILETYPE_PEM,key_raw)
    except OpenSSL.crypto.Error as e:
        print "One of the files provided in the %s key pair is not valid (returned %s), terminating..." % pair[2], e
        sys.exit(0) # This should be a return 0 to prevent the container from restarting.
    except:
        e = sys.exc_info()[0]
        print "Unrecognised exception occured, was unable to perform cert verification returned %s), terminating..." % e
        sys.exit(0) # This should be a return 0 to prevent the container from restarting.
    
    pub = crt.get_pubkey()
        
    # Convert to ASN1
    pub_asn1 = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_ASN1, pub)
    key_asn1 = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_ASN1, key)
    
    # Decode DER
    pub_der = asn1.DerSequence()
    key_der = asn1.DerSequence()
    pub_der.decode(pub_asn1)
    key_der.decode(key_asn1)
    
    # Get the modulus
    pub_mod = pub_der[1]
    key_mod = key_der[1]
    
    if pub_mod != key_mod:
        errormsg = "The files provided in the %s key pair do not appear to match," % pair[2]
        errormsg += " override with --ignore-match-errors, terminating..."
        print errormsg
        sys.exit(0) # This should be a return 0 to prevent the container from restarting.
        
lm_tags = list(itertools.chain(*args.lm_tags)) if args.lm_tags is not None else None # Make lm_tags one merged list
########################################################################################################################
# TEMPLATES                                                                                                            #
# This is where you manage any templates                                                                               #
########################################################################################################################
# Configuration Location goes here
template_location = '/ls-templates'

# Create the template list
template_list = {}

# Templates go here
### 00-ls-input.conf ###
template_name = '00-ls-input.conf'
template_dict = { 'context' : { # Subsitutions to be performed
                                'lm_ssl_crt'   : args.lm_ssl_crt,
                                'lm_ssl_key'   : args.lm_ssl_key,
                                'lm_type'      : args.lm_type,
                                'lm_tags'      : lm_tags,
                              },
                  'path'    : '/ls-data/conf/00-ls-input.conf',
                  'user'    : 'root',
                  'group'   : 'root',
                  'mode'    : 0644 }
template_list[template_name] = template_dict

## 80-hash-filter.conf ###
template_name = '80-hash-filter.conf'
template_dict = { 'context' : { # Subsitutions to be performed
                                'use_sha512'   : args.use_sha512,
                                'hash_key'     : args.hash_key,
                              },
                  'path'    : '/ls-data/conf/80-hash-filter.conf',
                  'user'    : 'root',
                  'group'   : 'root',
                  'mode'    : 0644 }
template_list[template_name] = template_dict

### 90-ls-output ###
template_name = '90-ls-output.conf'
template_dict = { 'context' : { # Subsitutions to be performed
                                'stdout'          : args.stdout,
                                'es_node_name'    : args.es_node_name,
                                'es_cluster_name' : args.es_cluster_name,
                                'es_bind_host'    : args.es_bind_host,
                              },
                  'path'    : '/ls-data/conf/90-ls-output.conf',
                  'user'    : 'root',
                  'group'   : 'root',
                  'mode'    : 0644 }
template_list[template_name] = template_dict

# Load in the files from the folder
template_loader = FileSystemLoader(template_location)
template_env = TemplateEnvironment(loader=template_loader,
                                   lstrip_blocks=True,
                                   trim_blocks=True,
                                   keep_trailing_newline=True)

# Load in expected templates
for template_item in template_list:
    # Attempt to load the template
    try:
        template_list[template_item]['template'] = template_env.get_template(template_item)
    except TemplateNotFound as e:
        errormsg = "The template file %s was not found in %s (returned %s)," % (template_item, template_location, e)
        errormsg += " terminating..."
        print errormsg
        sys.exit(0) # This should be a return 0 to prevent the container from restarting

    # Attempt to open the file for writing
    try:
        template_list[template_item]['file'] = open(template_list[template_item]['path'],'w')
    except IOError as e:
        errormsg = "The file %s could not be opened for writing for template" % template_list[template_item]['path']
        errormsg += " %s (returned %s), terminating..." % template_item, e
        print errormsg
        sys.exit(0) # This should be a return 0 to prevent the container from restart
    
    # Stream
    try:
        template_list[template_item]['render'] = template_list[template_item]['template'].\
                                             render(template_list[template_item]['context'])
    
        # Submit to file
        template_list[template_item]['file'].write(template_list[template_item]['render'].encode('utf8'))
        template_list[template_item]['file'].close()
    except:
        e = sys.exc_info()[0]
        print "Unrecognised exception occured, was unable to create template (returned %s), terminating..." % e
        sys.exit(0) # This should be a return 0 to prevent the container from restarting.


    # Change owner and group
    try:
        template_list[template_item]['uid'] = pwd.getpwnam(template_list[template_item]['user']).pw_uid
    except KeyError as e:
        errormsg = "The user %s does not exist for template %s" % template_list[template_item]['user'], template_item
        errormsg += "(returned %s), terminating..." % e
        print errormsg
        sys.exit(0) # This should be a return 0 to prevent the container from restarting

    try:
        template_list[template_item]['gid'] = grp.getgrnam(template_list[template_item]['group']).gr_gid
    except KeyError as e:
        errormsg = "The group %s does not exist for template %s" % template_list[template_item]['group'], template_item
        errormsg += "(returned %s), terminating..." % e
        print errormsg
        sys.exit(0) # This should be a return 0 to prevent the container from restarting

    try:
        os.chown(template_list[template_item]['path'],
                 template_list[template_item]['uid'],
                 template_list[template_item]['gid'])
    except OSError as e:
        errormsg = "The file %s could not be chowned for template" % template_list[template_item]['path']
        errormsg += " %s (returned %s), terminating..." % template_item, e
        print errormsg
        sys.exit(0) # This should be a return 0 to prevent the container from restarting

    # Change premisions
    try:
        os.chmod(template_list[template_item]['path'],
                 template_list[template_item]['mode'])
    except OSError as e:
        errormsg = "The file %s could not be chmoded for template" % template_list[template_item]['path']
        errormsg += " %s (returned %s), terminating..." % template_item, e
        print errormsg
        sys.exit(0) # This should be a return 0 to prevent the container from restarting

########################################################################################################################
# SPAWN CHILD                                                                                                          #
########################################################################################################################
# Flush anything on the buffer
sys.stdout.flush()

# Spawn the child
child_path = ["/logstash/bin/logstash", "-f", "/ls-data/conf/"]
child = Popen(child_path, stdout = PIPE, stderr = STDOUT, shell = False) 

# Reopen stdout as unbuffered. This will mean log messages will appear as soon as they become avaliable.
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

# Output any log items to Docker
for line in iter(child.stdout.readline, ''):
    sys.stdout.write(line)

# If the process terminates, read its errorcode and return it
sys.exit(child.returncode)
