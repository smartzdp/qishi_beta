from faster_whisper import WhisperModel
import json
import os
from utils import chunk_audio_segments


def transcribe_audio(audio_file, json_path=None, model_size="large-v3", device="cpu", compute_type="int8", beam_size=3):
    """Transcribe audio file to text using Faster Whisper."""
    
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, info = model.transcribe(audio_file, beam_size=beam_size)
    
    lines = []
    json_file = os.path.join(json_path, os.path.basename(audio_file) + ".json") if json_path else None
    
    if json_file and os.path.exists(json_file):
        with open(json_file, "r") as f:
            lines = json.load(f)
        for line in lines:
            print("[%.2fs -> %.2fs] %s" % (line["start"], line["end"], line["text"]))
    else:
        for segment in segments:
            line = {"start": segment.start, "end": segment.end, "text": segment.text}
            print("[%.2fs -> %.2fs] %s" % (line["start"], line["end"], line["text"]))
            lines.append(line)
        if json_file:
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(lines, f, indent=2, ensure_ascii=False)
    
    metadata = {
        "language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration,
    }

    return metadata, lines


