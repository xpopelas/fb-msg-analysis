from models import *
import os


def create_metadata(entries=None):
    """
    :param entries: optional, [string], list of paths to json files
    :return: object FBMetaData, with filled in entries (if given)
    """
    __metadata = FBMetadata()
    if entries is not None:
        for __entry in entries:
            __metadata.from_entry(__entry)
    return __metadata


def find_all_json(start_directory):
    """
    :param start_directory: string, path to directory, from which the search should begin
    :return: [string], list of all paths containing json files
    """
    result = []
    for dir_name, subdir_list, file_list in os.walk(start_directory):
        for file in file_list:
            file = file.strip()
            if file.endswith(".json"):
                result.append(dir_name + '/' + file)
    return result
