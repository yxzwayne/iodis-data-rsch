# use LLMs and prompting to fix the incorrectly transcribed terms.
import os
import re
import json
import time
import jsonlines

from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()


### Anthropic inference ###
# import anthropic
# client = anthropic.Anthropic()

### OpenAI inference ###
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

###  Local inference ###
# import mlx_parallm

# # from mlx_parallm.utils import load, generate, batch_generate
# from mlx_parallm import utils


SYSTEM = "You are a helpful assistant and an expert at catching and fixing Starcraft 2 transcripts."
LOGGING_FILE = "../transcript_fix_record.jsonl"  # leave blank if don't want logging


def log_interaction(input_text, output_text):
    if LOGGING_FILE:
        with jsonlines.open(LOGGING_FILE, mode="a") as writer:
            writer.write({"input": input_text, "output": output_text})


def fix_transcript(text, terminology):
    fixing_prompt = f"""
    The following transcript is largely correct, but because it is about Starcraft 2 gameplay, the transcript contains many mistakes of terminology, as well as many incorrect period positions.

    Please correct the transcript with the given terminology list, and make sure that all terms that seems to be a terminology is correct. For period mistakes, an example is: \"Welcome back to another. Is it Inba or do I suck?\", which should be \"Welcome back to another Is it Inba or do I suck?\". Sometimes, there would be a period in place of a comma or nothing, and you need to sort it out. Do not change everything else that is not a terminology or period mistake. 

    Return the correct script within the <fixed_script></fixed_script> tags. Before you begin fixing, think step by step in your <scratchpad>.

    <terminology>
    {terminology}
    </terminology>

    <transcript>
    {text}
    </transcript>
    """
    return fixing_prompt


with open("../iodis_transcripts.json", "r") as f:
    transcripts = json.load(f)


# fix the transcripts in place and save them back to original file.
if __name__ == "__main__":
    with open("../sc_terminologies.txt", "r") as f:
        terminology = f.readlines()
        terminology = ", ".join([t.strip().rstrip() for t in terminology])

    for transcript in transcripts:
        video_name = transcript["title"]
        transcript["text"] = re.sub(r"[\s\n]+", " ", transcript["text"])
        transcript["text"] = transcript["text"].strip().rstrip()
        text = transcript["text"]

        sentences = text.split(".")
        joined_sentences = []
        current_sentence = []
        word_count = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            words = sentence.split()
            if word_count + len(words) <= 128:
                current_sentence.extend(words)
                word_count += len(words)
            else:
                if current_sentence:
                    joined_sentences.append(" ".join(current_sentence) + ".")
                current_sentence = words
                word_count = len(words)

        if current_sentence:
            joined_sentences.append(" ".join(current_sentence) + ".")

        # by this point, joined_sentences should be a list of sentences, each less than or around 128 words.
        # we can now use anthropic to fix the sentences, and join them back to form back the original transcript with corrected terms.

        print(f"\n*** Processing {video_name} ***")
        corrected_sentences = []
        for sentence in tqdm(joined_sentences, desc="Fixing sentences"):
            fixing_prompt = fix_transcript(sentence, terminology)

            ### Anthropic syntax ###
            # fixing_response = client.messages.create(
            #     model="claude-3-5-sonnet-20240620",
            #     max_tokens=1920,
            #     system="You are a helpful assistant and an expert at catching and fixing Starcraft 2 transcripts.",
            #     messages=[{"role": "user", "content": fixing_prompt}],
            # )F
            # response_content = fixing_response.content[0].text

            ### OpenAI syntax ###
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": fixing_prompt},
                ],
            )
            response_content = completion.choices[0].message.content

            log_interaction(fixing_prompt, response_content)

            time.sleep(1)
            # extracting the fixed transcript from <fixed_script> tag.
            corrected_script = re.search(
                r"<fixed_script>(.*?)</fixed_script>", response_content, re.DOTALL
            )
            if corrected_script:
                corrected_sentences.append(corrected_script.group(1).strip())
            else:
                corrected_sentences.append(
                    sentence
                )  # If no correction found, keep the original

        transcript["text"] = " ".join(corrected_sentences)


with open("../iodis_transcripts.json", "w") as f:
    json.dump(transcripts, f)
