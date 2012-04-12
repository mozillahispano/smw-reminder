#!/env/bin/python

# load jsons
import json
json_tareas = open('tareas.json').read()
tareas = json.loads(json_tareas)
json_colab = open('colaboradores.json').read()
colab = json.loads(json_colab)
n = len(tareas["items"])

# append mails with tareas respons

# send mails
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
