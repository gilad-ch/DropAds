from moviepy.editor import (
    VideoFileClip, concatenate_videoclips, AudioFileClip, 
    TextClip, CompositeVideoClip, afx, CompositeAudioClip
)

import os
import re

def assemble_final_video(
    ranked_clips,
    tts_audio_path,
    ad_script,
    output_path="output/final_ad.mp4",
    min_score_threshold=0.005,
    font="Arial-Bold",
    font_size=48,
    subtitle_duration_per_line=2.5,
    bg_music_path=None,  # New optional parameter
    target_resolution=(1080, 1920),  # TikTok size
    bg_music_volume=0.1,  # Adjust background music volume
):
    """
    Assemble the final video using the highest ranked clips that meet the score threshold,
    mute their original audio, add TTS narration and optional background music,
    and render to TikTok dimensions.

    Args:
        ranked_clips: List of dicts with keys ['start', 'end', 'similarity', 'source']
        tts_audio_path: Path to the generated TTS mp3 file
        ad_script: The spoken ad script (string or list of lines)
        output_path: Path where the final video will be saved
        min_score_threshold: Minimum similarity score for a clip to be included
        font: Font for subtitles
        font_size: Font size for subtitles
        subtitle_duration_per_line: Duration to show each subtitle (if script is a list)
        bg_music_path: Optional path to background music file
        target_resolution: Desired output resolution (width, height)
        bg_music_volume: Volume level for background music
    """
    tts_audio = AudioFileClip(tts_audio_path)
    tts_duration = tts_audio.duration

    if isinstance(ad_script, str):
        ad_lines = re.split(r'[.!?]\s*', ad_script)
        ad_lines = [line.strip() for line in ad_lines if line.strip()]
    else:
        ad_lines = [line.strip() for line in ad_script if line.strip()]

    selected_clips = []
    current_duration = 0.0

    for seg in ranked_clips:
        if seg["similarity"] < min_score_threshold:
            break
        clip_duration = seg["end"] - seg["start"]
        if current_duration + clip_duration > tts_duration:
            break
        try:
            clip = VideoFileClip(seg["source"]).subclip(seg["start"], seg["end"]).without_audio()
            clip = clip.resize(height=target_resolution[1])  # Resize to match TikTok height
            clip = clip.resize(width=target_resolution[0])   # Ensure width matches (crop if needed)
            selected_clips.append(clip)
            current_duration += clip_duration
        except Exception as e:
            print(f"Failed to load clip {seg['source']} from {seg['start']} to {seg['end']}: {e}")

    if not selected_clips:
        raise ValueError("No suitable clips passed the min_score_threshold.")


    # Repeat clips until we reach or exceed the TTS duration
    full_clip_list = []
    repeated_duration = 0

    while repeated_duration < tts_duration:
        for clip in selected_clips:
            if repeated_duration >= tts_duration:
                break
            full_clip_list.append(clip)
            repeated_duration += clip.duration

    # Concatenate and trim to exact duration
    final_video = concatenate_videoclips(full_clip_list, method="compose").subclip(0, tts_duration)


    # Combine TTS and background music if provided
    final_audio = tts_audio
    if bg_music_path:
        try:
            bg_music = AudioFileClip(bg_music_path).subclip(0, tts_duration).volumex(bg_music_volume)
            bg_music = AudioFileClip(bg_music_path).subclip(0, tts_duration).volumex(bg_music_volume)
            bg_music = bg_music.audio_fadein(1).audio_fadeout(1)
            final_audio = CompositeAudioClip([tts_audio, bg_music])

        except Exception as e:
            print(f"Failed to load background music: {e}")

    # Add audio to video
    final_video = final_video.set_audio(final_audio)


    # Create final composite video
    final = CompositeVideoClip([final_video], size=target_resolution).set_duration(tts_duration)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final.write_videofile(output_path, codec="libx264", audio_codec="aac")

    # Cleanup
    for clip in selected_clips:
        clip.close()
    tts_audio.close()
    if bg_music_path:
        bg_music.close()
    final.close()

    return output_path
