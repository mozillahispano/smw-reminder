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

json_tasks = urllib2.urlopen('https://www.mozilla-hispano.org/documentacion/Especial:Ask/-5B-5BCategor%C3%ADa:Tarea-5D-5D-5B-5Bestado::!Finalizado-5D-5D/-3FResponsable%3DRespon./-3FArea/-3FProyecto/-3FEstado/-3FFechafin%3DL%C3%ADmite/mainlabel%3D/order%3DASC,ASC/sort%3DFechafin,Estado/format%3Djson/limit%3D1000').read()
tasks = json.loads(json_tasks)
json_collab = urllib2.urlopen('https://www.mozilla-hispano.org/documentacion/Especial:Ask/-5B-5BCategoría:Colaborador-5D-5D/-3FCorreo/mainlabel%3D/format%3Djson/limit%3D1000').read()
collab = json.loads(json_collab)

# jsons structures
# tareas['items'][0]['respon.']
# colab['items'][0]['label']
# colab['items'][0]['correo']

# transform list in dictionary

n = len(collab["items"])
collab_new = {}

for var in range(n):
    ncollab = collab['items'][int(var)]['label']
    try:
        mcollab = collab['items'][int(var)]['correo']
    except KeyError:
        mcollab = "no tiene"
    mcollab = [w.replace('ARROBA','@') for w in mcollab]
    mcollab = [w.replace('arroba','@') for w in mcollab]
    mcollab = [w.replace('AT','@') for w in mcollab]
    mcollab = [w.replace('PUNTO','.') for w in mcollab]
    mcollab = [w.replace('punto','.') for w in mcollab]
    mcollab = [w.replace('DOT','.') for w in mcollab]
    mcollab = [w.replace(' ','') for w in mcollab]
    collab_new.update({ncollab:mcollab})

# append mails with tareas respons (new file)
n = len(tasks['items'])
tasks_onday = []
tasks_treedays = []
tasks_overdue =[]
for i in range(n):
    try:
        l = len(tasks['items'][int(i)]['respon.'])
        for s in range(l):
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
	    datelimit = datetime.strptime(limit, '%Y-%m-%d %H:%M:%S')
	    if (datelimit - datetime.now()) == timedelta (hours = 1):
	        tasks_onday.append([resp,mailresp,label,limit])
	    elif (datelimit -datetime.now()) == timedelta (days = 3):
	        tasks_treedays.append([resp,mailreps,label,limit])
	    elif (datetime.now() - datelimit) > timedelta (hours = 1) :
                tasks_overdue.append([resp,mailresp,label,limit])
	    else:
	        pass
    except KeyError:
        pass


# send mails
FROM = "tareas@mozhipano.com"

def send_mail(txtmessage, txtsubject, tasks_new):
    d = defaultdict(list)
    for k,v,p,m in tasks_new:
        d[k,v].append(p)
    for k,v in d.items():
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
            server.sendmail(FROM, [TO], msg.as_string())
            server.quit()

def overdue():
    tasks_new = tasks_overdue
    txtmessage = u"Hola %s, \n\nActualmente tienes %s tarea(s) asignada(s) a ti que están caducadas. Por favor revisa su estado y marcalas como finalizadas o amplia su fecha límite \n"
    txtsubject = '[Mozilla Hispano] Tienes %s tareas caducadas'
    send_mail(txtmessage, txtsubject, tasks_new)

def treedays():
    tasks_new = tasks_treedays
    txtmessage = u"Hola %s, \n\nActualmente tienes %s tarea(s) asignada(s) a ti que están a punto de caducar. \n"
    txtsubject = '[Mozilla Hispano] Tienes %s tareas a punto de caducar'
    send_mail(txtmessage, txtsubject,tasks_new)

def onday():
    tasks_new = tasks_onday
    txtmessage = u"Hola %s, \n\nActualmente tienes %s tarea(s) asignada(s) a ti que caducan hoy. Por favor revisa su estado y actualizalas acordemente \n"
    txtsubject = '[Mozilla Hispano] Tienes %s tareas que caducan hoy'
    send_mail(txtmessage, txtsubject, tasks_new)
    
overdue()
treedays()
onday()
