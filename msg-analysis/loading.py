from models import *


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
