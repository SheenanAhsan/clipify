import subprocess
import whisper
import os

# === Helper: Convert timestamp format ===
def format_timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# === Step 1: Trim video ===
def trim_video(input_file, start_time, end_time, output_file):
    subprocess.run([
        "ffmpeg", "-y", "-i", input_file,
        "-ss", start_time, "-to", end_time,
        "-c", "copy", output_file
    ])

# === Step 2: Generate subtitles using Whisper ===
def generate_subtitles(input_video):
    model = whisper.load_model("small")
    result = model.transcribe(input_video)
    with open("subs.srt", "w") as f:
        for i, seg in enumerate(result["segments"], start=1):
            f.write(f"{i}\n")
            f.write(f"{format_timestamp(seg['start'])} --> {format_timestamp(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")

# === Step 3: Convert to vertical 9:16 ===
def convert_to_vertical(input_file, output_file):
    subprocess.run([
        "ffmpeg", "-y", "-i", input_file,
        "-vf",
        "scale=2304:1296,pad=2304:1920:(ow-iw)/2:(oh-ih)/2:black,crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2",
        "-c:a", "copy", output_file
    ])

# === Step 4: Add subtitles & music ===
def add_effects(input_video, subtitles, music, output_file):
    subprocess.run([
        "ffmpeg", "-y",
        "-i", input_video,
        "-i", music,
        "-vf", f"subtitles={subtitles}:force_style='Fontsize=28,PrimaryColour=&HFFFFFF&'",
        "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=shortest",
        "-c:v", "libx264", "-c:a", "aac",
        "-shortest", output_file
    ])

# === Main pipeline ===
if __name__ == "__main__":
    input_video = "twitch_clip.mp4"
    bg_music = "bg_music.mp3"

    print("🎬 Trimming clip...")
    trim_video(input_video, "00:00:05", "00:00:23", "highlight.mp4")

    print("💬 Generating subtitles...")
    generate_subtitles("highlight.mp4")

    print("📱 Converting to vertical format...")
    convert_to_vertical("highlight.mp4", "vertical.mp4")

    print("🎵 Adding subtitles and music...")
    add_effects("vertical.mp4", "subs.srt", bg_music, "final_short.mp4")

    print("\n✅ Done! Check your folder for 'final_short.mp4'")
