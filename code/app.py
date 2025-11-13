import os
import subprocess
from faster_whisper import WhisperModel
import srt
from datetime import timedelta
import re

# === Helper: Convert timestamp format ===
# def format_timestamp(seconds):
#     h = int(seconds // 3600)
#     m = int((seconds % 3600) // 60)
#     s = int(seconds % 60)
#     ms = int((seconds - int(seconds)) * 1000)
#     return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# === Step 1: Trim video ===
# def trim_video(input_file, start_time, end_time, output_file):
#     subprocess.run([
#         "ffmpeg", "-y",
#         "-i", input_file,
#         "-ss", start_time,  # switch between -ss and -i to find what works
#         "-to", end_time,
#         "-c", "copy", output_file
#     ])

def generate_bounce_subtitles(input_video):
    model = WhisperModel("medium.en", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(input_video, word_timestamps=True, vad_filter=True)

    output_ass = "subs.ass"

    # Header (basic style)
    header = """[Script Info]
Title: Bouncy Subtitles
ScriptType: v4.00+
Collisions: Normal
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,sans-serif,100,&H00FFFFFF,&H00000000,-1,1,4,0,2,50,50,500,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    # Helper for ASS timestamp
    def ass_time(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds - int(seconds)) * 100)
        return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"

    # Build dialogue lines
    events = ""

    fixed_up = 150   # ms bounce up
    fixed_down = 110  # ms bounce down

    for seg in segments:
        for w in seg.words or []:
            start = w.start
            # end = min(w.end + 0.15, seg.end)  # keep short and tight
            end = min(w.end, seg.end)  # keep short and tight
            text = re.sub(r'[^\w\s]', '', w.word.lower().strip())  # lowercase + remove punctuation
            if not text:
                continue

            # Bounce effect using scaling over the first ~1/5 of the duration
            duration = max(0.001, end - start)
            # up = duration / 5
            # down = duration / 10
            # ASS expects centiseconds (1/100 of a second)
            up_cs = fixed_up / 10   # 100 ms = 10 cs
            down_cs = (fixed_up + fixed_down) / 10  # add both parts for proper timing

            # events += (
            #     f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,"
            #     f"{{\\fscx60\\fscy60\\t(0,{int(up*1000)},\\fscx120\\fscy120)\\t({int(up*1000)},{int(down*1000)},\\fscx100\\fscy100)}}{text}\n"
            # )
            events += (
                f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,"
                f"{{\\fscx80\\fscy80"
                f"\\t(0,{up_cs},\\fscx120\\fscy120)"          # bounce up
                f"\\t({up_cs},{down_cs},\\fscx100\\fscy100)"  # bounce down
                f"}}{text}\n"
            )

    with open(output_ass, "w", encoding="utf-8") as f:
        f.write(header + events)

    print(f"✅ Generated animated ASS subtitles → {output_ass}")


# === Step 2: Generate subtitles using Faster-Whisper ===
def generate_subtitles(input_video, max_words=3):
    output_srt="subs.srt"
    model_size = "medium.en"
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(input_video, word_timestamps=True, vad_filter=True)

    captions = []
    for seg in segments:
        words = seg.words
        if not words:
            continue
        for i in range(0, len(words), max_words):
            group = words[i:i+max_words]
            start = group[0].start
            end = group[-1].end
            text = "".join([w.word for w in group]).strip().lower()
            text = re.sub(r"[^\w\s']", "", text)  # remove anything not a letter/number/space
            captions.append((start, end, text))

    # Write to SRT
    subs = []
    for i, (start, end, text) in enumerate(captions, 1):
        subs.append(
            srt.Subtitle(
                index=i,
                start=timedelta(seconds=start),
                end=timedelta(seconds=end),
                content=text.strip()
            )
        )

    with open(output_srt, "w", encoding="utf-8") as f:
        f.write(srt.compose(subs))

    print(f"✅ Generated {len(subs)} short subtitles → {output_srt}")

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
        #"-vf", f"subtitles={subtitles}:force_style='Fontname=sans-serif,Fontsize=15,Bold=-1,Outline=1,OutlineColour=&H000000&,PrimaryColour=&HFFFFFF&,Alignment=2,MarginV=85'",
        "-vf", f"ass={subtitles}",
        "-filter_complex", "[1:a]volume=0.3[a1];[0:a][a1]amix=inputs=2:duration=shortest",
        "-c:v", "libx264", "-c:a", "aac",
        "-shortest", output_file
    ])

# === Main pipeline ===
if __name__ == "__main__":
    input_video = "sunset_ace.mp4"
    highlight = "twitch_clip.mp4"
    vertical = "vertical.mp4"
    bg_music = "bg_music.mp3"

    # start_of_trim = "00:00:20"
    # end_of_trim = "00:00:40"

    #print("🎬 Trimming clip...")
    #trim_video(input_video, start_of_trim, end_of_trim, highlight)

    print("💬 Generating subtitles...")
    # generate_subtitles(highlight)
    generate_bounce_subtitles(highlight)

    print("📱 Converting to vertical format...")
    convert_to_vertical(highlight, vertical)

    print("🎵 Adding subtitles and music...")
    # add_effects(vertical, "subs.srt", bg_music, "final_short.mp4")
    add_effects(vertical, "subs.ass", bg_music, "final_short.mp4")

    print("\n✅ Done! Check your folder for 'final_short.mp4'")