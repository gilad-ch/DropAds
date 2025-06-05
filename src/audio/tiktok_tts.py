import base64
import os
import requests
from dotenv import load_dotenv
from pydub import AudioSegment

load_dotenv()
TIKTOK_SESSIONID = os.getenv("TIKTOK_SESSIONID")
API_BASE_URL = "https://api16-normal-v6.tiktokv.com/media/api/text/speech/invoke/"
USER_AGENT = "com.zhiliaoapp.musically/2022600030 (Linux; U; Android 7.1.2; es_ES; SM-G988N; Build/NRD90M;tt-ok/3.12.13.1)"

MAX_WORDS = 30

def sanitize(text):
    text = text.replace("+", "plus").replace(" ", "+")
    text = text.replace("&", "and").replace("ä", "ae").replace("ö", "oe")
    text = text.replace("ü", "ue").replace("ß", "ss")
    return text

def request_tts_chunk(text, speaker):
    req_text = sanitize(text)
    response = requests.post(
        f"{API_BASE_URL}?text_speaker={speaker}&req_text={req_text}&speaker_map_type=0&aid=1233",
        headers={
            'User-Agent': USER_AGENT,
            'Cookie': f'sessionid={TIKTOK_SESSIONID}'
        }
    )
    json_data = response.json()

    if json_data.get("message") == "Couldn't load speech. Try again.":
        raise Exception("Invalid TikTok Session ID or API error.")

    vstr = json_data["data"]["v_str"]
    return base64.b64decode(vstr)

def split_text(text, max_words=MAX_WORDS):
    words = text.split()
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]

def tts(text_speaker="en_us_002", req_text="TikTok Text To Speech", filename="voice.mp3"):
    chunks = split_text(req_text)
    final_audio = AudioSegment.empty()

    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}: {chunk}")
        try:
            audio_data = request_tts_chunk(chunk, text_speaker)
            temp_filename = f"temp_chunk_{i}.mp3"
            with open(temp_filename, "wb") as temp_file:
                temp_file.write(audio_data)
            final_audio += AudioSegment.from_file(temp_filename)
            os.remove(temp_filename)
        except Exception as e:
            print(f"Error processing chunk {i+1}: {e}")
            continue

    final_audio.export(filename, format="mp3")
    print(f"✅ Final audio saved to {filename}")
    return filename
