import pytest
import unittest

from reminder.reminder import Base
from reminder.tasks import Tasks
from datetime import datetime, timedelta

def test_convert_to_email_0():
    ''' Should convert string in valid email '''
    email = 'cesar ARROBA mozilla DOT pe'
    assert Base().convert_to_email(email) == 'cesar@mozilla.pe'

def test_convert_to_email_1():
    ''' Should convert string in valid email '''
    email = 'cesar AT mozilla punto pe'
    assert Base().convert_to_email(email) == 'cesar@mozilla.pe'

def test_get_collaborators_0():
    ''' Should return dict (name:mail) '''
    json0 = {u'items':[{u'correo': [u'cesar @ mozilla DOT pe'],
                       u'label': u'Usuario:ccarruitero'}],
            u'properties': {u'correo': {u'valueType': u'text'}}}
    collab_new = {}
    expected = {u'Usuario:ccarruitero': u'cesar@mozilla.pe'}
    assert Base().get_collab(json0, collab_new) == expected

def test_get_collaborators_1():
    ''' Should return dict (name:mail) '''
    json0 = {u'items':[{u'correo': [u'name @ domain DOT com'],
                       u'label': u'Usuario:user0'},
                       {u'correo':[u'another@mail.com'],
                       u'label': u'Usuario:user1'}],
            u'properties': {u'correo': {u'valueType': u'text'}}}
    collab_new = {}
    expected = {u'Usuario:user0': u'name@domain.com',
                u'Usuario:user1': u'another@mail.com'}
    assert Base().get_collab(json0, collab_new) == expected

class TasksTest(unittest.TestCase):
    def setUp(self):
        self.collab = {u'Usuario:user0':u'mail@example.com'}

    def test_getTasks(self):
        ''' should return json with tasks, assignees, email from assignees and
        limit time declared '''
        tasks = {u'items':[{u'l\xedmite': [u'2012-01-01 00:00:00'], u'area': [u'Area'],u'estado': [u'No iniciado'],u'label': u'una tarea',u'respon.':[u'user0']}], u'properties': {u'proyecto': {u'valueType': u'text'}, u'respon.': {u'valueType': u'text'}, u'estado': {u'valueType': u'text'}, u'l\xedmite': {u'valueType': u'date'}, u'area': {u'valueType': u'text'}}}
        tasks_json = []
        expected = [[u'user0', u'mail@example.com', u'una tarea', u'2012-01-01 00:00:00']]
        condition = [timedelta(weeks = -1000), timedelta(hours = 0)]
        assert Tasks().getTasks(condition, tasks, tasks_json, self.collab) == expected

    def test_get_assignees(self):
        task = {u'respon.':[u'user0']}
        assignees = []
        expected = [u'user0']
        assert Tasks().get_assignees(task, self.collab, assignees) == expected
