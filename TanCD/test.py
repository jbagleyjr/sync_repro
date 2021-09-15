#!/usr/bin/python2

token = 'blah'

print({
    'command_name': 'dec.open-session-request',
    'payload': { 'session_context': token },
    }, {
        'wait_secs': 5,
    })
