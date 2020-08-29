import datetime
from enum import Enum
import json


class FBMetadata:
    def __init__(self):
        self.persons = []
        self.chats = []
        self.group_chats = []

    def find_person(self, name):
        """
        :param name: string, name of person
        :return: reference to instance of object FBPerson, or None if not found
        """
        for person in self.persons:
            if person.name == name:
                return person
        return None

    def find_chat(self, title, participants, search_groups=False):
        """
        :param title: title of the chat (for regular chats, it's just name of the opposite chat, for group chats
        it's the custom name of the chat)
        :param participants: [string], name of all participants (can be used to extend search, or left None to be
        omitted)
        :param search_groups: optional bool, whether the search should be performed on group chats or on regular chats
        :return: reference to instance of object FBChat, or None if not found
        """
        participants = participants.sort()
        chats = self.chats
        if search_groups:
            chats = self.group_chats

        for chat in chats:
            if chat.title == title:
                if [x.name for x in chat.participants].sort() == participants:
                    return chat
        return None

    def __load_people(self, participants_data):
        """
        :param participants_data: object "participants" from deserialized message json
        :return: nothing
        """
        for person in participants_data:
            if self.find_person(person['name']) is None:
                self.persons.append(FBPerson(person['name']))

    def __load_message(self, message_data, chat_ref):
        """
        :param message_data: single element of array, which was gathered from "messages" in deserialized message json
        :param chat_ref: reference to instance of object FBChat, to which the message should be assigned
        :return: nothing
        """
        sender = message_data['sender_name']
        timestamp = message_data['timestamp_ms']
        msg_type = fb_message_type_switch(message_data["type"])

        possible_data = {}
        for search_term in ['content', 'photos', 'videos', 'share', 'reactions']:
            if search_term in message_data:
                possible_data[search_term] = message_data[search_term]
            else:
                possible_data[search_term] = None

        if possible_data['photos'] is not None:
            replacement = []
            for photo in possible_data['photos']:
                replacement.append(FBPhoto(photo['uri'], photo['creation_timestamp']))
            possible_data['photos'] = replacement

        if possible_data['videos'] is not None:
            replacement = []
            for video in possible_data['videos']:
                replacement.append(FBVideo(video['uri'], video['creation_timestamp'], video['thumbnail']['uri']))
            possible_data['videos'] = replacement

        if possible_data['reactions'] is not None:
            reactions = []
            for react in possible_data['reactions']:
                reactions.append(FBReaction(self.find_person(react['actor']), react['reaction']))

        message = FBMessage(sender, timestamp, msg_type,
                            possible_data['content'],
                            possible_data['photos'],
                            possible_data['videos'],
                            possible_data['share'],
                            possible_data['reactions'])

        chat_ref.add_messages([message])

    def __load_chat(self, json_data):
        """
        :param json_data: deserialized message json
        :return: nothing
        """
        participants = [x['name'] for x in json_data['participants']]

        is_group_chat = json_data['thread_type'] != 'Regular'

        if is_group_chat:
            chat = self.find_chat(json_data['title'], participants, search_groups=True)
        else:
            chat = self.find_chat(json_data['title'], participants)
        if chat is None:
            chat = FBChat(json_data['title'], [self.find_person(name) for name in participants])
            if is_group_chat:
                self.group_chats.append(chat)
            else:  # is standard 1on1 chat
                self.chats.append(chat)

        for msg in json_data['messages']:
            self.__load_message(msg, chat)

        for participant in participants:
            self.find_person(participant).add_chat(chat, is_group_chat)

    def from_entry(self, entry):
        """
        :param entry: path to single message json file
        :return: nothing
        """
        with open(entry, 'r') as json_file:
            json_data = json.load(json_file)

        self.__load_people(json_data['participants'])
        self.__load_chat(json_data)


class FBPerson:
    def __init__(self, name):
        """
        :param name: name of person
        """
        self.name = name
        self.chats = {}
        self.group_chats = {}

    def add_chat(self, chat, group_chat=False):
        """
        :param chat: the reference to the instance of object FBChat
        :param group_chat: bool, to determine whether the added chat is group_chat or not
        :return: nothing
        """
        if chat.find_participant(self.name) is not None:
            if group_chat:
                self.group_chats[chat.title] = chat
            else:
                self.chats[chat.title] = chat


class FBChat:
    def __init__(self, title, participants):
        """
        :param title: title of chat (usually name of person, or name of group chat)
        :param participants: [FBPerson], list of references to instances of person
        """
        self.title = title
        self.participants = participants
        self.messages = []

    def find_participant(self, name):
        """
        :param name: name of person, which is to be found in list of participants
        :return: reference to instance of object FBPerson, or None if person is not found
        """
        for participant in self.participants:
            if participant.name == name:
                return participant
        return None

    def add_messages(self, messages):
        """
        :param messages: [FBMessage], list of instances of object FBMessage
        :return: nothing
        """
        for msg in messages:
            if self.find_participant(msg.sender) is not None:
                self.messages.append(msg)


class FBPhoto:
    def __init__(self, uri, timestamp):
        """
        :param uri: uri to the source of the image
        :param timestamp: date given in ms
        """
        self.uri = uri
        self.date = datetime.datetime.fromtimestamp(timestamp / 1000.0)


class FBVideo:
    def __init__(self, uri, timestamp, thumbnail):
        """
        :param uri: uri of the source of the video
        :param timestamp: date given in ms
        :param thumbnail: uri of the thumbnail of video
        """
        self.uri = uri
        self.date = datetime.datetime.fromtimestamp(timestamp / 1000.0)
        self.thumbnail = thumbnail


class FBReaction:
    def __init__(self, person, reaction):
        """
        :param person: reference to instance of FBPerson, creator of react
        :param reaction: string, type of reaction
        """
        self.actor = person
        self.reaction = reaction


class FBMessage:
    def __init__(self, sender, timestamp, type_of_msg, content=None, photos=None, videos=None, share=None,
                 reactions=None):
        """
        :param sender: FBPerson, reference to instance of object of the sender of the message
        :param timestamp: date given in ms
        :param type_of_msg: FBTypeOfMsg
        :param content: optional, string, message content
        :param photos: optional, [FBPhoto], list of FBPhoto objects (if message has photos in it)
        :param videos: optional, [FBVideo], list of FBVideo objects (if message has videos in it)
        :param share: optional, NOT DEFINED SO FAR, TODO: create share object
        :param reactions: optional, [FBReaction], list of FBReaction objects (if message has reacts tied to it)
        """
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


class FBTypeOfMsg(Enum):  # Enum for the type message (more might be added later)
    Unknown = -1
    Generic = 1
    Share = 2


def fb_message_type_switch(argument):
    """
    :param argument: switch, to choose the FBTypeOfMsg
    :return: enum of FBTypeOfMsg
    """
    switch_cases = {
        'Generic': FBTypeOfMsg.Generic,
        'Share': FBTypeOfMsg.Share
    }
    if argument in switch_cases:
        return switch_cases[argument]
    # default:
    return FBTypeOfMsg.Unknown
