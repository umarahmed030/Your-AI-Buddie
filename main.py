
import os
import tempfile
import numpy as np
import sounddevice as sd
import soundfile as sf

from dotenv import load_dotenv
from sarvamai import SarvamAI
from sarvamai.play import play

load_dotenv()

api_key = os.getenv("SARVAM_API_KEY")

if not api_key:
    raise ValueError("API key nahi mili. .env file check karo.")

client = SarvamAI(api_subscription_key=api_key)


# Conversation instructions
messages = [
    {
        "role": "system",
        "content": """
You are Your AI Buddie, a friendly female English tutor.

Help the user improve conversational English.

1. Understand the user's intended meaning.
2. If English has mistakes, explain its intended meaning
   in simple Hindi, give the correct English sentence,
   explain the correction and translate it into Hindi.
3. If the sentence is already correct, do not invent errors.
4. If the meaning is unclear, ask a simple question in English.
5. If the user is still unclear after another attempt,
   ask them to explain in Hindi.
6. After understanding, give the correct English sentence
   and its Hindi meaning.
7. Continue the conversation with a simple English question.
8. Use natural Hindi and be patient and supportive.
9. Keep replies short and useful.
"""
    }
]


# Record voice until the user presses Enter
def record_voice():
    audio_frames = []

    def callback(indata, frames, time_info, status):
        audio_frames.append(indata.copy())

    print("\nRecording started! Speak now.")
    input("Press ENTER when you finish speaking...")

    # Audio is recorded in the stream below.
    # The recording stream must remain active while speaking.


def get_voice_input():
    audio_frames = []

    def callback(indata, frames, time_info, status):
        audio_frames.append(indata.copy())

    try:
        with sd.InputStream(
            samplerate=16000,
            channels=1,
            dtype="int16",
            callback=callback
        ):
            input("\nSpeak now, then press ENTER to stop recording...")

    except Exception as error:
        print("Microphone error:", error)
        return ""

    if not audio_frames:
        print("No audio recorded. Please try again.")
        return ""

    audio_data = np.concatenate(audio_frames, axis=0)

    audio_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False
        ) as temp_audio:
            audio_path = temp_audio.name

        sf.write(audio_path, audio_data, 16000, subtype="PCM_16")

        with open(audio_path, "rb") as audio_file:
            result = client.speech_to_text.transcribe(
                file=audio_file,
                model="saaras:v4",
                language_code="unknown",
                mode="transcribe"
            )

        transcript = result.transcript.strip()
        print("You said:", transcript)
        return transcript

    except Exception as error:
        print("Voice recognition error:", error)
        return ""

    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)


# Speak the AI reply using a female voice
def speak_reply(text):
    try:
        if not text.strip():
            return

        # Choose language based on the script in the reply
        if any("\u0900" <= char <= "\u097F" for char in text):
            language = "hi-IN"
        else:
            language = "en-IN"

        audio = client.text_to_speech.convert(
            text=text[:2500],
            model="bulbul:v3",
            speaker="priya",
            language_code=language
        )

        play(audio)

    except Exception as error:
        print("Voice output error:", error)


# Send the message to the AI
def chat_with_buddie(user_text):
    messages.append({
        "role": "user",
        "content": user_text
    })

    try:
        response = client.chat.completions(
            model="sarvam-105b-conversations",
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )

        reply = response.choices[0].message.content
        print(f"\nYour AI Buddie: {reply}\n")

        messages.append({
            "role": "assistant",
            "content": reply
        })

        speak_reply(reply)

    except Exception as error:
        messages.pop()
        print("AI error:", error)


# Main program
print("=" * 45)
print("          YOUR AI BUDDIE")
print("  Your Personal English Learning Partner")
print("=" * 45)

print("T = Type a message")
print("V = Speak using microphone")
print("EXIT = Close the assistant")

while True:
    choice = input("\nChoose T or V: ").strip().lower()

    if choice == "exit":
        print("Buddie: Great practice today! See you soon!")
        break

    if choice == "t":
        user_text = input("You: ").strip()

    elif choice == "v":
        user_text = get_voice_input()

    else:
        print("Please choose T, V or EXIT.")
        continue

    if not user_text:
        continue

    if user_text.lower() == "exit":
        print("Buddie: Great practice today! See you soon!")
        break

    chat_with_buddie(user_text)
