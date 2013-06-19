#!/env/bin/python
# -*- coding: utf-8 -*-

import urllib
import requests
import json
import smtplib
import string
import re
from email.mime.text import MIMEText
from collections import defaultdict
from datetime import datetime, timedelta
import local_config as config

COLLABORATORS_URL = 'https://www.mozilla-hispano.org/documentacion/Especial:Ask/-5B-5BCategoría:Colaborador-5D-5D/-3FCorreo/mainlabel%3D/format%3Djson/limit%3D1000'
AREA_OWNER_URL = 'https://www.mozilla-hispano.org/documentacion/index.php?title=Especial%3AAsk&po=%3FResponsable%0D%0A&p[format]=json&q='
MEETINGS_URL = 'https://www.mozilla-hispano.org/documentacion/Especial:Ask/-5B-5BCategor%C3%ADa:Reuniones-5D-5D/-3FFechainicio/-3FArea/-3FAsistentes/-3FProyecto/mainlabel%3D/order%3DDESC,DESC/sort%3DFechainicio/format%3Djson/limit%3D100'

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

# meetings reminder
class Meetings(Base):
    def __init__(self):
        self.collab_new = {}
        Base().collaborators(self.collab_new)
        self.meetings = requests.get(MEETINGS_URL).json()

    def meetingmail(self, txtmessage, txtsubject, json):
        try:
            address = json[1]
            text = txtmessage % (json[0],json[2],json[3],json[5],json[6])
            msg = MIMEText(unicode(text).encode('utf-8'))
            msg['Subject'] = txtsubject % unicode(json[4]).encode('utf-8')
            msg['From'] = config.MAIL_FROM
            msg['To'] = address
            msg.set_charset('utf-8')
            server = smtplib.SMTP(config.HOST)
            server.starttls()
            server.login(config.username,config.password)
            server.sendmail(config.MAIL_FROM, address, msg.as_string())
            server.quit
        except Exception:
            pass

    def separatemeetings(self, txtmessage, txtsubject, condition):
        for meeting in self.meetings['items']:
            fecha = meeting['fechainicio'][0]
            fecha = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
            if condition[0] < (fecha - datetime.now() + timedelta(hours = config.localtime)) <= condition[1]:
                for user in meeting['asistentes']:
                    json = []
                    try:
                        email = self.collab_new['Usuario:' + user]
                        try:
                            json.append([user, email, meeting['proyecto'][0],fecha.strftime('%d de %b a las %H:%M UTC'),meeting['area'][0],meeting['label'],fecha.strftime('%Y%m%dT%H%M')])
                        except KeyError:
                            json.append([user, email, meeting['area'][0],fecha.strftime('%d de %b a las %H:%M UTC'),meeting['area'][0],meeting['label'],fecha.strftime('%Y%m%dT%H%M')])
                        json = json[0]
                        Meetings().meetingmail(txtmessage,txtsubject,json)
                    except KeyError:
                        #ToDo: user don't have mail :S, message to nukeador
                        pass

    def meetingsthreedays(self):
        condition = [timedelta(days = 2), timedelta(days = 3)]
        txtmessage = u"""Hola %s, \n\n Te recordamos que estas registrado para asistir a la reunión de %s, el próximo %s.
                      \nPuedes ver más información acerca de la reunión en: https://www.mozilla-hispano.org/documentacion/%s 
                      \nRevisa tu hora local en http://www.timeanddate.com/worldclock/fixedtime.html?iso=%s"""
        txtsubject = '[MozillaHispano]Reunión de %s en unos días'
        self.separatemeetings(txtmessage, txtsubject, condition)


    def meetingstoday(self):
        condition = [timedelta(hours = 2), timedelta(hours=3)]
        txtmessage = u"""Hola %s, \n\n Te recordamos que estas registrado para asistir a la reunión de %s, hoy %s. 
                      \n Puedes ver más información acerca de la reunión en: https://www.mozilla-hispano.org/documentacion/%s
                      \nRevisa tu hora local en http://www.timeanddate.com/worldclock/fixedtime.html?iso=%s"""
        txtsubject = '[MozillaHispano]Reunión de %s en unas horas'
        self.separatemeetings(txtmessage,txtsubject,condition)
