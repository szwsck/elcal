import base64
from dataclasses import dataclass, field
from typing import Optional
import datetime as dt

from dataclasses_json import dataclass_json, config, LetterCase

from courses import Course
from google_api import gcal

TIME_FMT = '%H:%M'
DATE_FMT = '%Y-%m-%d'
RECURRENCE_DATETIME_FMT = '%Y%m%dT%H%M%S'
TIMEZONE = 'Europe/Warsaw'
ACL_RULE_PUBLIC = {'scope': {'type': 'default'}, 'role': 'reader'}


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Datetime:
    time_zone: str
    date_time: dt.datetime = field(metadata=config(encoder=dt.datetime.isoformat))


@dataclass_json
@dataclass
class Calendar:
    summary: str
    course: Course = field(metadata=config(
        field_name='description',
        encoder=Course.to_json,
        decoder=Course.from_json
    ))
    id: Optional[str] = None

    @classmethod
    def from_course(cls, course: Course):
        return cls(
            course.get_title(),
            course
        )

    def get_link(self):
        cid = base64.b64encode(self.id.encode('utf-8')).decode().rstrip('=')
        return f"https://calendar.google.com/calendar/u/0?cid={cid}"


@dataclass_json
@dataclass
class Event:
    summary: str
    description: str
    start: Datetime
    end: Datetime
    recurrence: list[str]
    location: str
    id: Optional[str] = None

    @classmethod
    def from_course(cls, course: Course, schedule: list[list[dt.date]]):
        recurrence = 'RDATE;VALUE=DATE:' + ','.join(
            dt.datetime.combine(schedule[course.weekday][week], course.start_time).strftime(RECURRENCE_DATETIME_FMT)
            for week in course.weeks[1:]
        )
        first_date = schedule[course.weekday][course.weeks[0]]
        return cls(
            course.get_title(),
            course.get_description(),
            Datetime('Europe/Warsaw', dt.datetime.combine(first_date, course.start_time)),
            Datetime('Europe/Warsaw', dt.datetime.combine(first_date, course.end_time)),
            [recurrence],
            course.location
        )


def load_calendars() -> list[Calendar]:
    response = gcal.calendarList().list().execute()['items']

    if 'nextPageToken' in response:
        # todo support pagination
        raise NotImplementedError

    return [
        Calendar.from_dict(json) for json in response
        if 'primary' not in json and json['accessRole'] == 'owner'
    ]


def insert_calendar(course: Course, schedule):
    print(f"Inserting calendar for {course.get_title()}")
    calendar_body = Calendar.from_course(course).to_dict()
    event_body = Event.from_course(course, schedule).to_dict()
    calendar_id = gcal.calendars().insert(body=calendar_body).execute()['id']
    gcal.events().insert(calendarId=calendar_id, body=event_body).execute()
    gcal.acl().insert(calendarId=calendar_id, body=ACL_RULE_PUBLIC).execute()


def update_calendar(calendar_id: str, course: Course, schedule):
    print(f"Updating calendar for {course.get_title()}")
    calendar_body = Calendar.from_course(course).to_dict()
    event_body = Event.from_course(course, schedule).to_dict()
    gcal.calendars().update(calendarId=calendar_id, body=calendar_body).execute()
    event_id = gcal.events().list(calendarId=calendar_id).execute()['items'][0]['id']
    gcal.events().update(calendarId=calendar_id, eventId=event_id, body=event_body).execute()


def delete_calendar(calendar_id: str):
    print(f'Deleting calendar {calendar_id}')
    gcal.calendars().delete(calendarId=calendar_id).execute()


if __name__ == '__main__':
    cals = load_calendars()
    for cal in load_calendars():
        delete_calendar(cal.id)
