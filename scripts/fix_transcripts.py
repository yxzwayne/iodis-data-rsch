import os
import re
import json
import time
from typing import List, Dict

import jsonlines
from tqdm import tqdm
from dotenv import load_dotenv

# from openai import OpenAI

import anthropic

load_dotenv()

SYSTEM = "You are a helpful assistant and an expert at catching errors in Starcraft 2 transcripts and fixing them."
LOGGING_FILE = "../transcript_fix_record.jsonl"
INPUT_FILE = "../iodis_transcripts.json"
OUTPUT_FILE = "../iodis_transcripts_fixed.json"
TERMINOLOGY_FILE = "../sc_terminologies.txt"

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = anthropic.Anthropic()


def log_interaction(input_text: str, output_text: str) -> None:
    if LOGGING_FILE:
        with jsonlines.open(LOGGING_FILE, mode="a") as writer:
            writer.write({"input": input_text, "output": output_text})


def fix_transcript(text: str, terminology: str) -> str:
    fixing_prompt = f"""
    The following transcript is largely correct, but because it is about Starcraft 2 gameplay, the transcript may contain mistakes of terminology, as well as incorrect period positions. If it does contain errors, please correct the transcript according to the given terminology list, and make sure that all terms that seems to be a terminology is corrected. For period mistakes, an example is: \"Welcome back to another. Is it Inba or do I suck?\", which should be \"Welcome back to another Is it Inba or do I suck?\". Do not change anything else that is not a terminology or period mistake.

    Return the correct script within the <fixed_script></fixed_script> tags. Before you begin fixing, think step by step in your <scratchpad>.

    <terminology>
    {terminology}
    </terminology>

    <transcript>
    {text}
    </transcript>
    """
    return fixing_prompt


def split_into_chunks(text: str, max_words: int = 128) -> List[str]:
    sentences = text.split(".")
    chunks = []
    current_chunk = []
    word_count = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        words = sentence.split()
        if word_count + len(words) <= max_words:
            current_chunk.extend(words)
            word_count += len(words)
        else:
            if current_chunk:
                chunks.append(" ".join(current_chunk) + ".")
            current_chunk = words
            word_count = len(words)

    if current_chunk:
        chunks.append(" ".join(current_chunk) + ".")

    return chunks


def process_chunk(chunk: str, terminology: str) -> str:
    fixing_prompt = fix_transcript(chunk, terminology)

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            system=SYSTEM,
            messages=[
                {"role": "user", "content": fixing_prompt},
            ],
        )
        response_content = message.content[0].text
        log_interaction(fixing_prompt, response_content)

        time.sleep(1)

        # Try to match with closing tag first
        corrected_script = re.search(
            r"<fixed_script>(.*?)</fixed_script>", response_content, re.DOTALL
        )
        if corrected_script:
            return corrected_script.group(1).strip()

        # If closing tag is not found, match everything after opening tag up to the end
        corrected_script = re.search(
            r"<fixed_script>(.*?)($|</)", response_content, re.DOTALL
        )
        return corrected_script.group(1).strip() if corrected_script else chunk
    except Exception as e:
        raise RuntimeError(f"Error processing chunk: {e}")


def process_transcript(transcript: Dict, terminology: str) -> Dict:
    video_name = transcript["title"]
    text = re.sub(r"[\s\n]+", " ", transcript["text"]).strip()

    print(f"\n*** Processing {video_name} ***")
    chunks = split_into_chunks(text)
    corrected_chunks = []

    for chunk in tqdm(chunks, desc="Fixing chunks"):
        corrected_chunk = process_chunk(chunk, terminology)
        corrected_chunks.append(corrected_chunk)
        time.sleep(1)

    transcript["text"] = " ".join(corrected_chunks)
    return transcript


def main():
    fixed_records = []
    with open(TERMINOLOGY_FILE, "r") as f:
        terminology = ", ".join([t.strip() for t in f.readlines()])

    with open(INPUT_FILE, "r") as f:
        transcripts = json.load(f)

    for i, transcript in enumerate(transcripts):
        try:
            fixed_transcript = process_transcript(transcript, terminology)
            fixed_records.append(fixed_transcript)
        except Exception as e:
            print(f"Error occurred while processing transcript: {transcript['title']}")
            print(f"Error details: {e}")
            print(f"Processed {i} transcripts before encountering this error.")
            break  # Stop processing further transcripts

        # Save progress after each transcript
        with open(OUTPUT_FILE, "w") as f:
            json.dump(fixed_records, f)

    print("Script execution completed.")


if __name__ == "__main__":
    main()
