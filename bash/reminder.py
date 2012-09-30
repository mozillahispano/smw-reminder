#!/env/bin/python
# -*- coding: utf-8 -*-

import urllib
import urllib2
import json
import smtplib
import string
import re
import argparse
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

def convertToEmailAddress(emailString):
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
    but this is not usable and mails isn't in mail format, this is for solve that.
    '''
    json_collab = urllib2.urlopen(COLLABORATORS_URL).read()
    collab = json.loads(json_collab)
    n = len(collab["items"])

    for var in range(n):
        '''
        for each collaborator we get a dictionary with collaborators name (ncollab) and collaborators mail (mcollab)
        '''
        ncollab = collab['items'][int(var)]['label']
        try:
            mcollab = convertToEmailAddress(collab['items'][int(var)]['correo'][0])
        except KeyError:
            mcollab = ''

        collab_new.update({ncollab:mcollab})
    return collab_new

def getTasks():
    '''
    Like json collab, tasks json structure is:
        tasks['items'][n]['respon.']
        tasks['items'][n]['label']
        tasks['items'][n][u'límite']
    this is to append collaborator mail with this data and separate tasks according to date limit: if is overdue (tasks_overdue),
    that mature in three days (tasks_threedays) and that mature today (tasks_onday)
    '''
    json_tasks = urllib2.urlopen(TASKS_URL).read()
    tasks = json.loads(json_tasks)
    tasks_onday = []
    tasks_threedays = []
    tasks_overdue =[]
    collab_new = {}
    collaborators(collab_new)

    for task in tasks['items']:
        dueToday = False
        dueInThreeDays = False
        overdue = False
        # Get the date limit and figure out if we need to do anything.
        if u'límite' in task:
            limit = task[u'límite'][0]
            datelimit = datetime.strptime(limit, '%Y-%m-%d %H:%M:%S')
            if timedelta(hours = 1) < (datelimit - datetime.now()) <= timedelta(hours = 24):
                dueToday = True
            elif timedelta(days = 1) < (datelimit -datetime.now()) <= timedelta(days = 3):
                dueInThreeDays = True
            elif (datetime.now() - datelimit) > timedelta (hours = 1) :
                overdue = True
        # Figure out who to send the message to.
        if (dueToday or dueInThreeDays or overdue):
            assignees = []
            # Get assignees from task.
            if 'respon.' in task:
                for user in task['respon.']:
                    userString = 'Usuario:' + user
                    if userString in collab_new:
                        assignees.append(user)
            # If there are none, get area owners.
            if len(assignees) == 0:
                if 'area' in task:
                    assignees = getAreaOwners(task['area'][0],collab_new)
                if len(assignees) == 0:
                    print 'Due task "' + task['label'] + '" has no one responsible for it.'
            for assignee in assignees:
                email = collab_new['Usuario:' + assignee]
                if dueToday:
                    tasks_onday.append([assignee, email, task['label'], limit])
                elif dueInThreeDays:
                    tasks_threedays.append([assignee, email, task['label'], limit])
                elif overdue:
                    tasks_overdue.append([assignee, email, task['label'], limit])
    taskoverdue(tasks_overdue)
    taskthreedays(tasks_threedays)
    taskonday(tasks_onday)

def send_mail(txtmessage, txtsubject, tasks_new):
    '''
    send mails for each collaborator
    '''
    d = defaultdict(list)
    for resp,mailresp,label,limit in tasks_new:
        '''
    	for order tasks (label) for each collaborator, result a dict with 2 items
        '''
        d[resp,mailresp].append(label)
    for k,v in d.items():
        '''
	lines before, we get a dict (d) with 2 items. Now I parse this items (k,v) in mail message
        '''
        toAddress = k[1]

        if (toAddress != ''):
            try:
                respon = k[0]
                numtasks = len(v)
                text = txtmessage % (respon, numtasks)
                for i in range(numtasks):
                    b = [w.replace(' ','_') for w in [v[int(i)]]]
                    text = text + '\n' + v[int(i)] + 'https://www.mozilla-hispano.org/documentacion/'+ b[0]
                text = text + '\n\nSaludos'
                msg = MIMEText(unicode(text).encode('utf-8'))
                msg['Subject'] = txtsubject % numtasks
                msg['From'] = MAIL_FROM
                msg['To'] = toAddress
                msg.set_charset('utf-8')
                server = smtplib.SMTP(HOST)
                server.starttls()
                server.login(username,password)
                server.sendmail(MAIL_FROM, toAddress, msg.as_string())
                server.quit()
            except Exception:
                pass
        else:
            # TODO: show a 'no email address for user X' error.
            pass

def taskoverdue(tasks_overdue):
    '''
    text for message and subject for overdue tasks
    '''
    tasks_new = tasks_overdue
    txtmessage = u"Hola %s, \n\nActualmente tienes %s tarea(s) asignada(s) a ti que están caducadas. Por favor revisa su estado y marcalas como finalizadas o amplia su fecha límite \n"
    txtsubject = '[Mozilla Hispano] Tienes %s tareas caducadas'
    send_mail(txtmessage, txtsubject, tasks_new)

def taskthreedays(tasks_threedays):
    '''
    text for message and subject for tasks that mature in three days
    '''
    tasks_new = tasks_threedays
    txtmessage = u"Hola %s, \n\nActualmente tienes %s tarea(s) asignada(s) a ti que están a punto de caducar. \n"
    txtsubject = '[Mozilla Hispano] Tienes %s tareas a punto de caducar'
    send_mail(txtmessage, txtsubject,tasks_new)

def taskonday(tasks_onday):
    '''
    text for message and subject for tasks that mature today
    '''
    tasks_new = tasks_onday
    txtmessage = u"Hola %s, \n\nActualmente tienes %s tarea(s) asignada(s) a ti que caducan hoy. Por favor revisa su estado y actualizalas acordemente \n"
    txtsubject = '[Mozilla Hispano] Tienes %s tareas que caducan hoy'
    send_mail(txtmessage, txtsubject, tasks_new)

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
            text = txtmessage % (json[0],json[2],json[3])
            msg = MIMEText(unicode(text).encode('utf-8'))
            msg['Subject'] = txtsubject % unicode(json[2]).encode('utf-8')
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

    def meetingsthreedays(self):
        for meeting in self.meetings['items']:
            fecha = meeting['fechainicio'][0]
            fecha = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
            if timedelta(days = 2) < (fecha - datetime.now()) <= timedelta(days=3):
                for user in meeting['asistentes']:
                    email = self.collab_new['Usuario:' + user]
                    meeting_three_days = []
                    try:
                        meeting_three_days.append([user, email, meeting['proyecto'][0],meeting['fechainicio'][0]])
                    except KeyError:
                        meeting_three_days.append([user, email, meeting['label'],meeting['fechainicio'][0]])
                    meeting_three_days = meeting_three_days[0]
                    txtmessage = u"""Hola %s, \n\n Te recordamos que estas registrado para asistir a la reunión de %s, a las %s.
                                  \n Puedes ver más información acerca de la reunión en: https://www.mozilla-hispano.org/documentacion/""" + meeting['label']
                    txtsubject = '[MozillaHispano]Reunión de %s en unos días'
                    Meetings().meetingmail(txtmessage,txtsubject,meeting_three_days)

    def meetingstoday(self):
        for meeting in self.meetings['items']:
            fecha = meeting['fechainicio'][0]
            fecha = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
            if timedelta(hours = 2) < (fecha - datetime.now()) <= timedelta(hours=3):
                for user in meeting['asistentes']:
                    email = self.collab_new['Usuario:' + user]
                    meeting_today = []
                    try:
                        meeting_today.append([user, email, meeting['proyecto'][0],meeting['fechainicio'][0]])
                    except KeyError:
                        meeting_today.append([user, email, meeting['label'],meeting['fechainicio'][0]])
                    meeting_today = meeting_today[0]
                    txtmessage = u"""Hola %s, \n\n Te recordamos que estas registrado para asistir a la reunión de %s, a las %s. 
                                  \n Puedes ver más información acerca de la reunión en: https://www.mozilla-hispano.org/documentacion/""" + meeting['label']
                    txtsubject = '[MozillaHispano]Reunión de %s en unas horas'
                    Meetings().meetingmail(txtmessage,txtsubject,meeting_today)

def tasks(parsed_args):
    getTasks()

def meeting_threedays(parsed_args):
    Meetings().meetingsthreedays()

def meeting_today(parsed_args):
    Meetings().meetingstoday()

parser=argparse.ArgumentParser()
parser.add_argument('--tasks', dest='action', action='store_const', const=tasks, help='reminder for tasks')
parser.add_argument('--meetings-threedays', dest='action', action='store_const', const=meeting_threedays, help='reminder for meetings into three days')
parser.add_argument('--meetings-today', dest='action', action='store_const', const=meeting_today, help= 'reminder for meetings today')
parsed_args = parser.parse_args()
if parsed_args.action is None:
    parser.parse_args(['-h'])
parsed_args.action(parsed_args)
