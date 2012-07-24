#!/env/bin/python
# -*- coding: utf-8 -*-

import urllib2
import json
import smtplib
import string
from email.mime.text import MIMEText
from collections import defaultdict
from datetime import datetime, timedelta
from local_config import *

MAIL_FROM = 'tareas@mozhipano.com'
TASKS_URL = 'https://www.mozilla-hispano.org/documentacion/Especial:Ask/-5B-5BCategor%C3%ADa:Tarea-5D-5D-5B-5Bestado::!Finalizado-5D-5D/-3FResponsable%3DRespon./-3FArea/-3FProyecto/-3FEstado/-3FFechafin%3DL%C3%ADmite/mainlabel%3D/order%3DASC,ASC/sort%3DFechafin,Estado/format%3Djson/limit%3D1000'
COLLABORATORS_URL = 'https://www.mozilla-hispano.org/documentacion/Especial:Ask/-5B-5BCategoría:Colaborador-5D-5D/-3FCorreo/mainlabel%3D/format%3Djson/limit%3D1000'

'''
we get json from media wiki with this structure:
    colab['items'][n]['label']
    colab['items'][n]['correo']
but this is not usable and mails isn't in mail format, this is for solve that.
'''
json_collab = urllib2.urlopen(COLLABORATORS_URL).read()
collab = json.loads(json_collab)
n = len(collab["items"])
collab_new = {}

for var in range(n):
    '''
    for each collaborator we get a dictionary with collaborators name (ncollab) and collaborators mail (mcollab)
    '''
    ncollab = collab['items'][int(var)]['label']
    try:
        mcollab = collab['items'][int(var)]['correo']
    except KeyError:
        mcollab = "no tiene"
    '''
    for transform mcollab in mail format
    '''
    mcollab = [w.replace('ARROBA','@') for w in mcollab]
    mcollab = [w.replace('arroba','@') for w in mcollab]
    mcollab = [w.replace('AT','@') for w in mcollab]
    mcollab = [w.replace('PUNTO','.') for w in mcollab]
    mcollab = [w.replace('punto','.') for w in mcollab]
    mcollab = [w.replace('DOT','.') for w in mcollab]
    mcollab = [w.replace(' ','') for w in mcollab]
    collab_new.update({ncollab:mcollab})

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
n = len(tasks['items'])
tasks_onday = []
tasks_threedays = []
tasks_overdue =[]
for i in range(n):
    '''
    for each task
    '''
    try:
        l = len(tasks['items'][int(i)]['respon.'])
        for s in range(l):
   	    '''
	    and for each responsible in each task
   	    '''
            resp = tasks['items'][int(i)]['respon.'][s]
            try:
                resp1 = 'Usuario:'+resp
            except KeyError:
                resp1= "no user"
            try:
                mailresp = collab_new[resp1][0]
            except KeyError:
                mailresp="no mail"
            label = tasks['items'][int(i)]['label']
	    limit = tasks['items'][int(i)][u'límite'][0]
    	    '''
	    separate tasks according date limit
    	    '''
	    datelimit = datetime.strptime(limit, '%Y-%m-%d %H:%M:%S')
	    if timedelta (hours = 1) < (datelimit - datetime.now()) <= timedelta (hours = 24):
	        tasks_onday.append([resp,mailresp,label,limit])
	    elif timedelta (days = 1) < (datelimit -datetime.now()) <= timedelta (days = 3):
	        tasks_threedays.append([resp,mailreps,label,limit])
	    elif (datetime.now() - datelimit) > timedelta (hours = 1) :
                tasks_overdue.append([resp,mailresp,label,limit])
	    else:
	        pass
    except KeyError:
        pass

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
        TO = k[1]
        if (TO == 'no mail'):
            pass
        else:
            respon = k[0]
            numtasks = len(v)
            text = txtmessage % (respon, numtasks)
            for i in range(numtasks):
	        b = [w.replace(' ','_') for w in [v[int(i)]]]
                text = text + '\n' + v[int(i)] + ' https://www.mozilla-hispano.org/documentacion/'+ b[0]
	    text = text + '\n\nSaludos'
            msg = MIMEText(unicode(text).encode('utf-8'))
            msg['Subject'] = txtsubject % numtasks
            server = smtplib.SMTP(HOST)
            server.starttls()
            server.login(username,password)
            server.sendmail(MAIL_FROM, [TO], msg.as_string())
            server.quit()

def overdue():
    '''
    text for message and subject for overdue tasks
    '''
    tasks_new = tasks_overdue
    txtmessage = u"Hola %s, \n\nActualmente tienes %s tarea(s) asignada(s) a ti que están caducadas. Por favor revisa su estado y marcalas como finalizadas o amplia su fecha límite \n"
    txtsubject = '[Mozilla Hispano] Tienes %s tareas caducadas'
    send_mail(txtmessage, txtsubject, tasks_new)

def threedays():
    '''
    text for message and subject for tasks that mature in three days
    '''
    tasks_new = tasks_threedays
    txtmessage = u"Hola %s, \n\nActualmente tienes %s tarea(s) asignada(s) a ti que están a punto de caducar. \n"
    txtsubject = '[Mozilla Hispano] Tienes %s tareas a punto de caducar'
    send_mail(txtmessage, txtsubject,tasks_new)

def onday():
    '''
    text for message and subject for tasks that mature today
    '''
    tasks_new = tasks_onday
    txtmessage = u"Hola %s, \n\nActualmente tienes %s tarea(s) asignada(s) a ti que caducan hoy. Por favor revisa su estado y actualizalas acordemente \n"
    txtsubject = '[Mozilla Hispano] Tienes %s tareas que caducan hoy'
    send_mail(txtmessage, txtsubject, tasks_new)
    
overdue()
threedays()
onday()
