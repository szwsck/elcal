# elcal

A script to create shareable Google Calendars for university classes.

### Adding a course

Create a JSON object from the following template:

```
 {
  "id": "wus-lec", # an unique id that will not change in the future
  "name": "WUS", # course name
  "type": "lecture", # one of: lecture, project, tutorial, laboratory
  "location": "123B, EiTI",
  "start_time": "14:15",
  "end_time": "16:00",
  "instructor": "Jan Kowalski", # optional, will show up in event description
  "group": "101", # optional, will show up in the title
  "weekday": 3, # an integer in range 0-4
  "weeks": [0, 2, 4, 6, 8, 10, 12, 14] # list of weeks this event will occur in, starting from 0 
}
```
then either add it to `semester.json` and open a PR, or send it to me via private message.
