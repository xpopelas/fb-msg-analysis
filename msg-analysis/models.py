import datetime
from enum import Enum
import json


class FBMetadata:
    def __init__(self):
        self.persons = []
        self.chats = []
        self.group_chats = []

    def find_person(self, name):
        for person in self.persons:
            if person.name == name:
                return person
        return None

    def find_chat(self, title, participants):
        participants = participants.sort()
        for chat in self.chats:
            if chat.title == title:
                if [x.name for x in chat.participants].sort() == participants:
                    return chat
        return None

    def load_people(self, participants_data):
        for person in participants_data:
            if self.find_person(person['name']) is None:
                self.persons.append(FBPerson(person['name']))

    def load_message(self, message_data):
        pass  # TODO: message parsing

    def load_chat(self, json_data):
        participants = [x['name'] for x in json_data['participants']]

        chat = self.find_chat(json_data['title'], participants)
        if chat is None:
            if len(participants) > 2:  # is group chat TODO: better group chat check
                chat = FBChat(json_data['title'], [self.find_person(name) for name in participants])
                self.group_chats.append(chat)

        for msg in json_data['messages']:
            self.load_message(msg)

    def load_entry(self, entry):
        with open(entry, 'r') as json_file:
            json_data = json.load(json_file)

        self.load_people(json_data['participants'])
        self.load_chat(json_data)


class FBPerson:
    def __init__(self, name):
        self.name = name
        self.chats = {}
        self.group_chats = {}

    def add_chat(self, chat, group_chat=False):
        if chat.has_participant(self.name):
            if group_chat:
                self.group_chats[chat.title] = chat
            else:
                self.chats[chat.title] = chat


class FBChat:
    def __init__(self, title, participants):
        self.title = title
        self.participants = participants
        self.messages = []

    def add_messages(self, messages):
        for msg in messages:
            if msg.sender_name in self.participants:
                self.messages.append(msg)


class FBPhoto:
    def __init__(self, uri, timestamp):
        self.uri = uri
        self.date = datetime.datetime.fromtimestamp(timestamp / 1000.0)


class FBVideo:
    def __init__(self, uri, timestamp, thumbnail):
        self.uri = uri
        self.date = datetime.datetime.fromtimestamp(timestamp / 1000.0)
        self.thumbnail = thumbnail


class FBMessage:
    def __init__(self, sender, timestamp, type_of_msg, content=None, photos=None, videos=None, share=None,
                 reactions=None):
        if reactions is None:
            reactions = []
        self.sender = sender
        self.date = datetime.datetime.fromtimestamp(timestamp / 1000.0)
        self.type = type_of_msg
        self.content = content
        self.photos = photos
        self.videos = videos
        self.share = share
        self.reactions = reactions


class FBTypeOfMsg(Enum):
    Generic = 1
    Share = 2
