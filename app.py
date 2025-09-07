# Streamlit, MoviePy, Pillow 라이브러리 및 기타 유틸리티를 가져옵니다.
import streamlit as st
import moviepy.editor as mp
import os
import tempfile
import uuid
from PIL import Image

def create_video_from_images(image_paths, audio_path, transition_duration=1, fade_in_duration=1, fade_out_duration=1):
    """
    주어진 이미지와 오디오 파일을 사용하여 비디오를 생성하고, 디졸브 및 페이드 효과를 적용합니다.

    Args:
        image_paths (list): 비디오에 포함될 이미지 파일 경로 리스트.
        audio_path (str): 배경 음악 파일 경로.
        transition_duration (int): 이미지 전환(디졸브) 효과의 길이(초).
        fade_in_duration (int): 비디오 시작 페이드인 효과의 길이(초).
        fade_out_duration (int): 비디오 끝 페이드아웃 효과의 길이(초).
    
    Returns:
        str: 생성된 최종 비디오 파일의 경로.
    """
    st.info("비디오 생성을 시작합니다...")

    try:
        # 배경 음악 파일의 길이를 가져옵니다.
        audio_clip = mp.AudioFileClip(audio_path)
        total_audio_duration = audio_clip.duration
        st.write(f"배경 음악 길이: {total_audio_duration:.2f} 초")

        # 각 이미지 클립의 기본 지속 시간을 계산합니다.
        # 이미지 간 전환 시간(transition_duration)을 고려합니다.
        num_images = len(image_paths)
        total_transition_time = (num_images - 1) * transition_duration
        effective_video_duration = total_audio_duration - fade_in_duration - fade_out_duration
        if effective_video_duration <= 0:
            st.error("오디오 길이가 너무 짧습니다. 비디오 길이는 페이드인/아웃 시간을 포함하여 오디오 길이보다 길 수 없습니다.")
            return None
            
        # 디졸브 시간을 고려하여 각 이미지의 순수 노출 시간을 계산합니다.
        single_image_duration = (effective_video_duration - total_transition_time) / num_images
        
        if single_image_duration <= 0:
            st.error("오디오 길이에 비해 이미지가 너무 많아 비디오를 만들 수 없습니다. 이미지 수를 줄여주세요.")
            return None

        st.write(f"각 이미지의 순수 노출 시간: {single_image_duration:.2f} 초")

        # 이미지 클립 생성 및 디졸브 효과 적용
        clips = []
        for i, path in enumerate(image_paths):
            image_clip = mp.ImageClip(path, duration=single_image_duration).set_fps(24) # FPS 설정
            
            # 마지막 클립에는 디졸브 효과를 적용하지 않습니다.
            if i < num_images - 1:
                next_clip = mp.ImageClip(image_paths[i+1])
                # 디졸브 효과를 위해 첫 번째 클립과 다음 클립을 합성합니다.
                dissolve_clip = mp.CompositeVideoClip([
                    image_clip,
                    next_clip.set_start(single_image_duration).set_duration(transition_duration).crossfadein(transition_duration)
                ]).set_duration(single_image_duration + transition_duration)
                clips.append(dissolve_clip)
            else:
                clips.append(image_clip)
        
        # 모든 클립들을 이어붙입니다.
        final_video_clip = mp.concatenate_videoclips(clips, method="compose")

        # 비디오 시작 부분에 페이드인 효과 적용
        final_video_clip = final_video_clip.fadein(fade_in_duration, initial_color=[0, 0, 0])
        # 비디오 끝 부분에 페이드아웃 효과 적용
        final_video_clip = final_video_clip.fadeout(fade_out_duration, final_color=[0, 0, 0])

        # 배경 음악을 비디오에 추가합니다.
        final_video_clip = final_video_clip.set_audio(audio_clip)

        # 최종 비디오를 저장할 임시 파일 경로를 생성합니다.
        output_filename = f"output_{uuid.uuid4()}.mp4"
        output_path = os.path.join(tempfile.gettempdir(), output_filename)
        st.write("동영상 파일을 생성하고 있습니다. 잠시만 기다려주세요...")
        final_video_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

        st.success("비디오 생성이 완료되었습니다!")
        return output_path

    except Exception as e:
        st.error(f"비디오 생성 중 오류가 발생했습니다: {e}")
        return None

# --- Streamlit 웹 앱 UI ---
st.title("🎵 음악과 사진으로 만드는 뮤직비디오")
st.markdown("---")

st.header("1. 이미지 업로드")
st.warning("12~14장의 이미지를 업로드하는 것을 권장합니다.")
uploaded_images = st.file_uploader("이미지 파일 선택 (PNG, JPG)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

st.header("2. 배경 음악 업로드")
uploaded_audio = st.file_uploader("음악 파일 선택 (MP3, WAV)", type=["mp3", "wav"])

st.markdown("---")

# 동영상 생성 버튼
if st.button("🚀 동영상 만들기"):
    if uploaded_images and uploaded_audio:
        # 임시 디렉토리에 파일들을 저장합니다.
        with tempfile.TemporaryDirectory() as tmpdir:
            image_paths = []
            for uploaded_file in uploaded_images:
                path = os.path.join(tmpdir, uploaded_file.name)
                with open(path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                image_paths.append(path)
            
            audio_path = os.path.join(tmpdir, uploaded_audio.name)
            with open(audio_path, "wb") as f:
                f.write(uploaded_audio.getbuffer())

            # 이미지 순서를 정렬 (업로드된 순서대로)
            image_paths.sort()
            
            # 비디오 생성 함수 호출
            video_path = create_video_from_images(image_paths, audio_path)

            if video_path:
                st.header("🎉 완성된 뮤직비디오")
                # 비디오 플레이어 표시
                st.video(video_path)
                
                # 다운로드 버튼
                with open(video_path, "rb") as file:
                    st.download_button(
                        label="📥 비디오 다운로드",
                        data=file,
                        file_name="my_music_video.mp4",
                        mime="video/mp4"
                    )
    else:
        st.error("이미지 파일과 음악 파일을 모두 업로드해주세요.")
