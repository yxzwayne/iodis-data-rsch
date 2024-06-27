import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from tqdm import tqdm
from pytube import YouTube
import jsonlines
import os
import json

device = "cuda" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model_id = "distil-whisper/distil-large-v3"

model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True, attn_implementation="sdpa"
)
model.to(device)

processor = AutoProcessor.from_pretrained(model_id)

pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    torch_dtype=torch_dtype,
    device=device,
)


with open("iodis_video_info.json", "r") as f:
    video_info = json.load(f)


parsed_file_path = "iodis.jsonl"
if os.path.exists(parsed_file_path):
    with open(parsed_file_path, "r") as f:
        existing_transcripts = jsonlines.Reader(f)
        existing_titles = [existing_transcript["title"] for existing_transcript in existing_transcripts]
else:
    existing_transcripts = []
    existing_titles = []

for video in tqdm(video_info, desc="Downloading and Transcribing videos..."):
    video_id = video["video_id"]
    watch_url = f"https://www.youtube.com/watch?v={video_id}"
    yt = YouTube(watch_url)
    try:
        title = yt.title
    except:
        continue
    
    if title in existing_titles:
        continue
    
    stream = (
        yt.streams.get_audio_only()
    )  # This automatically gets the highest bitrate audio stream
    local_title = title.replace("/", "_")
    downloaded = stream.download(output_path="wav", filename=f"{local_title}.wav", max_retries=5)

    # Transcribe the image using whisper
    result = pipe(f"wav/{local_title}.wav", batch_size=16)
    text = result["text"].rstrip()
    video["text"] = text

    os.remove(f"wav/{local_title}.wav")

    # saving the transcript to json
    # iodis_transcripts.append(video)
    with jsonlines.open(parsed_file_path, mode="a") as writer:
        writer.write(video)
