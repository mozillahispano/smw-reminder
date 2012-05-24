#!/env/bin/python

# load jsons
import json
json_tareas = open('tareas.json').read()
tareas = json.loads(json_tareas)
json_colab = open('colaboradores.json').read()
colab = json.loads(json_colab)
n = len(colab["items"])

# jsons structures
# tareas['items'][0]['respon.']
# colab['items'][0]['label']
# colab['items'][0]['correo']

# transform list in dictionary

colab_new = {}

vars = [i for i in range(n)]
for var in vars:
    ncolab = colab['items'][int(var)]['label']
    try:
        mcolab = colab['items'][int(var)]['correo']
    except KeyError:
        mcolab = "no tiene"
    mcolab = [w.replace('ARROBA','@') for w in mcolab]
    mcolab = [w.replace('arroba','@') for w in mcolab]
    mcolab = [w.replace('PUNTO','.') for w in mcolab]
    mcolab = [w.replace('punto','.') for w in mcolab]
    mcolab = [w.replace(' ','') for w in mcolab]
    colab_new.update({ncolab:mcolab})

# append mails with tareas respons (new file)

# send mails
'''
import smtplib
import string
 
SUBJECT = "You have a task pending"
TO = ""
FROM = "mail@mydomain.com"
text = ""
HOST = 
BODY = string.join((
        "From: %s" % FROM,
        "To: %s" % TO,
        "Subject: %s" % SUBJECT ,
        "",
        text
        ), "\r\n")
server = smtplib.SMTP(HOST)
server.sendmail(FROM, [TO], BODY)
server.quit()
'''
