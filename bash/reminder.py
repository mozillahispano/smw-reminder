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
    b = json.dumps({'name':ncolab,'mail':mcolab},sort_keys=True)
    print b

# In colab transform <xxx arroba xxx punto xx> in <xxx@xxx.xxx>

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
