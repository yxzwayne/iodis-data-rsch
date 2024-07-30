import re
import jsonlines
import random
from openai import OpenAI


SYSTEM = "You are a helpful assistant and an expert at catching and fixing Starcraft 2 transcripts."

chat_records = []
with jsonlines.open("transcript_fix_record.jsonl") as reader:
    for obj in reader:
        chat_records.append(obj)


client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

rolled_pair = random.choice(chat_records)

completion = client.chat.completions.create(
    model="NousResearch/Hermes-2-Pro-Llama-3-8B-GGUF",
    messages=[
        {"role": "system", "content": SYSTEM},
        {
            "role": "user",
            "content": rolled_pair["input"]
            + "\nDo not wrap anything to any terminologies.",
        },
    ],
    temperature=1,
)

input_transcript = re.search(
    r"<transcript>(.*?)</transcript>",
    rolled_pair["input"],
    re.DOTALL,
)
print(
    f"\n\nGiven the following input transcript:\n{input_transcript.group(1).strip()}\n"
)
print(
    f"\nLocal LM is able to give this output:\n{completion.choices[0].message.content}\n"
)
corrected_script = re.search(
    r"<fixed_script>(.*?)</fixed_script>",
    completion.choices[0].message.content,
    re.DOTALL,
)
if corrected_script:
    print(
        f" - We can parse <fixed_transcript> from the output. Parsed result:\n{corrected_script.group(1).strip()}\n\n"
    )
else:
    print(f" - We cannot parse <fixed_transcript> from this output.")
