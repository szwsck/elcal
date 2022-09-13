import datetime
from dataclasses import dataclass, field
from datetime import time
from typing import Optional

from dataclasses_json import dataclass_json, config

from google_api import sheets

COURSES_SHEET_ID = '1IEauKdcTEWjgRX43rcE9-x7VZ8BMEFg2AMTCDogBpwo'
COURSES_RANGE = 'calc2!A:K'
COURSE_TYPE_NAMES = {
    'lecture': 'Wykład',
    'project': 'Projekt',
    'tutorial': 'Ćwiczenia',
    'laboratory': 'Laboratorium',
}


def load_courses():
    result = sheets.values().get(spreadsheetId=COURSES_SHEET_ID, range=COURSES_RANGE).execute()
    return [Course.from_row(row) for row in result['values']]


@dataclass_json
@dataclass
class Course:
    id: str
    name: str
    type: str
    location: str
    start_time: time = field(metadata=config(encoder=time.isoformat, decoder=time.fromisoformat))
    end_time: time = field(metadata=config(encoder=time.isoformat, decoder=time.fromisoformat))
    weekday: int
    weeks: list[int]
    instructor: Optional[str] = None
    group: Optional[str] = None

    @classmethod
    def from_row(cls, row: list[str]):
        return cls(
            row[3],
            row[4],
            row[5],
            row[6],
            datetime.datetime.strptime(row[7], '%H:%M').time(),
            datetime.datetime.strptime(row[8], '%H:%M').time(),
            int(row[1]),
            list(map(int, row[0].split(', '))),
            row[9] if len(row) >= 10 and row[9] else None,
            row[10] if len(row) >= 11 and row[10] else None,
        )

    def get_title(self):
        if self.group:
            return f'{self.name} - {COURSE_TYPE_NAMES[self.type]} gr. {self.group}'
        else:
            return f'{self.name} - {COURSE_TYPE_NAMES[self.type]}'

    def get_description(self):
        if self.instructor:
            return f'Prowadzący: {self.instructor}'
        else:
            return ''
