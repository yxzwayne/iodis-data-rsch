import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from tqdm import tqdm
from pytube import YouTube
import jsonlines
import os
import json

# Constants
DEVICE = "mps"
MODEL_ID = "distil-whisper/distil-large-v3"
VIDEO_INFO_PATH = "../iodis_video_info.json"
PARSED_FILE_PATH = "../iodis_transcripts.json"
WAV_OUTPUT_PATH = "../wav"

# Model setup
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    MODEL_ID, low_cpu_mem_usage=True, use_safetensors=True, attn_implementation="sdpa"
).to(DEVICE)

processor = AutoProcessor.from_pretrained(MODEL_ID)

pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    device=DEVICE,
)

# Load existing transcripts
existing_transcripts = []
if os.path.exists(PARSED_FILE_PATH):
    with open(PARSED_FILE_PATH, "r") as f:
        existing_transcripts = json.load(f)

existing_video_ids = {transcript["video_id"] for transcript in existing_transcripts}

# Load video info
with open(VIDEO_INFO_PATH, "r") as f:
    video_info = json.load(f)

# Process videos
for video in tqdm(video_info, desc="Downloading and Transcribing videos..."):
    if video["video_id"] in existing_video_ids:
        continue

    yt = YouTube(f"https://www.youtube.com/watch?v={video['video_id']}")

    try:
        local_title = yt.title.replace("/", "_")
        wav_path = f"{WAV_OUTPUT_PATH}/{local_title}.wav"

        yt.streams.get_audio_only().download(
            output_path=WAV_OUTPUT_PATH, filename=f"{local_title}.wav", max_retries=5
        )
        print(f" ~~ Transcribing: {local_title}")
        result = pipe(wav_path, batch_size=16)
        video["text"] = result["text"].rstrip()

        existing_transcripts.insert(0, video)

        with open(PARSED_FILE_PATH, "w") as f:
            json.dump(existing_transcripts, f, indent=2)

    except Exception as e:
        print(f"Error processing video {video['video_id']}: {str(e)}")

    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)
