"""
Modules used to represent all kinds of Facebook chat related data
Data used in loading of all the messages and chats are downloaded from the
Settings -> Your Facebook Information -> Download Your Information
and then chosen as Messages and downloaded in json format
"""

from __future__ import annotations
import datetime
from enum import Enum
import json
from typing import List, Dict


class FBMetadata:
    """
    Class used to represent entire Facebook messages metadata

    Attributes
    ----------
    persons: List[FBPerson]
        represents all persons, who are loaded and have some sort of chat conversation
    chats: List[FBChat]
        list of all chats (1 on 1) that were loaded
    group_chats: List[FBChat]
        list of all group chats that were loaded

    Methods
    -------
    find_person(self, name: str)
        finds person by their name and returns reference to their object
    find_chat(self, title: str, participants: List[str] = None, search_groups: bool = False)
        finds chat by it's title and potentially by their participants (to be more accurate) and returns reference to
        their object
    from_entry(self, entry: str)
        loads all of information from message.json file
    """
    def __init__(self):
        self.persons: List[FBPerson] = []
        self.chats: List[FBChat] = []
        self.group_chats: List[FBChat] = []

    def find_person(self, name: str):
        """
        :param name: string, name of person
        :return: reference to instance of object FBPerson, or None if not found
        """
        for person in self.persons:
            if person.name == name:
                return person
        return None

    def find_chat(self, title: str, participants: List[str] = None, search_groups: bool = False):
        """
        :param title: title of the chat (for regular chats, it's just name of the opposite chat, for group chats
        it's the custom name of the chat)
        :param participants: name of all participants (can be used to extend search, or left None to be
        omitted)
        :param search_groups: optional bool, whether the search should be performed on group chats or on regular chats
        :return: reference to instance of object FBChat, or None if not found
        """
        chats = self.chats
        if search_groups:
            chats = self.group_chats

        if participants is not None:
            participants.sort()

        for chat in chats:
            if chat.title == title:
                if participants is None or sorted([x.name for x in chat.participants]) == participants:
                    return chat
        return None

    def __load_people(self, participants_data: List[Dict[str, str]]):
        """
        :param participants_data: object "participants" from deserialized message json
        :return: nothing
        """
        for person in participants_data:
            if self.find_person(person['name']) is None:
                self.persons.append(FBPerson(person['name']))

    def __load_message(self, message_data: Dict, chat_ref: FBChat):
        """
        :param message_data: single element of array, which was gathered from "messages" in deserialized message json
        :param chat_ref: reference to instance of object FBChat, to which the message should be assigned
        :return: nothing
        """
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

        if possible_data['share'] is not None:
            link = None
            share_text = None
            if 'link' in possible_data['share']:
                link = possible_data['share']['link']
            if 'share_text' in possible_data['share']:
                share_text = possible_data['share']['share_text']
            possible_data['share'] = FBShare(link, share_text)

        message = FBMessage(message_data['sender_name'],
                            message_data['timestamp_ms'],
                            fb_message_type_switch(message_data["type"]),
                            possible_data['content'],
                            possible_data['photos'],
                            possible_data['videos'],
                            possible_data['share'],
                            possible_data['reactions'])

        chat_ref.add_messages([message])

    def __load_chat(self, json_data: Dict):
        """
        :param json_data: deserialized message json
        :return: nothing
        """
        participants = [x['name'] for x in json_data['participants']]

        is_group_chat = json_data['thread_type'] != 'Regular'

        chat = self.find_chat(json_data['title'], participants, search_groups=is_group_chat)

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

    def from_entry(self, entry: str):
        """
        :param entry: path to single message json file
        :return: nothing
        """
        with open(entry, 'r') as json_file:
            json_data = json.load(json_file)

        self.__load_people(json_data['participants'])
        self.__load_chat(json_data)


class FBChat:
    """
    Class used to represent one singular chat instance (can be group or general 1on1 chat)

    Attributes
    ----------
    title: str
        title of the chat (usually the name of the group chat or name of the other person)
    participants: List[FBPerson]
        list of all persons, that are/were in the chat
    messages: List[FBMessage]
        list of all messages in that chat

    Methods
    -------
    find_participant(self, name: str)
        finds the participant by its' name and returns reference to the FBPerson object of that person
    add_messages(self, messages: List[FBMessage])
        adds all of the messages from the input list to the class attribute
    """
    def __init__(self, title: str, participants: List[FBPerson]):
        """
        :param title: title of chat (usually name of person, or name of group chat)
        :param participants: [FBPerson], list of references to instances of person
        """
        self.title: str = title
        self.participants: List[FBPerson] = participants
        self.messages: List[FBMessage] = []

    def find_participant(self, name: str):
        """
        :param name: name of person, which is to be found in list of participants
        :return: reference to instance of object FBPerson, or None if person is not found
        """
        for participant in self.participants:
            if participant.name == name:
                return participant
        return None

    def add_messages(self, messages: List[FBMessage]):
        """
        :param messages: [FBMessage], list of instances of object FBMessage
        :return: nothing
        """
        for msg in messages:
            if self.find_participant(msg.sender) is not None:
                self.messages.append(msg)


class FBPhoto:
    """
    Class used to represent single instance of Facebook Photo

    Attributes
    ----------
    uri: str
        uri to the source image
    date: datetime
        date of creation of the image (or when it was uploaded)
    """
    def __init__(self, uri: str, timestamp: int):
        """
        :param uri: uri to the source of the image
        :param timestamp: date given in ms
        """
        self.uri = uri
        self.date = datetime.datetime.fromtimestamp(timestamp / 1000.0)


class FBVideo:
    """
    Class used to represent single instance of Facebook Video

    Attributes
    ----------
    uri: str
        uri to the source video
    date: datetime
        date of creation of the video (or when it was uploaded)
    thumbnail: str
        uri to the source image of the thumbnail of the video
    """
    def __init__(self, uri: str, timestamp: int, thumbnail: str):
        """
        :param uri: uri of the source of the video
        :param timestamp: date given in ms
        :param thumbnail: uri of the thumbnail of video
        """
        self.uri = uri
        self.date = datetime.datetime.fromtimestamp(timestamp / 1000.0)
        self.thumbnail = thumbnail


class FBShare:
    """
    Class used to represent Facebook share object

    Attributes
    ----------
    link: str
        link to the share that person posted in a message
    text: str
        text of the share
    """
    def __init__(self, link: str = None, text: str = None):
        """
        :param link: url of Facebook link share
        :param text: text displayed in share
        """
        self.link = link
        self.text = text


class FBReaction:
    """
    Class used to represent a single reaction to a message

    Attributes
    ----------
    actor: FBPerson
        reference to the creator of the reaction
    reaction: str
        what kind of reaction was given
    """
    def __init__(self, person: FBPerson, reaction: str):
        """
        :param person: reference to instance of FBPerson, creator of react
        :param reaction: string, type of reaction
        """
        self.actor = person
        self.reaction = reaction


class FBTypeOfMsg(Enum):  # Enum for the type message (more might be added later)
    """
    Basic enumerator for determining the type of the message
    """
    Unknown = -1  # Not yet discovered type of message
    Generic = 1   # Generic text message
    Share = 2     # Share of link/song/sth


class FBPerson:
    """
    Class to represent single person/user of Facebook

    Attributes
    ----------
    name: str
        name of the person/user
    chats: Dict[str, FBChat]
        dictionary of all chats to which the person belongs
    group_chats: Dict[str, FBChat]
        dictionary of all group chats to which the person belongs

    Methods
    -------
    add_chat(self, chat: FBChat, group_chat: bool = False)
        method used to add chat to the certain person
    """
    def __init__(self, name: str):
        """
        :param name: name of person
        """
        self.name = name
        self.chats = {}
        self.group_chats = {}

    def add_chat(self, chat: FBChat, group_chat: bool = False):
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


class FBMessage:
    """
    Class used to represent a single message sent on Facebook

    Attributes
    ----------
    sender: FBPerson
        reference to the original sender of the message
    date: datetime
        date of the time, when was the image sent
    type: FBTypeOfMsg
        type of message
    content: str, optional
        text/content of the message, if sent
    photos: List[FBPhoto], optional
        list of references to the photos, if sent
    videos: List[FBVideo], optional
        list of references to the videos, if sent
    share: FBShare, optional
        share object, if something (like link or sth) was shared
    reactions: List[FBReaction], optional
        list of references to the reactions, if someone reacted to the message
    """
    def __init__(self, sender: FBPerson, timestamp: int, type_of_msg: FBTypeOfMsg, content: str = None,
                 photos: List[FBPhoto] = None, videos: List[FBVideo] = None, share: FBShare = None,
                 reactions: List[FBReaction] = None):
        """
        :param sender: FBPerson, reference to instance of object of the sender of the message
        :param timestamp: date given in ms
        :param type_of_msg: FBTypeOfMsg
        :param content: optional, string, message content
        :param photos: optional, [FBPhoto], list of FBPhoto objects (if message has photos in it)
        :param videos: optional, [FBVideo], list of FBVideo objects (if message has videos in it)
        :param share: optional, FBShare (if message is type of Share instead of Generic)
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


def fb_message_type_switch(argument: str):
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
