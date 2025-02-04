import os
import time
import asyncio

import azure.cognitiveservices.speech as speechsdk
import keyboard
import pyautogui
from groq import Groq

# Configuration constants
GROQ_API_KEY = os.environ.get("GROQ_KEY")
SPEECH_KEY = os.environ.get("SPEECH_KEY")
SPEECH_REGION = os.environ.get("SPEECH_REGION")
AI_MODEL = "llama-3.3-70b-versatile"

# Initialize the Groq client
client = Groq(api_key=GROQ_API_KEY)


class SpeechHandler:
    """Handles speech recognition and subsequent AI processing."""

    def __init__(self):
        speech_config = speechsdk.SpeechConfig(
            subscription=SPEECH_KEY,
            region=SPEECH_REGION
        )
        speech_config.speech_recognition_language = "en-US"

        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        self.recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )

        self.text_length = 0
        self.is_running = False

        # Connect the recognized event to the callback
        self.recognizer.recognized.connect(self.on_recognized)

        # Store a reference to the main event loop
        self.loop = asyncio.get_event_loop()

    def on_recognized(self, evt: speechsdk.SpeechRecognitionEventArgs):
        """Handles recognized speech events."""
        text = evt.result.text
        pyautogui.write(text, interval=0.01)
        print(f"Recognized: {text}")

        self.text_length = len(text)
        # Schedule asynchronous AI processing safely on the main event loop
        asyncio.run_coroutine_threadsafe(self.process_ai(text), self.loop)

    async def process_ai(self, message: str):
        """Processes the recognized message using AI."""
        await ai_process(message)

    def start_recognition(self):
        """Starts the continuous speech recognition."""
        if not self.is_running:
            self.recognizer.start_continuous_recognition()
            self.is_running = True
            print("Started recognizing")

    def stop_recognition(self):
        """Stops speech recognition and cleans up the typed text."""
        if self.is_running:
            self.recognizer.stop_continuous_recognition()
            self.is_running = False
            print("Stopped recognizing")
            print(f"Text length was: {self.text_length}")
            time.sleep(1)  # Brief pause before removing text
            pyautogui.write("\b" * self.text_length, interval=0.01)


async def ai_process(message: str):
    """Calls the AI service with the provided message and writes the result."""
    print("AI received a message for processing")
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI note taking assistant that accurately transcribes speech, "
                    "intelligently formats text, and processes real-time commands. You recognize "
                    "and apply punctuation, fix capitalization, and prevent unnecessary all-caps. "
                    "Users can issue commands like 'New line', 'Scratch that', or 'Remove that line' "
                    "to modify text instantly. Post-processing ensures natural sentence flow by correcting "
                    "errors and removing filler words. Transcriptions must be near-instant. Your goal is "
                    "to create a seamless, efficient, and user-friendly voice dictation experience."
                )
            },
            {
                "role": "user",
                "content": message,
            }
        ],
        model=AI_MODEL,
        temperature=0.1,
        stop=None,
        stream=False,
    )

    ai_response = response.choices[0].message.content
    print("AI processed the message")
    print(f"AI response: {ai_response}")
    pyautogui.write(ai_response, interval=0.01)


async def main():
    """Main entry point for the application."""
    speech_handler = SpeechHandler()

    def on_ctrl_press(_):
        speech_handler.start_recognition()

    def on_ctrl_release(_):
        speech_handler.stop_recognition()

    keyboard.on_press_key("ctrl", on_ctrl_press)
    keyboard.on_release_key("ctrl", on_ctrl_release)

    try:
        while True:
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        speech_handler.stop_recognition()


if __name__ == "__main__":
    asyncio.run(main())
