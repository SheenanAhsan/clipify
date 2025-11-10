import subprocess
import whisper

def trim_video(input_file, start_time, end_time, output_file):
    subprocess.run([
        "ffmpeg", "-i", input_file,
        "-ss", start_time, "-to", end_time,
        "-c", "copy", output_file
    ])

def generate_subtitles(input_video):
    model = whisper.load_model("small")
    result = model.transcribe(input_video)
    # Save as SRT file
    with open("subs.srt", "w") as f:
        for i, segment in enumerate(result["segments"], start=1):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()
            f.write(f"{i}\n")
            f.write(f"{format_timestamp(start)} --> {format_timestamp(end)}\n")
            f.write(f"{text}\n\n")

def format_timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def convert_to_vertical(input_file, output_file):
    subprocess.run([
        "ffmpeg", "-i", input_file,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:a", "copy", output_file
    ])

def add_effects(input_video, subtitles, music, output_file):
    subprocess.run([
        "ffmpeg",
        "-i", input_video,
        "-i", music,
        "-vf", f"subtitles={subtitles}:force_style='Fontsize=24,PrimaryColour=&HFFFFFF&'",
        "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=shortest",
        "-c:v", "libx264", "-c:a", "aac",
        "-shortest", output_file
    ])
