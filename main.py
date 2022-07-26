import requests
import datetime 
import json
from scheduler import book_timeslot
import re
import numpy 
from functools import reduce
#create a python file called api_key 
#that contains a dictionary api={"api_key":"your_api_key"}
import api_key
api_key=api_key.api['api_key']
import api

'''check if the email is in a valid format using regex'''
#if the email address sent matches regex, consider it a valid email; otherwise, it is invalid 
def check_email(email):
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
    if(re.search(regex,email)):  
        print("Valid Email") 
        return True
    else:  
        print("Invalid Email")  
        return False

#The number of None's attributed to the variable no_response is due to the fact that we had many variables
#update_id and api.tgGetMessages as the parameters under the getLastMessage function 
#following Telegram bot parameters
#lines of code all the way until line 38: checks the length of all the messages 
#if the size is equal to 0, that means there are no messages, so the function returns no response
#last_index = size-1 takes the last message, and the last item just takes the message that last_index refers to
def getLastMessage(update_id):
    no_response = None, None, None, None, None, None
    result = api.tgGetMessages(update_id)
    size= len(result)
    if (size == 0):
        return no_response
    last_index = size-1
    last_item = result[last_index]
#update_id is the update id of the last message, which was taken in the previous line
#if there's no string (message) in the last message, then there should be no response 
    update_id = last_item['update_id']
    if 'message' not in last_item:
        return no_response
    #the message variable simply gets the content of the last message 
    #terms like 'message', 'message_id', 'chat', etc. are part of Telegram's in-built parameters 
    message = last_item['message']
    message_id = message['message_id']
    chat = message['chat']
    chat_id = chat['id']
    chat_type = chat['type']
    if chat_type != 'group': 
        return no_response
        #text, from, is_bot are also all Telegram bot parameter
    if 'text' not in message:
        return no_response
    last_msg = message['text']
    sender = message['from']
    #is_bot is a Boolean; if the sender of the message is a bot, then no response/reply is warranted
    if sender['is_bot']:
        return no_response
    user_id = sender['id']

    return last_msg,chat_id,update_id, user_id, message_id, sender
    
'''the sendInlineMessageForService function creates the introductory message given by Arc Bot'''
#comprised of lists and dictionaries, it shows options for the types of meetings 
def sendInlineMessageForService(chat_id, reply_to_message_id):
    text='Hi! I am Arc Bot, your corporate scheduling buddy! \n\nYou can control me using these commands:\n\n/start - to start chatting with the bot\n/preferred - to see common time intervals\n/vote - to create a poll to vote based on common times\n/schedule [time] - to choose meeting time interval\n/book - to finalize the booking after emails are added\n/cancel - to stop chatting with the bot\n\nFor more information please contact jana.ang@obf.ateneo.edu | celestine.yu@obf.ateneo.edu | john.balaong@obf.ateneo.edu.'
    keyboard={
        'keyboard':
            [
                [{'text':'Progress Report'},{'text':'Post-Project Evaluation'}],
                [{'text':'Planning Seminar'},{'text':'Onboarding'}]
            ],
        'one_time_keyboard': True,
        'selective': True,
    }
    #so that python can understand the response
    #Telegram operates on JSON, so there is a need to encode it in JSON as well
    reply_markup=json.JSONEncoder().encode(keyboard)
    response = api.tgSendMessage({ 
        'chat_id': chat_id, 
        'text': text, 
        'reply_markup' : reply_markup, 
        'reply_to_message_id': reply_to_message_id
    })
    return response

'''time interval options created from 8:00 to 5:30 pm'''
time_range = range(8,18)
def generateTimeKeyboard():
    items = []
    #gets the current date and time 
    current_time=datetime.datetime.now()
    current_hour = current_time.hour
    #for all items within the variable time_range
    #if the time the user plans to schedule the meeting is not within working hours, the continue keyword ends the iteration in for loop and moves to the next one 
    for hour in time_range:
        if hour < current_hour:
            continue
        #time slots are appended to the items list for the keyboard (30 minute intervals, as can be seen from the format below)
        items.append([{'text': '{0:02}:00'.format(hour)}, {'text': '{0:02}:30'.format(hour)}])
        
    return items

#since we cannot directly use data from a keyboard, we created a list of time slots similarly to the code aboe
#then just added them to the items list
'''difference between time generateTimeList and generateTimeKeyboard: 
the former is a one-dimensional array of hours e.g. ['10:00', '10:30'], 
while the latter is a 2d array of values used for replying the inline keyboard'''

def generateTimeList():
    items = []
    current_time=datetime.datetime.now()
    current_hour = current_time.hour
    for hour in time_range:
        if hour < current_hour:
            continue
        items.append('{0:02}:00'.format(hour))
        items.append('{0:02}:30'.format(hour))
    return items

'''sends time slots as an inline keyboard'''
def sendInlineMessageForBookingTime(chat_id):
    text_message='Please choose a time slot...'
    keyboard = generateTimeKeyboard()
    key=json.JSONEncoder().encode({'keyboard': keyboard, 'one_time_keyboard': True})
    response = api.tgSendMessage({ 
        #a dictionary that is composed of the response to the options given in the inline time keyboard
        'chat_id': chat_id, 
        'text': text_message, 
        'reply_markup' : key,
    })
    return response

meeting_types = ['Progress Report','Post-Project Evaluation','Planning Seminar','Onboarding']

#current active session
def book_session(session):
    description = session['description']
    booking_time = session['booking_time']
    emails = session['emails']
    title = session['title']
    response = book_timeslot(description,booking_time,emails, title)
    return response

'''function that should send the common times (intersection of all time slots) to users'''
def send_common_times (chat_id, times):
    text = 'Here are the common times: {}\nEnter /vote - to create a poll and choose one common time\nEnter /schedule [time] to finalize your booking schedule'.format(reduce(lambda str, t: str+ '\n- ' + t,times,''))
    response = api.tgSendMessage({ 
        'chat_id': chat_id, 
        'text': text,

    })
    return response

'''terminate all the past sessions, so that the poll only involves the common times'''
def cleanup(sessions, chat_id):
    session = sessions.pop(chat_id)
    if session['poll']:
        api.tgStopPoll(chat_id, session['poll'])

'''structures the flow of the bot'''
def run():
    prev_update_id = None
    sessions = {}
    #while True is just an infinite loop
    while True:
        try: #try and except to catch any errors/bugs
            current_last_msg,chat_id,current_update_id,user_id, message_id, sender =getLastMessage(prev_update_id)
            print(sender)
            #identifying the unique senders
            sender_username = sender['id'] if sender  else None
            print(sessions)
            if current_update_id==prev_update_id:
                continue
            
            prev_update_id=current_update_id
            if chat_id in sessions:
                session = sessions[chat_id]
                print(session)
                step = session['step']
                user = session['user']
                #step refers to the stage in the sequence of the Arc-Bot flow 
                #if the last/most recent message was one of the four meeting types, the next stage would be the list of available time slots
                if (step == 0 and
                    user == user_id and
                    current_last_msg in meeting_types ):
                    time_list = generateTimeList()
                    #if the number of elements in the time_list is zero (past work hours), it will display the message that there are no available time slots.
                    if (len(time_list) == 0):
                        api.tgSendSimpleReply(chat_id, 'Sorry, it is past work hours. Try booking again between 08:00 to 17:30.', message_id)
                        continue;
                    session['step'] = 1
                    session['title'] = current_last_msg

                    sendInlineMessageForBookingTime(chat_id)
                #next steps  
                if step == 1:
                    #users pick their available time slots
                    preferred_times = session['preferred_times']
                    if (current_last_msg in generateTimeList()):
                        #if the user already sent available time slots:
                        if sender_username in preferred_times:
                            user_preferred_times = preferred_times[sender_username]
                            #these line of code either adds, removes, or initializes the preferred time arrays for each user
                            if current_last_msg in user_preferred_times:
                                preferred_times[sender_username].remove(current_last_msg)
                            else:
                                preferred_times[sender_username].append(current_last_msg)
                        else:
                            preferred_times[sender_username] = [current_last_msg]
                        
                        continue
                    time_values = preferred_times.values()
                    if (len(time_values) == 0):
                        continue
                    #found the intersection/common time/s among all the ones provided by users and converted them into a list 
                    common_times = reduce(numpy.intersect1d, time_values).tolist()
                    if (current_last_msg == '/preferred'):
                        send_common_times(chat_id,common_times)
                        continue
                    if (current_last_msg == '/vote' and user == user_id):
                        #if the number of common times is less than or equal to 1, that means there is no need to poll
                        if (len(common_times) <= 1):
                            api.tgSendSimpleMessage(chat_id, "There are no time slots to vote on.")
                            continue
                        response = api.tgSendPoll(chat_id,'schedule vote', common_times)
                        session['poll'] = response['message_id']
                        continue
                    #everyone has to have selected the common time
                    schedule_match = re.search('^/schedule(?: ([\d]{2}:[\d]{2})|preferred)?', current_last_msg)
                    if (schedule_match and user == user_id):
                        selected_time = schedule_match.group(1)
                        if not selected_time:
                            send_common_times(chat_id,common_times)
                            continue
                        if selected_time == 'preferred':
                            if (len(common_times) ==1):
                                preferred_time = common_times[0]
                                session['booking_time'] = preferred_time
                                session['step'] = 2
                                api.tgSendSimpleMessage(chat_id, "Schedule is set to " + preferred_time)
                                api.tgSendSimpleMessage(chat_id,"Please enter email address:\nEnter /book to finalize the booking once everyone's email addresses have been sent.")
                            continue
                        if (selected_time in common_times): #if chosen slot to schedule is one of the common times, it sets it then and asks for the email address
                            session['booking_time'] = selected_time
                            session['step'] = 2
                            api.tgSendSimpleMessage(chat_id, "Schedule is set to " + selected_time)
                            api.tgSendSimpleMessage(chat_id,"Please enter email address:")
                        else: #chosen slot to schedule was not returned as one of the common times
                            api.tgSendSimpleReply(chat_id, "Time provided not in your common schedules", message_id)
                            send_common_times(chat_id, common_times)
                descCmd = re.search('^/description (.*)', current_last_msg)  
                if descCmd: #command to add the optional description option in the Google Calendar event
                    session['description'] = descCmd.group(1)
                    api.tgSendSimpleReply(chat_id, "Description for the meeting has been added successfully.", message_id)
                    continue
                if current_last_msg=='/cancel': #if the booking is cancelled, all the sessions are erased in the process so that users can start with a clean slate
                    cleanup(sessions,chat_id)
                    api.tgSendSimpleReply(chat_id, "Booking has been cancelled. Thank you for using Arc-Bot.", message_id)
                    continue
                if (step == 2): #if users moved on to the next stage, which involves booking the meeting and inputting email addresses
                    if (current_last_msg == '/book'):
                        if len(session['emails']) == 0: #if the number of email addresses is equal to zero, then the bot will not recognize any and return the message below
                        #otherwise, the Google Calendar event will be booked
                            api.tgSendSimpleReply(chat_id, "You have not yet sent any email addresses to me yet.", message_id)
                            continue
                        response = book_session(sessions[chat_id])
                        if response:
                            api.tgSendSimpleMessage(chat_id,f"Appointment is booked. See you at {session['booking_time']}")
                        else: #if users try to book, but didn't fulfill all parameters needed to book
                            api.tgSendSimpleMessage(chat_id, "Please try another time slot and try again tomorrow.")
                        cleanup(sessions,chat_id)
                        continue
                    if check_email(current_last_msg):
                        if current_last_msg in sessions[chat_id]['emails']: #if added email is repeated/sent again by the user when it was already noted by the bot
                            api.tgSendSimpleReply(chat_id, "That email address is already in the guest list.", message_id)
                            continue
                        #replies to emails sent includes the message below
                        api.tgSendSimpleReply(chat_id,"Booking please wait...", message_id)
                        sessions[chat_id]['emails'].append(current_last_msg)
                    else: #invalid email based on the regex in the earlier part of the code 
                        api.tgSendSimpleReply(chat_id,"Please enter a valid email.\nEnter /cancel to quit chatting with the bot\nThanks!", message_id)

            #the bot does not move/do anything until the /start command is given
            elif current_last_msg=='/start':
                #counts the number of group chat members
                #dictionary of parameters
                count = api.tgGetChatMembersCount(chat_id)
                sessions[chat_id] = {
                    'step': 0,
                    'user': user_id,
                    'members_count': count,
                    'title': None,
                    'description': None,
                    'booking_time': None,
                    'emails': [],
                    'preferred_times': {},
                    'poll': None,
                }
                print(sessions[chat_id])
                sendInlineMessageForService(chat_id, message_id)
        except:
            continue

            
         
'''just test code so that there is no need to go through the whole flow (testing short sections is possible)'''       
#blocks/prevents parts of code from being run when modules are being imported
#we only want the code to run when all modules are imported     
if __name__ == "__main__":
    run()