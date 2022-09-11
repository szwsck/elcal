#!/usr/bin/env python3
import base64
import json
from datetime import datetime as dt

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TIME_FMT = "%H:%M"
DATE_FMT = '%Y-%m-%d'
RECURRENCE_DATETIME_FMT = "%Y%m%dT%H%M%S"
TIMEZONE = "Europe/Warsaw"
ACL_RULE_PUBLIC = {'scope': {'type': 'default'}, 'role': 'reader'}
SCOPES = ['https://www.googleapis.com/auth/calendar']
COURSE_TYPE_NAMES = {
    'lecture': 'Wykład',
    'project': 'Projekt',
    'tutorial': 'Ćwiczenia',
    'laboratory': 'Laboratorium',
}
COURSE_TYPE_COLORS = {
    'lecture': '12',
    'project': '15',
    'tutorial': '2',
    'laboratory': '6',
}

creds = Credentials.from_authorized_user_file('token.json', SCOPES)
if creds.expired:
    creds.refresh(Request())
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

service = build('calendar', 'v3', credentials=creds)
semester = json.load(open('semester.json', 'rb'))


def create_datetime_obj(weekday, week, time):
    date = dt.strptime(semester['schedule'][weekday][week], DATE_FMT).date()
    datetime = dt.combine(date, time)
    return {'timeZone': TIMEZONE, 'dateTime': datetime.isoformat()}


def create_calendar_body(course):
    return {
        'summary': create_title(course),
        'description': json.dumps(course)
    }


def create_event_body(course):
    start_time = dt.strptime(course['start_time'], TIME_FMT).time()
    end_time = dt.strptime(course['end_time'], TIME_FMT).time()

    recurrence_date_strs = [
        dt.combine(
            dt.strptime(semester['schedule'][course['weekday']][week], DATE_FMT),
            start_time
        ).strftime(RECURRENCE_DATETIME_FMT)
        for week in course['weeks'][1:]
    ]
    recurrence_rule = f"RDATE;VALUE=DATE:{','.join(recurrence_date_strs)}"

    return {
        'summary': create_title(course),
        'description': create_description(course),
        'start': create_datetime_obj(course['weekday'], course['weeks'][0], start_time),
        'end': create_datetime_obj(course['weekday'], course['weeks'][0], end_time),
        'recurrence': [recurrence_rule],
        'location': course['location']
    }


def create_link(calendar):
    cid = base64.b64encode(calendar['id'].encode('utf-8')).decode().rstrip('=')
    return f"https://calendar.google.com/calendar/u/0?cid={cid}"


def get_course(calendar):
    return json.loads(calendar['description'])


def create_title(course):
    title = f"{course['name']} - {COURSE_TYPE_NAMES[course['type']]}"
    if 'group' in course:
        title += f" gr. {course['group']}"
    return title


def create_description(course):
    if 'instructor' in course:
        return f"Prowadzący: {course['instructor']}"
    else:
        return ""


def list_calendars():
    all_calendars = service.calendarList().list().execute()['items']
    return list(filter(lambda c: 'primary' not in c and c['accessRole'] == 'owner', all_calendars))


def create_calendar(course):
    print(f"Creating calendar for {create_title(course)}")
    calendar = service.calendars().insert(body=create_calendar_body(course)).execute()
    service.calendarList().patch(calendarId=calendar['id'], body={
        'colorId': COURSE_TYPE_COLORS[course['type']]
    }).execute()
    service.acl().insert(calendarId=calendar['id'], body=ACL_RULE_PUBLIC).execute()
    service.events().insert(calendarId=calendar['id'], body=create_event_body(course)).execute()
    return calendar


def delete_calendar(calendar):
    print(f"Deleting calendar {calendar['id']}")
    service.calendars().delete(calendarId=calendar['id']).execute()


def update_calendar(calendar, course):
    print(f"Updating calendar {course['id']}")

    calendar_body = {'summary': create_title(course), 'description': json.dumps(course)}
    service.calendars().update(calendarId=calendar['id'], body=calendar_body).execute()
    service.calendarList().patch(calendarId=calendar['id'], body={
        'colorId': COURSE_TYPE_COLORS[course['type']]
    }).execute()
    event = service.events().list(calendarId=calendar['id']).execute()['items'][0]
    service.events().update(calendarId=calendar['id'], eventId=event['id'], body=create_event_body(course)).execute()


def main():
    courses = semester['courses']
    calendars = list_calendars()

    for course in courses:
        existing_calendar = next(filter(lambda calendar: get_course(calendar)['id'] == course['id'], calendars), None)
        if not existing_calendar:
            print(f'Course missing: {course["name"]}')
            create_calendar(course)
        elif course != get_course(existing_calendar):
            print(f'Needs update: {course["name"]}')
            update_calendar(existing_calendar, course)
        else:
            print(f'Up to date: {course["name"]}')

    for calendar in calendars:
        existing_course = next(filter(lambda course: course['id'] == get_course(calendar)['id'], courses), None)
        if not existing_course:
            print(f"Calendar no longer needed, deleting: {get_course(calendar)['name']}")
            delete_calendar(calendar)

    for calendar in list_calendars():
        print(f"{create_title(get_course(calendar))}: {create_link(calendar)}")


if __name__ == '__main__':
    main()
