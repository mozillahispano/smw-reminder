#!/env/bin/python
# -*- coding: utf-8 -*-

import urllib2
import json
from collections import defaultdict

json_tasks = urllib2.urlopen('https://www.mozilla-hispano.org/documentacion/Especial:Ask/-5B-5BCategor%C3%ADa:Tarea-5D-5D-5B-5Bestado::!Finalizado-5D-5D/-3FResponsable%3DRespon./-3FArea/-3FProyecto/-3FEstado/-3FFechafin%3DL%C3%ADmite/mainlabel%3D/order%3DASC,ASC/sort%3DFechafin,Estado/format%3Djson/limit%3D1000').read()
tasks = json.loads(json_tasks)
json_colab = urllib2.urlopen('https://www.mozilla-hispano.org/documentacion/Especial:Ask/-5B-5BCategoría:Colaborador-5D-5D/-3FCorreo/mainlabel%3D/format%3Djson/limit%3D1000').read()
colab = json.loads(json_colab)
n = len(colab["items"])

# jsons structures
# tareas['items'][0]['respon.']
# colab['items'][0]['label']
# colab['items'][0]['correo']

# transform list in dictionary

colab_new = {}

for var in range(n):
    ncolab = colab['items'][int(var)]['label']
    try:
        mcolab = colab['items'][int(var)]['correo']
    except KeyError:
        mcolab = "no tiene"
    mcolab = [w.replace('ARROBA','@') for w in mcolab]
    mcolab = [w.replace('arroba','@') for w in mcolab]
    mcolab = [w.replace('AT','@') for w in mcolab]
    mcolab = [w.replace('PUNTO','.') for w in mcolab]
    mcolab = [w.replace('punto','.') for w in mcolab]
    mcolab = [w.replace('DOT','.') for w in mcolab]
    mcolab = [w.replace(' ','') for w in mcolab]
    colab_new.update({ncolab:mcolab})

# append mails with tareas respons (new file)
n = len(tasks['items'])

tasks_new = []
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
                mailresp = colab_new[resp1][0]
            except KeyError:
                mailresp="no mail"
            label = tasks['items'][int(i)]['label']
            tasks_new.append([resp,mailresp,label])
    except KeyError:
        pass

d = defaultdict(list)
for k,v,p in tasks_new:
    d[k,v].append(p)

# send mails
import smtplib
import string
from email.mime.text import MIMEText

FROM = "tareas@mozhipano.com"
HOST =  # 'mailserver:port'
username = # 'username'
password = # 'password'

for k,v in d.items():
    TO = k[1]
    if (TO == 'no mail'):
        pass
    else:
        respon = k[0]
        numtasks = len(v)
        text = u"Hola %s, \n\nActualmente tienes %s tarea(s) asignada(s) a ti que están caducadas. Por favor revisa su estado y marcalas como finalizadas o amplia su fecha límite \n" % (respon, numtasks)
        for i in range(numtasks):
	    b = [w.replace(' ','_') for w in [v[int(i)]]]
            text = text + '\n' + v[int(i)] + ' https://www.mozilla-hispano.org/documentacion/'+ b[0]
	text = text + '\n\nSaludos'
        msg = MIMEText(unicode(text).encode('utf-8'))
        msg['Subject'] = '[Mozilla Hispano] Tienes %s tareas caducadas' % numtasks
        server = smtplib.SMTP(HOST)
        server.starttls()
        server.login(username,password)
        server.sendmail(FROM, [TO], msg.as_string())
        server.quit()
