#!/usr/bin/env python3
"""
DropAds: Automated TikTok Ad Generator for Dropshipping Products
"""

import os
from video.assembler import assemble_final_video
from video.clipSelector import ClipSelector
from audio.tts import create_ad_voiceover
from audio.eleven_tts import tts
from ai.openAI import prompt_image, prompt_llm
from config.prompts import create_product_description, create_ad_script, create_embeding_prompt

clip_controller = ClipSelector()

def create_ad(
    product_image_path: str,
    media_assets_dir: str,
    target_length: int = 30,
    background_music: str = None,
    output_path: str = "output/final_ad.mp4",
    
):
    """
    Create a TikTok ad for a dropshipping product.
    
    Args:
        product_image_path: Path to the main product image
        media_assets_dir: Directory containing additional media assets (videos, images)
        target_length: Target length of the final ad in seconds
        output_path: Path where the final ad will be saved
    """
    # Step 1: Detect product and generate description
    print("Detecting product...")
    print("Generating product description...")
    product_description = prompt_image(user_prompt=create_product_description['user_prompt'],system_prompt=create_product_description['system_prompt'], image_path=product_image_path)
    print(f"Product description: {product_description} ")

    embeding_prompt = prompt_llm(prompt=create_embeding_prompt['user_prompt'].format(product_description=product_description), system_message=create_embeding_prompt['system_prompt'])
    print(f"Clips embeding prompt: {embeding_prompt} - writing ad script")
    
    ad_script = prompt_llm(prompt=create_ad_script['user_prompt'].format(product_description=product_description), system_message=create_ad_script['system_prompt'])
    print(f"Ad script: {ad_script}")

    # Step 2: Ranking video clips
    print("ranking video clips...")
    video_paths = [os.path.join(media_assets_dir, f) for f in os.listdir(media_assets_dir) 
                  if f.endswith(('.mp4', '.mov', '.avi'))]
    ranked_clips = clip_controller.get_ranked_clips(video_paths=video_paths, embedding_prompt=embeding_prompt)
    
    # Step 4: Generate audio (TTS)
    print("Generating speech audio...")
    # tts_path = create_ad_voiceover(ad_input=ad_script, output_path=os.path.join("temp", "tts.mp3"))
    tts_path = tts(text=ad_script, filename=os.path.join("temp", "tts.mp3"))
    
    print("Assembling final video...")
    final_video_path = assemble_final_video(
        ranked_clips=ranked_clips,
        tts_audio_path=tts_path,
        ad_script=ad_script,  # the raw string or list
        output_path=output_path, bg_music_path=background_music
    )
    print(f"Ad generation complete! Saved to: {final_video_path}")


def main():

    current_path = os.path.dirname(os.path.abspath(__file__))
    product_image = os.path.join(current_path, 'assets', 'images', 'image.png')
    background_music = os.path.join(current_path, 'assets', 'audio', 'chill.mp3')
    media_dir = os.path.join(current_path, 'assets', 'clips')
    output_path = os.path.join(current_path, 'output', 'final.mp4')
    
    create_ad(product_image, media_dir,background_music=background_music, output_path=output_path)


if __name__ == "__main__":
    main() 