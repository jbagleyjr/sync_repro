#!/usr/bin/env python3
import json, time, sys, base64, os
from TanCD import tanrest
from pprint import pprint as pp
from time import sleep
import getpass
import getopt

import subprocess


def usage():
    print("""
    Usage:
        tanium_put.py [options]
    
    Description:
        Uploads test package to the Tanium server.
        
        Command:
            $TANIUM_CLIENT_EXECUTABLE runscript InternalPython test.py
    
    Options:
        -h, --help      display this help and exit
        --server        [required] tanium server (ip address or dns name) [required]
        --username      user name to connect to tanium with (defaults to logged in user)
        --password      password to connect to tanium with (will prompt if not provided)
        --string        unique string to use in deployment action

    Example:
        ./tanium_put.py --server 139.181.111.21 --username tanium

    """)

def main(argv):

    global loglevel
    creds = {}

    try:
        opts, args = getopt.getopt(argv,"d:hs:p:q:b:",["debug:","help", "environment=", "server=", "username=", "password=", "string="])
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
        if opt in ('--string'):
            string = arg

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


    f = open("string.txt", "w")
    f.write(string)
    f.close()

    tan = tanrest.server(creds)

    package = {
        'name': 'DISW package sync test',
        'display-name':'DISW package sync test',
        'command': '$TANIUM_CLIENT_EXECUTABLE runscript InternalPython test.py',
        'files': [
            {
                'name': 'test.py',
                'source': '',
                'download_seconds': 3600
            },
            {
                'name': 'time.txt',
                'source': '',
                'download_seconds': 3600
            }
        ],
        'expire_seconds': 60,
        "skip_lock_flag": False,
        "process_group_flag": True,
    }

    #pp(package)
    package_id = tan.get_package_id(package['name'])

    if package_id:
        if tan.update_package(package_id, package):
            print('updated existing package: ' + package["name"] + ' (' + str(package_id) + ')')
    else:
        resp = tan.create_package(package)
        if resp:
            print('created new package: ' + package["name"] + ' (' + str(resp['data']['id']) + ')')
            package_id = str(resp['data']['id'])

    #package = tan.get_package(package_id)
    while True:
        package_update = tan.req('GET', 'packages/' + str(package_id))
        if package_update:
            sleep(3)
            #pp(package_update['data']['files'])
            allcached = True
            for package_file in package_update['data']['files']:
                # pp({
                #     'name': package_file['name'],
                #     'cache_status': package_file['file_status'][0]['cache_status'],
                #     'status': package_file['file_status'][0]['status']
                # })
                print(package_file['name'] + ': ' + package_file['file_status'][0]['cache_status'] + ' (' + str(package_file['file_status'][0]['status']) + ')')
                if package_file['file_status'][0]['status'] != 200:
                    allcached = False

            if allcached:
                break

if __name__ == "__main__":
   main(sys.argv[1:])
