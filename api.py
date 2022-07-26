from random import Random
import requests
import api_key
import json
import random
from urllib.parse import urlencode
api_key=api_key.api['api_key']

#params - can take different arguments
def tgGetJsonResponse(path, params=None):
    if params:
      query = urlencode(params)
      path = '{}?{}'.format(path,query)

    url = "https://api.telegram.org/bot{}/{}".format(api_key, path)
    response = requests.get(url, timeout=60)
    status = response.status_code
    json = response.json()
    if status != 200:
      print('error getting response', json)
    return json

#offset - a telegram parameter 
#it is the identifier of the first update to be returned; updates are confirmed when getUpdates is used with an offset greater than its update_id  
def tgGetUpdates(update_type, offset = None):
  offsetParam = "&offset={}".format(offset) if offset else ""
  return tgGetJsonResponse('getUpdates?allowed_updates={}{}'.format(update_type,offsetParam))['result']

'''get messages from updates'''
def tgGetMessages(offset = None):
  return tgGetUpdates('message',offset)

'''get polls from updates'''
def tgGetPolls(offset = None):
  return tgGetUpdates('poll',offset)

#since we got an HTTP access token for the bot, we have to employ an encoded URL to encode the query; this encoding is the reason why we called the urlib.parse module
#the query string is made up of key-value pairs
def tgSendMessage(params):
  query = urlencode(params)
  path = 'sendMessage?{}'.format(query)
  return tgGetJsonResponse(path)

def tgSendSimpleMessage(chat_id, text):
  return tgSendMessage({ 
        'chat_id': chat_id, 
        'text': text
    })

'''takes the details of reply and returns it in a dictionary form'''
def tgSendSimpleReply(chat_id, text, message_id):
  return tgSendMessage({ 
        'chat_id': chat_id, 
        'reply_to_message_id': message_id,
        'text': text,
    })

'''gets the number of group chat members'''
def tgGetChatMembersCount(chat_id):
  return tgGetJsonResponse('getChatMembersCount?chat_id={}'.format(str(chat_id)))['result']

#parameters needed by the Telegram poll (needed when users have more than one common time available)
def tgSendPoll(chat_id, question, options):
  query = urlencode({ 
    'chat_id': chat_id, 
    'question': question, 
    'options': json.JSONEncoder().encode(options), 
    'is_anonymous': False,
    'allows_multiple_answers': True,
  })
  path = 'sendPoll?{}'.format(query)
  return tgGetJsonResponse(path)['result']

def tgStopPoll(chat_id, message_id):
  params= {
    'chat_id': chat_id,
    'message_id': message_id
  }
  return tgGetJsonResponse('stopPoll', params)


if __name__ == "__main__":
    chat_id = -693369611 #ID of the group used
    response = tgStopPoll(chat_id, 462)
    print(response)