# Description

This repo should contain the transcript data from [Harstem](https://www.youtube.com/@Harstem)'s video series "Is it imba or do I suck?" This is created for research and practice purporses, where I currently practice implementing BM25 and semantic search from scratch.

I also include Python scripts for data collection and processing. Ideally, I should have some maintained way of updating data as new videos come in. Fortunately the growing compute outruns Harstem's upload speed, meaning I can just reliably search against the metadata file to check for any new videos.

# Current data cut off

Jun 10, 2024

# Data pipeline

1. Parse the playlist for any new videos
   1. this requires a record of existing video ids: done in supabase db
2. obtain info of the new videos and add record to supabase db
3. download audio of the new videos
4. transcribe audio of the new videos
5. chunk transcript, add text to supabase db
6. obtain embeddings for chunks and add embeddings to supabase db

# Cloning the mlx-parallm submodule ran by will brown

`git submodule update --init --recursive`