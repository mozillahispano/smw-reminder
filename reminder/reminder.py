#!/env/bin/python
# -*- coding: utf-8 -*-

import requests
import json
import smtplib
import string
import re
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import local_config as config

COLLABORATORS_URL = config.MAIN_URL + '&q=[[Category:Colaborador]]&po=?Correo&p[format]=json&p[limit]=1000'
AREA_OWNER_URL = config.MAIN_URL + '&po=?Responsable&p[format]=json&q=[[%s]]'

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

    def get_area_owners(self, area, area_owners):
        '''
        Gets the user information of the owners of the given focus area.
        '''
        if area not in area_owners:
            owner_url = AREA_OWNER_URL % area
            owners = requests.get(ownerURL).json()
            area_owners.update({ area: owners['items'][0]['responsable']})
        return area_owners

    def get_owner_data(self, area, area_owners, collab_new, owner_array):
        for owner in area_owners[area]:
            user = 'Usuario:' + owner
            if user in collab_new:
                owner_array.append(owner)
        return owner_array

    def report_to_owner(self, area, area_owners, collab_new):
        owner_array = []
        self.get_area_owner(area, area_owners)
        self.get_owner_data(area, area_owners, collab_new, owner_array)

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
