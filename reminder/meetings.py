#!/env/bin/python
# -*- coding: utf-8 -*-

import requests
import smtplib
import local_config as config
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from reminder import Base
import pdb

MEETINGS_URL = 'https://www.mozilla-hispano.org/documentacion/Especial:Ask/-5B-5BCategor%C3%ADa:Reuniones-5D-5D/-3FFechainicio/-3FArea/-3FAsistentes/-3FProyecto/mainlabel%3D/order%3DDESC,DESC/sort%3DFechainicio/format%3Djson/limit%3D100'

class Meetings(Base):
    ''' Reminder for meetings'''
    def __init__(self):
        self.collab_new = {}
        Base().collaborators(self.collab_new)
        self.meetings = requests.get(MEETINGS_URL).json()

    def meeting_mail(self, txtmessage, txtsubject, json):
        json = json[0]
        address = json[1]
        if address == '':
            message = 'user %s dont have mail' % json[0]
            # TODO: implement to_owner(message)
            pass
        else:
            text = txtmessage % (json[0],json[2],json[3],json[5],json[6])
            msg = MIMEText(unicode(text).encode('utf-8'))
            msg['Subject'] = txtsubject % unicode(json[4]).encode('utf-8')
            self.sender_mail(msg, address)

    def sender_mail(self, msg, address):
        msg['From'] = config.MAIL_FROM
        msg['To'] = address
        msg.set_charset('utf-8')
        server = smtplib.SMTP(config.HOST)
        server.starttls()
        server.login(config.username,config.password)
        server.sendmail(config.MAIL_FROM, address, msg.as_string())
        server.quit

    def meetings_reminder(self, txtmessage, txtsubject, condition):
        for meeting in self.meetings['items']:
            fecha = meeting['fechainicio'][0]
            fecha = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
            if condition[0] < (fecha - datetime.now() + timedelta(hours = config.localtime)) <= condition[1]:
                for user in meeting['asistentes']:
                    json = []
                    self.append_json(self.collab_new, user, meeting, fecha, json)
                    self.meeting_mail(txtmessage,txtsubject,json)

    def append_json(self, collab, user, meeting, fecha, json):
        email = collab['Usuario:' + user]
        try:
            json.append([user, email, meeting['proyecto'][0],
                        fecha.strftime('%d de %b a las %H:%M UTC'),
                        meeting['area'][0],meeting['label'],
                        fecha.strftime('%Y%m%dT%H%M')])
        except KeyError:
            json.append([user, email, meeting['area'][0],
                        fecha.strftime('%d de %b a las %H:%M UTC'),
                        meeting['area'][0],meeting['label'],
                        fecha.strftime('%Y%m%dT%H%M')])
        return json

    def meetingsthreedays(self):
        condition = [timedelta(days = 2), timedelta(days = 3)]
        txtmessage = u"""Hola %s, \n\n Te recordamos que estas registrado para asistir a la reunión de %s, el próximo %s.
                      \nPuedes ver más información acerca de la reunión en: https://www.mozilla-hispano.org/documentacion/%s 
                      \nRevisa tu hora local en http://www.timeanddate.com/worldclock/fixedtime.html?iso=%s"""
        txtsubject = '[MozillaHispano]Reunión de %s en unos días'
        self.meetings_reminder(txtmessage, txtsubject, condition)


    def meetingstoday(self):
        condition = [timedelta(hours = 2), timedelta(hours=3)]
        txtmessage = u"""Hola %s, \n\n Te recordamos que estas registrado para asistir a la reunión de %s, hoy %s. 
                      \n Puedes ver más información acerca de la reunión en: https://www.mozilla-hispano.org/documentacion/%s
                      \nRevisa tu hora local en http://www.timeanddate.com/worldclock/fixedtime.html?iso=%s"""
        txtsubject = '[MozillaHispano]Reunión de %s en unas horas'
        self.meetings_reminder(txtmessage,txtsubject,condition)
