import json


def count_reacts(json_data_inp):
    """

    :param json_data_inp: list of all json deserialized objects
    :return: dict with key = name and value = number of total reacts made
    """
    final_res = {}

    for data in json_data_inp:
        for m in data['messages']:
            if 'reactions' in m:
                for r in m['reactions']:
                    if r['actor'] in final_res:
                        final_res[r['actor']] += 1
                    else:
                        final_res[r['actor']] = 1

    return final_res


def count_occurrence(json_data_inp, keyword, sender=None, use_lowercase=True):
    """

    :param json_data_inp: list of all json deserialized objects
    :param keyword: search phrase
    :param sender: name of sender, optional arg
    :param use_lowercase: whether lowercase should be used, optional arg
    :return: int, total number of messages with occurrence of keyword
    """
    result = 0

    if use_lowercase:
        keyword = keyword.lower()

    for data in json_data_inp:
        for m in data['messages']:
            if 'content' in m and (sender is None or sender in m['sender_name']):
                cont = m['content']
                if use_lowercase:
                    cont = cont.lower()
                if keyword in cont:
                    result += 1

    return result


def load_all_json_files(entries):
    """

    :param entries: list of strings (paths to json files)
    :return: list of all deserialized json objects
    """
    res_data = []

    for me in entries:
        with open(me, 'r', encoding='UTF-8') as json_file:
            res_data.append(json.load(json_file))

    return res_data

