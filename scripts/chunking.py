# This file assumes that we are given a central file named "iodis.jsonl" 
# where it contains every bit of info. 
# The purpose of this script is to chunk the main transcription 
# and create or update a separate file.

import jsonlines
from tqdm import tqdm

ids, documents = [], []

with jsonlines.open("../iodis.jsonl") as reader:
    for obj in reader:
        ids.append(obj["video_id"])
        documents.append(obj["text"])


assert len(ids) == len(documents)

chunked_docs = [] # each record in this list will be a key value pair of {"video_id": "...", "chunk": "..."}

for di, d in tqdm(enumerate(documents)):
    vid = ids[di] # getting the video id from previous constructs
    doc_chunks = []
    sentences = d.split(".")
    curr_chunk = ""
    overlap_sentence = ""

    for s in sentences:
        s = s.strip() + ". "
        if len((curr_chunk + s).split()) > 96:
            if curr_chunk:
                doc_chunks.append(curr_chunk.strip())
            curr_chunk = overlap_sentence + s
            overlap_sentence = s
        else:
            curr_chunk += s
            overlap_sentence = s

    if curr_chunk:
        doc_chunks.append(curr_chunk.strip())

    for chunk in doc_chunks:
        chunked_docs.append({"video_id": vid, "chunk": chunk})

with jsonlines.open("../iodis_chunks.jsonl", "w") as writer:
    for doc in chunked_docs:
        writer.write(doc)