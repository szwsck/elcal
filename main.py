#!/usr/bin/env python3
from __future__ import print_function

import json
from datetime import datetime as dt

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ACL_RULE_PUBLIC = {'scope': {'type': 'default'}, 'role': 'reader'}
SCOPES = ['https://www.googleapis.com/auth/calendar']

creds = Credentials.from_authorized_user_file('token.json', SCOPES)
if creds.expired:
    creds.refresh(Request())
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
service = build('calendar', 'v3', credentials=creds)
semester = json.load(open('semester.json', 'rb'))


def get_datetime_obj(weekday, week, time):
    date = dt.strptime(semester['plan'][weekday][week], '%Y-%m-%d').date()
    datetime = dt.combine(date, time)
    return {'timeZone': "Europe/Warsaw", 'dateTime': datetime.isoformat()}


def get_event_body(course):
    start_time = dt.strptime(course['start_time'], "%H:%M").time()
    end_time = dt.strptime(course['start_time'], "%H:%M").time()

    recurrence_date_strs = [
        dt.combine(
            dt.strptime(semester['plan'][course['weekday']][week], '%Y-%m-%d'),
            start_time
        ).strftime("%Y%m%dT%H%M%S")
        for week in course['weeks'][1:]
    ]
    recurrence_rule = f"RDATE;VALUE=DATE:{','.join(recurrence_date_strs)}"

    return {
        'summary': course['name'],
        'start': get_datetime_obj(course['weekday'], course['weeks'][0], start_time),
        'end': get_datetime_obj(course['weekday'], course['weeks'][0], end_time),
        'recurrence': [recurrence_rule]
    }


def get_calendars():
    all_calendars = service.calendarList().list().execute()['items']
    return list(filter(lambda c: 'primary' not in c and c['accessRole'] == 'owner', all_calendars))


def create_calendar(course):
    print(f"Creating calendar {course}")
    calendar_body = {'summary': course['name'], 'description': json.dumps(course)}
    calendar = service.calendars().insert(body=calendar_body).execute()
    service.acl().insert(calendarId=calendar['id'], body=ACL_RULE_PUBLIC).execute()

    service.events().insert(calendarId=calendar['id'], body=get_event_body(course)).execute()

    return calendar


def delete_calendar(calendar):
    print(f"Deleting calendar {calendar}")
    service.calendars().delete(calendarId=calendar['id']).execute()


def update_calendar(calendar, course):
    print(f"Updating calendar {course}")

    calendar_body = {'summary': course['name'], 'description': json.dumps(course)}
    service.calendars().update(calendarId=calendar['id'], body=calendar_body).execute()

    event = service.events().list(calendarId=calendar['id']).execute()['items'][0]
    service.events().update(calendarId=calendar['id'], eventId=event['id'], body=get_event_body(course)).execute()


def main():
    courses = semester['courses']
    calendars = get_calendars()

    print(calendars)
    print(courses)

    for course in courses:
        existing_calendar = next(filter(lambda calendar: get_course(calendar)['id'] == course['id'], calendars), None)
        if existing_calendar:
            if course == get_course(existing_calendar):
                # course already added
                print(f"{course['name']} is up to date")
            else:
                # update calendar to match course
                print(f"{course['name']} needs update")
                update_calendar(existing_calendar, course)
        else:
            print(f"{course['name']} is missing")
            create_calendar(course)

    for calendar in calendars:
        existing_course = next(filter(lambda course: course['id'] == get_course(calendar)['id'], courses), None)
        if not existing_course:
            print(f"Calendar no longer needed, deleting: {calendar}")
            delete_calendar(calendar)


def get_course(cal):
    return json.loads(cal['description'])


if __name__ == '__main__':
    main()
