from utility import * 

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
    
    for i,vid in enumerate(morePaths):
        print(f"LOOK AT ME {morePaths} at index {i}")
        print(f"we need to do this loop: {len(morePaths)}")
        print(f"doing video: {vid}")
        video_path = edit_video(vid, "mcLow.mp4", f"generated/[{i}]intermediate_{formatted_now}.mp4")
        srt_path = transcribe_video(video_path, f"generated/[{i}]{formatted_now}.srt")
        final_short_path = add_subtitles_to_video(video_path, srt_path, f"generated/[{i}]final_{formatted_now}.mp4")
        response = upload_to_youtube(final_short_path, title + f"part {i} #shorts", f"{content} #aitah #aita #shorts")
    print(response)

if __name__ == "__main__":
    main()
