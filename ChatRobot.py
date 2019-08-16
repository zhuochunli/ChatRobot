import string
import re
import random
import requests
import spacy
import json
from rasa_nlu.training_data import load_data
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.model import Trainer
from rasa_nlu import config
from wxpy import *

# Create a trainer that uses this config
trainer = Trainer(config.load("config_spacy.yml"))
# Load the training data
training_data = load_data('demo-rasa-noents.json')
# Create an interpreter by training the model
interpreter = trainer.train(training_data)

nlp = spacy.load("en_core_web_md")

# Define the policy rules
INIT=0
AUTHED=1
CHOOSE_STOCK=2
QUERY_RESULT=3
policy_rules = {
    (INIT, "greet"): (INIT, "hi,i am a smart robot helping you query stock information!", None),
    (INIT, "ask"): (INIT, "you'll have to log in first, what's your phone number?", AUTHED),  #不登陆的话就一直处于authed状态
    (INIT, "number"): (AUTHED, "perfect, welcome back! ", None),
    (AUTHED, "ask"): (CHOOSE_STOCK, "what specific information you wanna query?", None),
    (CHOOSE_STOCK, "specify_stock"): (QUERY_RESULT, "here are some information I find for you:{}", None),
    (QUERY_RESULT, "specify_stock"): (QUERY_RESULT, "here are some information I find for you:{}", None),
    (QUERY_RESULT, "bye"): (INIT, "thank you for using, hope to see you again!", None)
}
#初始化状态（若不用微信则无需设置）
state = INIT
pending = None

#查询参数
company = ""
company_name = ""
query_attribute = ""

#针对chitchat的匹配及回答
responses = ["I'm sorry :( I couldn't find any stock information like that", "The {} of {} is {}, what else you wanna query?"]
rules = {'if (.*)': ["Do you really think it's likely that {0}", 'Do you wish that {0}', 'What do you think about {0}', 'Really--if {0}'], 'do you think (.*)': ['if {0}? Absolutely.', 'No chance'], 'I want (.*)': ['What would it mean if you got {0}', 'Why do you want {0}', "What's stopping you from getting {0}"], 'do you remember (.*)': ['Did you think I would forget {0}', "Why haven't you been able to forget {0}", 'What about {0}', 'Yes .. and?']}

#公司名与股票名映射
stock_name = {'Apple':'aapl', 'Tesla':'tsla', 'Google':'goog'}



def find_stock():
    url = "https://cloud.iexapis.com/stable/stock/{}/quote?token=sk_984e096fa40b459b8d49019690145508".format(company)
    r = requests.get(url)
    dict = json.loads(r.text)
    u=dict.get('{}'.format(query_attribute))
    list=[u]
    return list


def respond():
    results = find_stock()
    info = results[0]
    n = min(len(results),3)
    return responses[n].format(query_attribute, company_name, info)


def interpret(message):
    doc = nlp(message)
    data = interpreter.parse(message)
    intent=data["intent"]["name"]
    if re.match(r'[0-9]{6}', message):     #规定电话号码为6位数字，若任意数字，会与week52High这种查询参数混淆(识别为PERSON？)
        return 'number'
    elif intent=='ask' or intent=='bye' or intent=='greet':
        return intent

    for ent in doc.ents:
        if ent.label_ == 'ORG' and ent.text != 'latestPrice':    #因为latestPrice会被识别为ORG了
                global company, query_attribute, company_name
                company_name = ent.text
                company = stock_name.get(ent.text)
                list = re.findall(r"\bthe(.+)of\b", message)
                query_attribute = list[0].strip()
                return 'specify_stock'
    # msg = message.lower()
    # if any([d in msg for d in string.digits]):
    #     return 'number'
    # if 'bye' in msg or 'see you' in msg:
    #     return 'bye'
    # if 'want' in msg or 'wanna' in msg:
    #     return 'ask'
    # return 'none'

    # if 'no' in message:
    #     data["intent"]["name"] = "deny"


#不集成微信时使用：

# def send_message(state, pending, message):
#     print("USER : {}".format(message))
#     response = chitchat_response(message)
#     if response is not None:
#         print("BOT : {}".format(response))
#         return state, None
#
#     # Calculate the new_state, response, and pending_state
#     new_state, response, pending_state = policy_rules[(state, interpret(message))]
#     print(new_state)
#     if new_state == QUERY_RESULT:
#         pending=None
#         i = respond()
#         response = response.format(i)
#         print("BOT : {}".format(response))
#     if new_state != QUERY_RESULT:
#         print("BOT : {}".format(response))
#
#     if pending is not None:
#         new_state, response, pending_state = policy_rules[pending]
#         print("BOT : {}".format(response))
#     if pending_state is not None:
#         pending = (pending_state, interpret(message))
#     return new_state, pending  # 不断轮询，直到pending为空


def chitchat_response(message):
    # Call match_rule()
    response, phrase = match_rule(rules, message)
    # Return none is response is "default"
    if response == "default":
        return None
    if '{0}' in response:
        # Replace the pronouns of phrase
        phrase = replace_pronouns(phrase)
        # Calculate the response
        response = response.format(phrase)
    return response



def match_rule(rules, message):
    for pattern, responses in rules.items():
        match = re.search(pattern, message)
        if match is not None:
            response = random.choice(responses)
            var = match.group(1) if '{0}' in response else None
            return response, var
    return "default", None



def replace_pronouns(message):

    message = message.lower()
    if 'me' in message:
        return re.sub('me', 'you', message)
    if 'i' in message:
        return re.sub('i', 'you', message)
    elif 'my' in message:
        return re.sub('my', 'your', message)
    elif 'your' in message:
        return re.sub('your', 'my', message)
    elif 'you' in message:
        return re.sub('you', 'me', message)

    return message


#提前静态输入至数组中：

# Define send_messages()
# def send_messages(messages):
#     state = INIT
#     pending = None
#     for msg in messages:
#         state, pending = send_message(state, pending, msg)
#
# send_messages([
#     "hello",
#     "I wanna query stock",
#     "123456",
#     "do you remember when I ordered 1000 kilos by accident?",  #I want you
#     "What is the latestPrice of Tesla?",
#     "What's the week52High of Google?",
#     "good bye"  #no,thanks
# ])

#循环动态输入：

# def send_messages():
#     state = INIT
#     pending = None
#     print("淳SIR的智能机器人已启动！！")
#     while 1:
#         msg = input()
#         state, pending = send_message(state, pending, msg)
#
# send_messages()

#wxpy集成微信模块：

bot = Bot()        #cache_path=True
my_friend = bot.friends().search('淳sir', sex=MALE, city="武汉")[0]   #查找我的微信用户
def send_message(state, pending, message):
    print("USER : {}".format(message))
    response = chitchat_response(message)
    if response is not None:
        print("BOT : {}".format(response))
        my_friend.send(response)   #将response发送至我
        return state, None

    # Calculate the new_state, response, and pending_state
    new_state, response, pending_state = policy_rules[(state, interpret(message))]
    print(new_state)
    if new_state == QUERY_RESULT:
        pending=None
        i = respond()
        response = response.format(i)
        print("BOT : {}".format(response))
        my_friend.send(response)
    if new_state != QUERY_RESULT:
        print("BOT : {}".format(response))
        my_friend.send(response)

    if pending is not None:
        new_state, response, pending_state = policy_rules[pending]
        print("BOT : {}".format(response))
        my_friend.send(response)
    if pending_state is not None:
        pending = (pending_state, interpret(message))
    return new_state, pending    # 不断轮询，直到pending为空

@bot.register(my_friend)
def reply_my_friend(msg):
    global state,pending
    state, pending = send_message(state, pending, msg.text)    #msg.text为消息的文本信息

embed()   #阻塞线程并进入pycharm控制台

