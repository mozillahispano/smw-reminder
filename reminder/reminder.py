#!/env/bin/python
# -*- coding: utf-8 -*-

import urllib
import urllib2
import json
import smtplib
import string
import re
from email.mime.text import MIMEText
from collections import defaultdict
from datetime import datetime, timedelta
from local_config import *

TASKS_URL = 'https://www.mozilla-hispano.org/documentacion/Especial:Ask/-5B-5BCategor%C3%ADa:Tarea-5D-5D-5B-5Bestado::!Finalizado-5D-5D/-3FResponsable%3DRespon./-3FArea/-3FProyecto/-3FEstado/-3FFechafin%3DL%C3%ADmite/mainlabel%3D/order%3DASC,ASC/sort%3DFechafin,Estado/format%3Djson/limit%3D1000'
COLLABORATORS_URL = 'https://www.mozilla-hispano.org/documentacion/Especial:Ask/-5B-5BCategoría:Colaborador-5D-5D/-3FCorreo/mainlabel%3D/format%3Djson/limit%3D1000'
AREA_OWNER_URL = 'https://www.mozilla-hispano.org/documentacion/index.php?title=Especial%3AAsk&po=%3FResponsable%0D%0A&p[format]=json&q='
MEETINGS_URL = 'https://www.mozilla-hispano.org/documentacion/Especial:Ask/-5B-5BCategor%C3%ADa:Reuniones-5D-5D/-3FFechainicio/-3FArea/-3FAsistentes/-3FProyecto/mainlabel%3D/order%3DDESC,DESC/sort%3DFechainicio/format%3Djson/limit%3D100'

# Dictionary that maps areas to an array of owner email addresses.
areaOwners = {}

def convert_to_email(emailString):
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

def getAreaOwners(area, collab_new):
    '''
    Gets the user information of the owners of the given focus area.
    '''
    owners = []

    if len(area) != 0:
        quotedArea = urllib.quote_plus(area.encode('utf-8'))

        if quotedArea not in areaOwners:
            ownerURL = AREA_OWNER_URL + '[[' + quotedArea + ']]'
            ownerJSON = urllib2.urlopen(ownerURL).read()
            ownerObj = json.loads(ownerJSON)

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


def collaborators(collab_new):
    '''
    we get json from media wiki with this structure:
        colab['items'][n]['label']
        colab['items'][n]['correo']
    but this is not usable and mails isn't in mail format, this is for
    solve that.
    '''
    json_collab = urllib2.urlopen(COLLABORATORS_URL).read()
    collab = json.loads(json_collab)
    get_collab(collab, collab_new)

def get_collab(collab, collab_new):
    '''
    for each collaborator we get a dictionary with collaborators name
    (ncollab) and collaborators mail (mcollab)
    '''
    n = len(collab["items"])
    for var in range(n):
        ncollab = collab['items'][int(var)]['label']
        try:
            mcollab = convert_to_email(collab['items'][int(var)]['correo'][0])
        except KeyError:
            mcollab = ''
        collab_new.update({ncollab:mcollab})
    return collab_new

class Tasks(object):
    '''
    Like json collab, tasks json structure is:
        tasks['items'][n]['respon.']
        tasks['items'][n]['label']
        tasks['items'][n][u'límite']
    this is to append collaborator mail with this data and separate tasks
    according to date limit: if is overdue (tasks_overdue),
    that mature in three days (tasks_threedays) and that mature today
    (tasks_onday)
    '''
    def __init__(self):
        self.collab_new = {}
        collaborators(self.collab_new)
        json_tasks = urllib2.urlopen(TASKS_URL).read()
        self.tasks = json.loads(json_tasks)

    def getTasks(self, condition, tasks, tasks_response, collab):
        for task in tasks['items']:
            # Get the date limit and figure out if we need to do anything.
            if u'límite' in task:
                limit = task[u'límite'][0]
                datelimit = datetime.strptime(limit , '%Y-%m-%d %H:%M:%S')
                if condition[0] < (datelimit - datetime.now()) <= condition[1]:
                    assignees = []
                    # Get assignees from task.
                    if 'respon.' in task:
                        Tasks().get_assignees(task, collab, assignees)
                    # If there are none, get area owners.
                    if len(assignees) == 0:
                        pass
                        #TODO: implement getAreaOwners
                    for assignee in assignees:
                        email = collab['Usuario:' + assignee]
                        tasks_response.append([assignee, email, task['label'], limit])
        return tasks_response

    def get_assignees(self, task, collab, assignees):
        for user in task['respon.']:
            userString = 'Usuario:' + user
            if userString in collab:
                assignees.append(user)
        return assignees

    def tasksmail(self, txtmessage, txtsubject, k, v):
        try:
            respon = k[0]
            numtasks = len(v)
            text = txtmessage % (respon, numtasks)
            for i in range(numtasks):
                b = [w.replace(' ','_') for w in [v[int(i)]]]
                text = text + '\n' + v[int(i)] + ' https://www.mozilla-hispano.org/documentacion/'+ b[0]
            text = text + '\n\nSaludos'
            msg = MIMEText(unicode(text).encode('utf-8'))
            msg['Subject'] = txtsubject % numtasks
            msg['From'] = MAIL_FROM
            msg['To'] = k[1]
            msg.set_charset('utf-8')
            server = smtplib.SMTP(HOST)
            server.starttls()
            server.login(username,password)
            server.sendmail(MAIL_FROM, k[1], msg.as_string())
            server.quit()
        except Exception:
            pass

    def send_mail(self, txtmessage, txtsubject, tasks_list):
        '''
        send mails for each collaborator
        '''
        d = defaultdict(list)
        for resp,mailresp,label,limit in tasks_list:
            '''
            for order tasks (label) for each collaborator, result a dict
            with 2 items
            '''
            d[resp,mailresp].append(label)
        for k,v in d.items():
            '''
            lines before, we get a dict (d) with 2 items. Now I parse this
            items (k,v) in mail message
            '''
            toAddress = k[1]
            if (toAddress != ''):
                Tasks().tasksmail(txtmessage, txtsubject, k,v)
            else:
                # TODO: show a 'no email address for user X' error.
                pass

    def send_tasks(self, txtmessage, txtsubject, condition):
        tasks_json = []
        Tasks().getTasks(condition, self.tasks, tasks_json, self.collab_new)
        Tasks().send_mail(txtmessage, txtsubject, tasks_json)

    def taskoverdue(self):
        '''
        text for message and subject for overdue tasks
        '''
        condition = [timedelta(weeks = -1000), timedelta(hours = 0)]
        txtmessage = u"Hola %s, \n\nActualmente tienes %s tarea(s) asignada(s) a ti que están caducadas. Por favor revisa su estado y marcalas como finalizadas o amplia su fecha límite \n"
        txtsubject = '[Mozilla Hispano] Tienes %s tarea(s) caducada(s)'
        Tasks().send_tasks(txtmessage, txtsubject, condition)

    def taskthreedays(self):
        '''
        text for message and subject for tasks that mature in three days
        '''
        condition = [timedelta(days = 1), timedelta(days = 3)]
        txtmessage = u"Hola %s, \n\nActualmente tienes %s tarea(s) asignada(s) a ti que están a punto de caducar. \n"
        txtsubject = '[Mozilla Hispano] Tienes %s tareas a punto de caducar'
        Tasks().send_tasks(txtmessage, txtsubject, condition)

    def taskonday(self):
        '''
        text for message and subject for tasks that mature today
        '''
        condition = [timedelta(hours = 1), timedelta(hours = 24)]
        txtmessage = u"Hola %s, \n\nActualmente tienes %s tarea(s) asignada(s) a ti que caducan hoy. Por favor revisa su estado y actualizalas acordemente \n"
        txtsubject = '[Mozilla Hispano] Tienes %s tareas que caducan hoy'
        Tasks().send_tasks(txtmessage, txtsubject, condition)


# meetings reminder
class Meetings(object):
    def __init__(self):
        self.collab_new = {}
        collaborators(self.collab_new)
        json_meeting = urllib2.urlopen(MEETINGS_URL).read()
        self.meetings = json.loads(json_meeting)

    def meetingmail(self, txtmessage, txtsubject, json):
        try:
            address = json[1]
            text = txtmessage % (json[0],json[2],json[3],json[5],json[6])
            msg = MIMEText(unicode(text).encode('utf-8'))
            msg['Subject'] = txtsubject % unicode(json[4]).encode('utf-8')
            msg['From'] = MAIL_FROM
            msg['To'] = address
            msg.set_charset('utf-8')
            server = smtplib.SMTP(HOST)
            server.starttls()
            server.login(username,password)
            server.sendmail(MAIL_FROM, address, msg.as_string())
            server.quit
        except Exception:
            pass

    def separatemeetings(self, txtmessage, txtsubject, condition):
        for meeting in self.meetings['items']:
            fecha = meeting['fechainicio'][0]
            fecha = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
            if condition[0] < (fecha - datetime.now() + timedelta(hours = localtime)) <= condition[1]:
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
        Meetings().separatemeetings(txtmessage, txtsubject, condition)


    def meetingstoday(self):
        condition = [timedelta(hours = 2), timedelta(hours=3)]
        txtmessage = u"""Hola %s, \n\n Te recordamos que estas registrado para asistir a la reunión de %s, hoy %s. 
                      \n Puedes ver más información acerca de la reunión en: https://www.mozilla-hispano.org/documentacion/%s
                      \nRevisa tu hora local en http://www.timeanddate.com/worldclock/fixedtime.html?iso=%s"""
        txtsubject = '[MozillaHispano]Reunión de %s en unas horas'
        Meetings().separatemeetings(txtmessage,txtsubject,condition)
