#!/env/bin/python
# -*- coding: utf-8 -*-

import urllib
import requests
import json
import smtplib
import string
import re
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import local_config as config

COLLABORATORS_URL = config.MAIN_URL + '&q=[[Category:Colaborador]]&po=?Correo&p[format]=json&p[limit]=1000'
AREA_OWNER_URL = config.MAIN_URL + '&po=?Responsable&p[format]=json&q='

class Base(object):

    def convert_to_email(self, emailString):
        '''
        Converts the email string into a valid email address. This is necessary
        because addresses can be obfuscated (name ARROBA server PUNTO com).
        '''
        email = emailString.strip()
        # The spaces around the 'at' are intentional. It avoids picking up names
        # with 'at' in them. Why algarrobo? Ask StripTM :|
        pattern = re.compile('\s?(arroba| at |@|algarrobo)\s?', re.IGNORECASE)
        email = pattern.sub('@', emailString, 1)
        pattern = re.compile('\s?(punto|dot)\s?', re.IGNORECASE)
        email = pattern.sub('.', email)
        # MediaWiki doesn't handle underscores well (issue #17).
        email = email.replace(' ', '_')
        return email

    def getAreaOwners(self, area, collab_new):
        '''
        Gets the user information of the owners of the given focus area.
        '''
        owners = []
        areaOwners = {}

        if len(area) != 0:
            quotedArea = urllib.quote_plus(area.encode('utf-8'))

            if quotedArea not in areaOwners:
                ownerURL = AREA_OWNER_URL + '[[' + quotedArea + ']]'
                ownerObj = requests.get(ownerURL).json()

                for ownerList in ownerObj['items']:
                    for owner in ownerList['responsable']:
                        userString = 'Usuario:' + owner

                        if userString in collab_new:
                            owners.append(owner)
                    # Save locally for future use.
                    areaOwners[quotedArea] = owners
            else:
                # Use saved copy instead of fetching it again.
                owners = areaOwners[quotedArea]
        return owners


    def collaborators(self, collab_new):
        '''
        we get json from media wiki with this structure:
            colab['items'][n]['label']
            colab['items'][n]['correo']
        but this is not usable and mails isn't in mail format, this is for
        solve that.
        '''
        collab = requests.get(COLLABORATORS_URL).json()
        self.get_collab(collab, collab_new)

    def get_collab(self, collab, collab_new):
        '''
        for each collaborator we get a dictionary with collaborators name
        (ncollab) and collaborators mail (mcollab)
        '''
        n = len(collab["items"])
        for var in range(n):
            ncollab = collab['items'][int(var)]['label']
            try:
                mcollab = self.convert_to_email(collab['items'][int(var)]['correo'][0])
            except KeyError:
                mcollab = ''
            collab_new.update({ncollab:mcollab})
        return collab_new
