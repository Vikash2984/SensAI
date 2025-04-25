import os, sys, io, re, wave, queue, asyncio, threading
import numpy as np, pyaudio, pygame, keyboard, requests
import win32gui
from dotenv import load_dotenv
from groq import Groq
from gtts import gTTS
from playsound import playsound
from sensai import sens

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
chunk_file, input_q, record_flag = 'temp_audio_chunk.wav', queue.Queue(), threading.Event()
pygame.mixer.init()

def is_silence(data, threshold=1000): return np.max(np.abs(data)) <= threshold

def record(file_path):
    format, chans, rate, chunk = pyaudio.paInt16, 1, 16000, 1024
    audio = pyaudio.PyAudio()
    stream = audio.open(format=format, channels=chans, rate=rate, input=True, frames_per_buffer=chunk)
    frames = []
    sys.stdout.write('\r' + ' ' * 80 + '\r🎙 Recording... (Hold insert)'); sys.stdout.flush()
    try:
        while keyboard.is_pressed('insert'): frames.append(stream.read(chunk))
    except Exception as e: print(f"Recording error: {e}")
    stream.stop_stream(); stream.close(); audio.terminate()
    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(chans); wf.setsampwidth(audio.get_sample_size(format)); wf.setframerate(rate)
        wf.writeframes(b''.join(frames))
    try:
        with wave.open(file_path, 'rb') as wf: data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        if is_silence(data): os.remove(file_path); return True
        return False
    except Exception as e: print(f"Audio error: {e}"); return False

def transcribe(file_path):
    try:
        with open(file_path, "rb") as f:
            b = io.BytesIO(f.read()); b.name = os.path.basename(file_path)
            return groq_client.audio.transcriptions.create(model="whisper-large-v3-turbo", file=b).text
    except Exception as e: print(f"Transcription error: {e}")

def strip_emoji(text):
    return re.sub(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
                  r"\U0001F1E0-\U0001F1FF\U00002700-\U000027BF\U0001F900-\U0001F9FF"
                  r"\U00002600-\U000026FF\U00002B00-\U00002BFF\U00002000-\U000023FF]+", '', text)

def play(text):
    try:
        headers = {
            "xi-api-key": os.getenv("ELEVEN_LABS_API_KEY"),
            "Content-Type": "application/json"
        }
        voices = requests.get("https://api.elevenlabs.io/v1/voices", headers=headers).json()["voices"]
        brian_id = next(v["voice_id"] for v in voices if v["name"].lower() == "brian")
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.5, "use_speaker_boost": True}
        }
        res = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{brian_id}", headers=headers, json=payload)
        with open("output.mp3", "wb") as f: f.write(res.content)
        playsound("output.mp3")
    except Exception as e: print(f"TTS error: {e}")

async def handle_audio(path):
    txt = transcribe(path)
    if txt:
        print("\nPrompt (Voice) : " + txt)
        res = await sens(txt); print("\n>>> " + res); play(res)
    else: print("Transcription failed.")

def get_active_title():
    return win32gui.GetWindowText(win32gui.GetForegroundWindow())

def text_input():
    while True:
        try:
            msg = input("\n>>> ")
            input_q.put(("submit", msg))
        except EOFError: break

def esc_listener():
    main_title = get_active_title()
    while True:
        keyboard.wait('esc')
        if get_active_title() == main_title:
            input_q.put(("exit", ""))
            break

def insert_listener():
    while True:
        keyboard.wait('insert'); record_flag.set()
        while keyboard.is_pressed('insert'): asyncio.run(asyncio.sleep(0.1))

async def main():
    print("\n💬 Start typing or hold INSERT to speak... (Press ESC to quit)\n", end='', flush=True)
    threading.Thread(target=text_input, daemon=True).start()
    threading.Thread(target=insert_listener, daemon=True).start()
    threading.Thread(target=esc_listener, daemon=True).start()

    while True:
        await asyncio.sleep(0.1)
        if record_flag.is_set():
            record_flag.clear()
            if not record(chunk_file): await handle_audio(chunk_file)
            else: print("\nSilence detected. Skipping...")
            print("\n>>> ", end='', flush=True)

        while not input_q.empty():
            action, content = input_q.get()
            if action == 'exit': print("\n\nGoodbye!"); return
            if action == 'submit' and content:
                print(await sens(content))
                print("\n>>> ", end='', flush=True)

if __name__ == "__main__": asyncio.run(main())
