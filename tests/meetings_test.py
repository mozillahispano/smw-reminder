import pytest
import unittest

from datetime import datetime, timedelta
from reminder.meetings import Meetings

class MeetingsTest(unittest.TestCase):
    def setUp(self):
        self.collab_new = {'Usuario:user0':'mail@example.com'}
        self.meetings_json = {'items': [{'asistentes':['user0'],
                                        'area': ['area'],
                                        'fechainicio': ['2013-06-23 23:50:00'],
                                        'label': 'label'}]}

    def test_append_json(self):
        user = 'user0'
        meeting = self.meetings_json['items'][0]
        fecha = meeting['fechainicio'][0]
        fecha = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
        json = []
        expected = [[user, 'mail@example.com','area', 
                    '23 de Jun a las 23:50 UTC', 'area', 'label',
                    '20130623T2350']]
        assert Meetings().append_json(self.collab_new, user, meeting, fecha, json) == expected

    def test_meeting_mail_fail(self):
        message = 'message'
        subject = 'subject'
        json = [['user1', '','area', 
                    '23 de Jun a las 23:50 UTC', 'area', 'label',
                    '20130623T2350']]
        #expected = {'user user1 dont have mail'}
        expected = None
        assert Meetings().meeting_mail(message, subject, json) == expected
