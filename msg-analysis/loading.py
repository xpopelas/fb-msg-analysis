from models import *


def create_metadata(entries=None):
    metadata = FBMetadata()
    if entries is not None:
        for entry in entries:
            metadata.load_entry(entry)
    return metadata

