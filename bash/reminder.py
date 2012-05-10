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
def mailstructure(self):
    x = [i for i in range(n)]
    ncolab = "colab['items']["+str(varl)+"]['label']"
    mcolab = "colab['items']["+str(varl)+"]['correo']"
    colab_new["name"] = ncolab
    colab_new["mail"] = mcolab
    b = json.dumps(colab_new)
    self.response.out.write(b)

# repeat this for all

#mailstructure(self,varl=0)

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
