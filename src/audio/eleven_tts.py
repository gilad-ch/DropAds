import os
import uuid
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

load_dotenv()



def tts(text: str, filename: str = None) -> str:
    client = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY"),
)
    
    response = client.text_to_speech.convert(
        text=text,
        voice_id="pNInz6obpgDQGcFmaJgB", 
        model_id="eleven_turbo_v2_5",
        output_format="mp3_22050_32",  
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True,
            speed=1.0,
        ),
    )

    if not filename:
        filename = f"{uuid.uuid4()}.mp3"

    with open(filename, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    print(f"Audio saved to: {filename}")
    return filename
