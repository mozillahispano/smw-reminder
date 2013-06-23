#!/env/bin/python
# -*- coding: utf-8 -*-
import requests
import smtplib
import pdb
import local_config as config
from reminder import Base
from datetime import datetime, timedelta
from collections import defaultdict
from email.mime.text import MIMEText

TASKS_URL = 'https://www.mozilla-hispano.org/documentacion/Especial:Ask/-5B-5BCategor%C3%ADa:Tarea-5D-5D-5B-5Bestado::!Finalizado-5D-5D/-3FResponsable%3DRespon./-3FArea/-3FProyecto/-3FEstado/-3FFechafin%3DL%C3%ADmite/mainlabel%3D/order%3DASC,ASC/sort%3DFechafin,Estado/format%3Djson/limit%3D1000'

class Tasks(Base):
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
        Base().collaborators(self.collab_new)
        self.tasks = requests.get(TASKS_URL).json()

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
                        self.get_assignees(task, collab, assignees)
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
            msg['From'] = config.MAIL_FROM
            msg['To'] = k[1]
            msg.set_charset('utf-8')
            server = smtplib.SMTP(config.HOST)
            server.starttls()
            server.login(config.username,config.password)
            server.sendmail(config.MAIL_FROM, k[1], msg.as_string())
            server.quit()
        except Exception:
            pass

    def send_mail(self, txtmessage, txtsubject, tasks_json):
        '''
        send mails for each collaborator
        '''
        d = defaultdict(list)
        for resp,mailresp,label,limit in tasks_json:
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
                self.tasksmail(txtmessage, txtsubject, k,v)
            else:
                # TODO: show a 'no email address for user X' error.
                pass

    def send_tasks(self, txtmessage, txtsubject, condition):
        tasks_json = []
        self.getTasks(condition, self.tasks, tasks_json, self.collab_new)
        self.send_mail(txtmessage, txtsubject, tasks_json)

    def taskoverdue(self):
        '''
        text for message and subject for overdue tasks
        '''
        condition = [timedelta(weeks = -1000), timedelta(hours = 0)]
        txtmessage = u"Hola %s, \n\nActualmente tienes %s tarea(s) asignada(s) a ti que están caducadas. Por favor revisa su estado y marcalas como finalizadas o amplia su fecha límite \n"
        txtsubject = '[Mozilla Hispano] Tienes %s tarea(s) caducada(s)'
        self.send_tasks(txtmessage, txtsubject, condition)

    def taskthreedays(self):
        '''
        text for message and subject for tasks that mature in three days
        '''
        condition = [timedelta(days = 1), timedelta(days = 3)]
        txtmessage = u"Hola %s, \n\nActualmente tienes %s tarea(s) asignada(s) a ti que están a punto de caducar. \n"
        txtsubject = '[Mozilla Hispano] Tienes %s tareas a punto de caducar'
        self.send_tasks(txtmessage, txtsubject, condition)

    def taskonday(self):
        '''
        text for message and subject for tasks that mature today
        '''
        condition = [timedelta(hours = 1), timedelta(hours = 24)]
        txtmessage = u"Hola %s, \n\nActualmente tienes %s tarea(s) asignada(s) a ti que caducan hoy. Por favor revisa su estado y actualizalas acordemente \n"
        txtsubject = '[Mozilla Hispano] Tienes %s tareas que caducan hoy'
        self.send_tasks(txtmessage, txtsubject, condition)
