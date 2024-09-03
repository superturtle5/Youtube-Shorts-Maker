import os
import random
from datetime import datetime
from moviepy.editor import *
import moviepy.video.fx.all as vfx
import moviepy.video.fx.crop as crop_vid
from gtts import gTTS
import assemblyai as aai
import pysrt
import praw
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import google.auth.transport.requests
import json
import soundfile as sf
from pydub import AudioSegment
from audiostretchy.stretch import stretch_audio
from dotenv import load_dotenv
from openai import OpenAI
from GoogleTTS import (
    tts
)


# Load environment variables
load_dotenv()
num = 1

def get_current_datetime():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def fetch_reddit_post():
    reddit = praw.Reddit(
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET'),
        user_agent=os.getenv('USER_AGENT'),
    )
    subreddit = reddit.subreddit('AmItheAsshole')
    post = next(subreddit.new(limit=1)
)
    return post.title[0:50], post.selftext[0:4900]

def makeStory(post):
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {   "role": "user",
                "content": f"rewrite the following story to be more engaging and entertaining for short form content. Tell the story in first person, do not use acronyms, and use less than 4900 charaters. Make this story viral. {post}"}
        ]
    )
    story = completion.choices[0].message.content
    print(story)
    return story

def generate_speech(content, output_path):
    speech = tts(content,output_path)
    return output_path
def speed_speech(input_file, output_file):
    speedFactor = 1.3
    print(f"speeding up {input_file}")
    toWav = AudioSegment.from_file(input_file)
    toWav.export("generated/temp.wav",format="wav")

    stretch_audio("generated/temp.wav","generated/file.wav", ratio=1/speedFactor)
    newDuration = (toWav.duration_seconds/speedFactor)

    outputAudio = AudioSegment.from_file("generated/file.wav")[0:(newDuration*1000)].export(output_file, format="mp3")
    return output_file

def makeMore(input_path):
    audio_clip = AudioSegment.from_file(input_path) 
    duration = audio_clip.duration_seconds
    durEachClip = 58
    num_clips_to_split = int(duration//durEachClip)+1
    print(f"init numclips to split = {num_clips_to_split}")
    last_slash_index = input_path.rfind('/')
    input_folder = input_path[:last_slash_index]
    input_file = input_path[last_slash_index + 1:]

    print(f"Folder: {input_folder}")
    print(f"File: {input_file}")
    #input_folder = input_path.split("/")[0]
    #input_file = input_path.split("/")[1]
    output_path_list = []

    if(duration%num_clips_to_split < 8 & num_clips_to_split > 1):
        num_clips_to_split+=1
    durEachClip = duration/num_clips_to_split
    print(f"you need {num_clips_to_split} and each clip should be {durEachClip} long out of a {duration} long clip")

    for i in range(num_clips_to_split):
        start = durEachClip*i*1000
        end = start+durEachClip*1000
        output_path = f"{input_folder}/[{i}]{input_file}"
        print(f"start: {start} end: {end} saved at {output_path}")
        trimmed_audio_clip = audio_clip[start:end]
        trimmed_audio_clip.export(output_path, format="mp3")
        output_path_list.append(output_path)
    return output_path_list



def makeMoreBAD(input_file):
    audio_clip = AudioFileClip(input_file).fx(vfx.speedx, 1)
    output_file = [input_file]
    num=0
    if(audio_clip.duration > (58)):
        num = int(round(audio_clip.duration/58,1))
        print(f"Lets make {num} shorts with this!")
        toSplit = AudioSegment.from_mp3(input_file) 
    for i in range(num):
        output_file[i] = f"[{i}]{input_file}"
        toSplit.export(output_file[i])
    return output_file

def edit_video(audio_path, video_path, output_path):
    audio_clip = AudioFileClip(audio_path).fx(vfx.speedx, 1)
    start_point = random.randint(1, 480)
    video_clip = VideoFileClip("snakes.mp4").subclip(start_point, start_point + audio_clip.duration)
    final_clip = video_clip.set_audio(audio_clip)

    w, h = final_clip.size
    target_ratio = 1080 / 1920
    current_ratio = w / h

    if current_ratio > target_ratio:
        new_width = int(h * target_ratio)
        x_center = w / 2
        final_clip = crop_vid.crop(final_clip, width=new_width, height=h, x_center=x_center)
    else:
        new_height = int(w / target_ratio)
        y_center = h / 2
        final_clip = crop_vid.crop(final_clip, width=w, height=new_height, y_center=y_center)

    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', temp_audiofile='temp-audio.m4a', remove_temp=True)
    return output_path

def transcribe_video(video_path, srt_output_path):
    aai.settings.api_key = os.getenv('ASSEMBLYAI_API_KEY')
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(video_path)
    srt = transcript.export_subtitles_srt(chars_per_caption=17)

    with open(srt_output_path, "w") as f:
        f.write(srt)
    return srt_output_path

def add_subtitles_to_video(video_path, srt_path, output_path):
    video = VideoFileClip(video_path)
    subtitles = pysrt.open(srt_path)

    subtitle_clips = []
    for subtitle in subtitles:
        start_time = subtitle.start.hours * 3600 + subtitle.start.minutes * 60 + subtitle.start.seconds + subtitle.start.milliseconds / 1000
        end_time = subtitle.end.hours * 3600 + subtitle.end.minutes * 60 + subtitle.end.seconds + subtitle.end.milliseconds / 1000
        text_clip = TextClip(subtitle.text, fontsize=43, font='System-Font-Bold', color='White', bg_color='none', size=(video.size[0]*5/6, None), method='caption', stroke_width=1, stroke_color='white')
        text_clip = text_clip.set_start(start_time).set_duration(end_time - start_time)
        text_clip = text_clip.set_position(('center', 'center'))
        subtitle_clips.append(text_clip)

    final_video = CompositeVideoClip([video] + subtitle_clips)
    final_video.write_videofile(output_path, codec='libx264', remove_temp=True)
    return output_path

def shorten_video_if_needed(video_path, max_duration=58):
    video_clip = VideoFileClip(video_path)
    if video_clip.duration > max_duration:
        final_short_clip = video_clip.subclip(0, max_duration)
        final_short_path = video_path.replace(".mp4", "_short.mp4")
        final_short_clip.write_videofile(final_short_path, codec='libx264', remove_temp=True)
        final_short_clip.close()
        return final_short_path
    video_clip.close()
    return video_path

def get_authenticated_service():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "secret.json"
    credentials_file = 'credentials.json'

    credentials = None
    if os.path.exists(credentials_file):
        with open(credentials_file, 'r') as file:
            credentials = google.oauth2.credentials.Credentials.from_authorized_user_info(json.load(file), scopes=["https://www.googleapis.com/auth/youtube.upload"])

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(google.auth.transport.requests.Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes=["https://www.googleapis.com/auth/youtube.upload"])
            credentials = flow.run_local_server(port=0)

        with open(credentials_file, 'w') as file:
            file.write(credentials.to_json())

    return googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)

def upload_to_youtube(video_path, title, description):
    youtube = get_authenticated_service()
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "categoryId": "22",
                "description": description,
                "title": title,
                "defaultLanguage": "en",
            },
            "status": {
                "privacyStatus": "private",
                "madeForKids": False
            }
        },
        media_body=googleapiclient.http.MediaFileUpload(video_path)
    )
    response = request.execute()
    return response
