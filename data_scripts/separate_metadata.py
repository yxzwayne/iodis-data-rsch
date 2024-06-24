# This file assumes that we are given a central file named "iodis.jsonl" 
# where it contains every bit of info. 
# The purpose of this script is to separate the metadata from the main transcription.

import jsonlines


metadata = []
with jsonlines.open("../iodis.jsonl") as reader:
    for obj in reader:
        metadata.append({"video_id": obj["video_id"], "title": obj["title"], "description": obj["description"], "thumbnail": obj["thumbnail"]})

with jsonlines.open(f"../iodis_metadata.jsonl", mode="w") as writer:
    for obj in metadata:
        writer.write(obj)