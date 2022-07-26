from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
# SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SCOPES = ['https://www.googleapis.com/auth/calendar']

def create_service():
    """shows basic usage of the Google Calendar API.
    prints the start and name of the next 10 events on the user's calendar
    """
    creds = None
    #The file token.pickle stores the user's access and refresh tokens, and is
    #created automatically when the authorization flow completes for the first
    #time
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)

def book_timeslot(event_description,booking_time,emails, title):
    service = create_service()
    
    '''to manipulate the booking time'''
    start_time=str(datetime.datetime.now())[:10]+'T'+booking_time+':00+08:00'
    end_time=str(datetime.datetime.now())[:10]+'T'+str(int(booking_time[:2])+1)+':00:00+08:00'

    '''to call the calendar API'''
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Booking a time slot....')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])
    attendees = list(map(lambda email: { 'email': email}, emails ))
    if not events:
        event = {
            'summary': title,
            'location': 'Philippines',
            'description': event_description,
            'sendUpdatess': 'all',
            'createRequest': {
                'type': 'hangoutsMeet'
            },
            'start': {
                'dateTime': start_time,
                'timeZone': 'Asia/Singapore',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'Asia/Singapore',
            },
            'recurrence': [
                'RRULE:FREQ=DAILY;COUNT=1'
            ],
            'attendees': attendees,
            'reminders': {
            'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
            'visibility': 'public'
        }
        print(event)
        event = service.events().insert(calendarId='primary', body=event).execute()
        print ('Event created: %s' % (event.get('htmlLink')))
        return True

    else:
        '''check if there are any similar start times'''
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            if start==start_time:
                print('Already booked....')
                return False
        '''break out of for loop if there are no apppointment that has the same time'''
        event = {
            'summary': title,
            'location': 'Philippines',
            'description': event_description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'Asia/Singapore',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'Asia/Singapore',
            },
            'recurrence': [
                'RRULE:FREQ=DAILY;COUNT=1'
            ],
            'attendees': attendees,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                    ],
            },
            'sendUpdatess': 'all',
            'createRequest': {
                'type': 'hangoutsMeet'
            },
            'visibility': 'public'
        }
        event = service.events().insert(calendarId='primary', body=event).execute()
        print ('Event created: %s' % (event.get('htmlLink')))
        return True
    


if __name__ == '__main__': 
    input_email='test@gmail.com'
    booking_time='14:00' 
    result=book_timeslot('Progress Report',booking_time,input_email)