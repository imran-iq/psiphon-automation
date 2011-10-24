# Copyright (c) 2011, Psiphon Inc.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
'''

import sys
import os
import syslog
import email
import json
import re

import sendmail


# We're going to use a fixed address to reply to all email from. 
# The reasons for this are:
#   - Amazon SES requires you to register ever email address you send from;
#   - Amazon SES has a limit of 100 registered addresses;
#   - We tend to set up and down autoresponse addresses quickly.
# If this becomes a problem in the future, we could set up some kind of 
# auto-verification mechanism.
RESPONSE_FROM_ADDR = 'Psiphon Responder <get@psiphon3.com>'


def get_email_localpart(email_address):
    addr_regex = '([a-zA-Z0-9\+\.\-]+)@([a-zA-Z0-9\+\.\-]+)\.([a-zA-Z0-9\+\.\-]+)'
    match = re.match(addr_regex, email_address)
    if match:
        return match.group(1)

    # Bad address. 
    return False


class MailResponder:
    '''
    Takes a configuration file and an email and sends back the appropriate 
    response to the sender.
    '''

    def __init__(self):
        self.requested_addr = None
        self._conf = None
        self._email = None

    def read_conf(self, conf_filepath):
        '''
        Reads in the given configuration file.
        Return True if successful, False otherwise.
        '''

        try:
            conffile = open(conf_filepath, 'r')

            self._response_from_addr = RESPONSE_FROM_ADDR

            # Note that json.load reads in unicode strings
            self._conf = json.load(conffile)

            # The keys in our conf file may be full email addresses, but we 
            # really just want them to be the address localpart (the part before the @)
            for addr in self._conf.keys():
                localpart = get_email_localpart(addr)
                if not localpart: 
                    # if a localpart can't be found properly, just leave it
                    continue
                self._conf[localpart] = self._conf.pop(addr)

        except Exception as e:
            syslog.syslog(syslog.LOG_CRIT, 'Failed to read conf file: %s' % e)
            return False

        return True

    def process_email(self, email_string):
        '''
        Processes the given email and sends a response.
        Returns True if successful, False or exception otherwise.
        '''

        if not self._parse_email(email_string):
            return False

        if not self._conf.has_key(self._requested_localpart):
            syslog.syslog(syslog.LOG_INFO, 'recip_addr invalid: %s' % self.requested_addr)
            return False

        raw_response = sendmail.create_raw_email(self._requester_addr, 
                                                 self._response_from_addr,
                                                 self._subject,
                                                 self._conf[self._requested_localpart])

        if not raw_response:
            return False

        if not sendmail.send_raw_email_amazonses(raw_response, 
                                                 self._response_from_addr):
            return False

        return True

    def _parse_email(self, email_string):
        '''
        Extracts the relevant items from the email.
        '''

        # Note that the email fields will be UTF-8, but we need them in unicode
        # before trying to send the response. Hence the .decode('utf-8') calls.

        self._email = email.message_from_string(email_string)

        self.requested_addr = self._email['To'].decode('utf-8')
        if not self.requested_addr:
            syslog.syslog(syslog.LOG_INFO, 'No recip_addr')
            return False
        
        # The 'To' field generally looks like this: 
        #    "get+fa" <get+fa@psiphon3.com>
        # So we need to strip it down to the useful part.
        # This regex is adapted from:
        # https://gitweb.torproject.org/gettor.git/blob/HEAD:/lib/gettor/requests.py

        to_regex = '.*?(<)?([a-zA-Z0-9\+\.\-]+@[a-zA-Z0-9\+\.\-]+\.[a-zA-Z0-9\+\.\-]+)(?(1)>).*'
        match = re.match(to_regex, self.requested_addr)
        if match:
            self.requested_addr = match.group(2)
        else:
            # Bad address. Fail.
            syslog.syslog(syslog.LOG_INFO, 'Unparsable recip_addr')
            return False

        # We also want just the localpart of the email address (get+fa or whatever).
        self._requested_localpart = get_email_localpart(self.requested_addr)
        if not self._requested_localpart:
            # Bad address. Fail.
            syslog.syslog(syslog.LOG_INFO, 'Bad recip_addr')
            return False
        
        self._requester_addr = self._email['Return-Path'].decode('utf-8')
        if not self._requester_addr:
            syslog.syslog(syslog.LOG_INFO, 'No sender_addr')
            return False

        self._subject = self._email['Subject'].decode('utf-8')

        # Add 'Re:' to the subject
        self._subject = u'Re: %s' % self._subject

        return True



if __name__ == '__main__':
    '''
    Note that we always exit with 0 so that the email server doesn't complain.
    '''

    if len(sys.argv) < 2:
        raise Exception('Not enough arguments. conf file required')

    conf_filename = sys.argv[1]

    if not os.path.isfile(conf_filename):
        raise Exception('conf file must exist: %s' % conf_filename)

    try:
        email_string = sys.stdin.read()

        if not email_string:
            syslog.syslog(syslog.LOG_CRIT, 'No stdin')
            exit(0)

        responder = MailResponder()

        if not responder.read_conf(conf_filename):
            exit(0)

        if not responder.process_email(email_string):
            exit(0)

    except Exception as e:
        syslog.syslog(syslog.LOG_CRIT, 'Exception caught: %s' % e)
    else:
        syslog.syslog(syslog.LOG_INFO, 
                      'Responded successfully to request for: %s' % responder.requested_addr)
    
    exit(0)