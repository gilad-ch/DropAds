import asyncio
import edge_tts
import os

async def generate_tts(text, output_path="voiceover.mp3", voice="en-US-GuyNeural", rate="+15%"):
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(output_path)
    print(f"[+] Voiceover saved to {output_path}")

def create_ad_voiceover(ad_input, output_path="voiceover.mp3"):
    if isinstance(ad_input, str):
        import re
        ad_lines = re.split(r'[.!?]\\s*', ad_input)
        ad_lines = [line.strip() for line in ad_lines if line.strip()]
    else:
        ad_lines = ad_input

    script = " ".join(ad_lines)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    asyncio.run(generate_tts(script, output_path=output_path))
    return output_path


