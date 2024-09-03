from utility import *
from dotenv import load_dotenv

load_dotenv()

from GoogleTTS import (
    tts
)
def main():
    title, content = fetch_reddit_post()
    print("Title:", title)
    print("Content:", content)

    print("\n Rewriting the story!")
    formatted_now = get_current_datetime()
    story = makeStory(content)

    #Audio Generation
    speech_path = generate_speech(story, f"generated/speech_{formatted_now}.mp3")
    speed_up_path = speed_speech(speech_path, f"generated/sped_{formatted_now}.mp3")
    morePaths = makeMore(speed_up_path)
    
    
    

main()

