#!/usr/bin/env python3

import json, time, sys, base64,subprocess
import tanrest
from pprint import pprint as pp
from time import sleep
import getpass
import getopt
import re

##
# Copyright 2019 Mentor Graphics
# SPDX-License-Identifier: Apache-2.0


def git_revision_hash():
    return subprocess.getoutput('git rev-parse --short HEAD')

def release_hash():
    file = open("release")
    release = file.read().replace("\n", " ").strip()
    file.close()
    return release

def usage():
    print("""
    Usage:
        tanium_deploy_puppet.py [options]
    
    Description:
        Deploys Puppet environment content (uploaded with put_puppet.py) to all Tanium endpoints
        that need it.  This uses the 'DISW Puppet Update Needed' sensor so it can be re-run fairly
        frequently without much overhead.

    Options:
        -h, --help      display this help and exit
        --server        [required] tanium server (ip address or dns name) [required]
        --username      user name to connect to tanium with (defaults to logged in user)
        --password      password to connect to tanium with (will prompt if not provided)
        --environment   the puppet environment to deploy to (usually test or production)
        --action_group  the tanium action group to target (defaults to "all computers")

    Example:
        ./deploy_puppet.py --server 139.181.111.21 --username tanium --environment production --action_group "all windows"

    """)

def escape_ansi(line):
	ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
	try:
		return ansi_escape.sub('', line)
	except:
		return 'no output'

def main(argv):
    #print(argv)
    global loglevel
    creds = {}
    action_group = "all computers"
    try:
        opts, args = getopt.getopt(argv,"d:hs:p:q:",["debug:","help","server=", "username=", "password=", "environment=","action_group="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(2)
        if opt in ('d', '--debug'):
            loglevel = arg
        if opt in ('--server'):
            creds['server'] = arg
        if opt in ('--username'):
            creds['username'] = arg
        if opt in ('--password'):
            creds['password'] = arg
        if opt in ('--environment'):
            environment = arg
        if opt in ('--action_group'):
            action_group = arg

    if 'server' not in creds:
        print("--server parameter required")
        usage()
        sys.exit(2)
    else:
        if 'http' not in creds['server']:
            creds['server'] = 'https://' + creds['server']
        if '/api/v2' not in creds['server']:
            creds['server'] = creds['server'] + '/api/v2'

    if 'username' not in creds:
        creds['username'] = getpass.getuser()
    if 'password' not in creds:
        creds['password'] = getpass.getpass()

    tan = tanrest.server(creds)

    action_spec = {
        "name" : "testing actions via rest api",
        "comment" : "this is a new comment",
        "package_spec" : {
            "source_id" : tan.get_package_id('DISW Puppet Content test'),
            "parameters": []
        },
        "action_group" : {
            "id" : tan.get_action_group_id(action_group)
        },
       "target_group" : {
            'and_flag': True,
            'filters': [
                {
                    'sensor': {
                        'source_hash': tan.get_sensor_hash("DISW Puppet Update Needed"),
                        'parameters': [
                            {
                                "key": "||release||",
                                "value": str(release_hash())
                            },
                            {
                                "key": "||environment||",
                                "value": environment
                            }
                        ],
                    },
                    'operator': 'Equal',
                    'value': 'True',
                    'value_type': 'String',
                    'ignore_case_flag': True,
                }
            ]           
       },
        "expire_seconds" : 1800,
        "issue_seconds" : 14400
    }

    #pp(action_spec)
    #action = tan.run_action(action_spec,get_results = True)
	#action = self.req('POST', 'actions/', action_spec)

    #saved_action = tan.req('POST', 'saved_actions/', action_spec)

    action_id = tan.get_scheduled_action_id('testing actions via rest api')
    while action_id:
        action_id = tan.get_scheduled_action_id('testing actions via rest api')
        delete = tan.delete_scheduled_action(action_id)

    action = tan.schedule_action(action_spec,get_results = True)

    pp(action)

if __name__ == "__main__":
   main(sys.argv[1:])

