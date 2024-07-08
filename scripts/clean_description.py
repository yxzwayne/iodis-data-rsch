import re
import json
import time
from tqdm import tqdm
import anthropic
from dotenv import load_dotenv

load_dotenv()

GUIDANCE = """
Given the following description text content of a YouTube video, please clean up the description by removing any social or promotional contents and links. If the description is already clean, no need to do anything to it. Directly return the text of the resulting description wrapped in <cleaned_description> tag.
"""


def main():
    with open("../iodis_video_info.json", "r") as f:
        video_info = json.load(f)

    client = anthropic.Anthropic()

    for video in tqdm(video_info):
        response = client.messages.create(
            max_tokens=1024,
            model="claude-3-5-sonnet-20240620",
            system="You are a helpful assistant that cleans up descriptions of YouTube videos.",
            messages=[
                {
                    "role": "user",
                    "content": f"{GUIDANCE}\n\n\"\"\"\n{video['description']}\n\"\"\"",
                }
            ],
        )

        cleaned_description = re.search(
            r"<cleaned_description>(.*?)</cleaned_description>",
            response.content[0].text,
            re.DOTALL,
        )
        video["description"] = (
            cleaned_description.group(1).rstrip()
            if cleaned_description
            else video["description"]
        )

        time.sleep(0.11)

    with open("../iodis_video_info.json", "w") as f:
        json.dump(video_info, f)


if __name__ == "__main__":
    main()
