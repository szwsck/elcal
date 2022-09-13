#!/usr/bin/env python3
import datetime as dt
import json

from calendars import load_calendars, update_calendar, insert_calendar
from courses import load_courses


def main():
    schedule = [
        [dt.date.fromisoformat(d) for d in dates]
        for dates in json.load(open('schedule.json', 'rb'))
    ]
    courses = load_courses()
    existing_calendars = load_calendars()

    print(f"Loaded {len(courses)} courses and {len(existing_calendars)} calendars")

    for course in courses:
        existing_calendar = next(filter(lambda c: c.course.id == course.id, existing_calendars), None)
        if not existing_calendar:
            insert_calendar(course, schedule)
        elif existing_calendar.course != course:
            update_calendar(existing_calendar.id, course, schedule)

    for calendar in existing_calendars:
        existing_course = next(filter(lambda c: calendar.course.id == c.id, courses), None)
        if not existing_course:
            print(f"warn: calendar {calendar.summary}(id: {calendar.id}) no longer needed")

    for calendar in load_calendars():
        print(f"{calendar.course.get_title()}: {calendar.get_link()}")


if __name__ == '__main__':
    main()
