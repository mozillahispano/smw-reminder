import reminder
import argparse

def tasks(parsed_args):
    reminder.Tasks().taskoverdue()
    reminder.Tasks().taskthreedays()
    reminder.Tasks().taskonday()

def meeting_threedays(parsed_args):
    reminder.Meetings().meetingsthreedays()

def meeting_today(parsed_args):
    reminder.Meetings().meetingstoday()

parser=argparse.ArgumentParser()

parser.add_argument('--tasks',
                    dest='action',
                    action='store_const',
                    const=tasks,
                    help='reminder for tasks')

parser.add_argument('--meetings-threedays',
                    dest='action',
                    action='store_const',
                    const=meeting_threedays,
                    help='reminder for meetings into three days')

parser.add_argument('--meetings-today',
                    dest='action',
                    action='store_const',
                    const=meeting_today,
                    help= 'reminder for meetings today')

parsed_args = parser.parse_args()

if parsed_args.action is None:
    parser.parse_args(['-h'])
parsed_args.action(parsed_args)
