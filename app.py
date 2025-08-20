import streamlit as st
import os
import tempfile
import shutil
import requests
import time
from datetime import datetime
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import io
import atexit
import json
import base64

# Try to import moviepy
try:
    from moviepy.editor import *
    from moviepy.video.fx.all import *
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    st.error("⚠️ MoviePy not installed. Run: pip install moviepy")

# Page config
st.set_page_config(
    page_title="🎬 Complete AI Video Editor",
    page_icon="🎬",
    layout="wide"
)

# Create persistent temp directory
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp(prefix="video_editor_")

def safe_cleanup():
    """Safely clean up temp files"""
    try:
        if hasattr(st.session_state, 'temp_dir') and os.path.exists(st.session_state.temp_dir):
            for root, dirs, files in os.walk(st.session_state.temp_dir):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except:
                        pass
            try:
                shutil.rmtree(st.session_state.temp_dir)
            except:
                pass
    except:
        pass

atexit.register(safe_cleanup)

# Enhanced CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .editor-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .timeline-item {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.25rem;
        padding: 0.75rem;
        margin: 0.5rem 0;
        position: relative;
    }
    .scene-card {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
    .export-options {
        background-color: #f1f8e9;
        border: 1px solid #8bc34a;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .video-preview {
        border: 2px solid #ddd;
        border-radius: 0.5rem;
        padding: 1rem;
        background-color: #fafafa;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'project_scenes' not in st.session_state:
    st.session_state.project_scenes = []
if 'current_audio_file' not in st.session_state:
    st.session_state.current_audio_file = None
if 'project_images' not in st.session_state:
    st.session_state.project_images = []
if 'video_settings' not in st.session_state:
    st.session_state.video_settings = {
        'resolution': '1280x720',
        'fps': 24,
        'transition_duration': 0.5,
        'scene_duration': 'auto'
    }
if 'final_video_path' not in st.session_state:
    st.session_state.final_video_path = None

# Header
st.markdown('<h1 class="main-header">🎬 Complete AI Video Editor</h1>', unsafe_allow_html=True)

st.markdown("""
<div class="editor-section">
    <h3>🚀 All-in-One Video Creation Studio</h3>
    <p>Generate audio • Find images • Edit timeline • Add effects • Export professional videos</p>
</div>
""", unsafe_allow_html=True)

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎙️ Audio", "🖼️ Images", "✂️ Timeline Editor", "🎨 Effects & Text", "📤 Export"
])

# Sidebar - Global Settings
with st.sidebar:
    st.header("🎛️ Project Settings")
    
    # Video settings
    st.subheader("📹 Video Format")
    resolution = st.selectbox("Resolution", 
        ["1280x720 (HD)", "1920x1080 (Full HD)", "854x480 (SD)"],
        key="resolution_select"
    )
    
    fps = st.selectbox("Frame Rate", [24, 30, 60], index=0)
    
    st.session_state.video_settings['resolution'] = resolution.split(' ')[0]
    st.session_state.video_settings['fps'] = fps
    
    st.subheader("🎭 Global Effects")
    transition_type = st.selectbox("Default Transition", 
        ["crossfade", "slide_left", "slide_right", "fade_black", "none"])
    transition_duration = st.slider("Transition Duration (s)", 0.1, 2.0, 0.5)
    
    st.session_state.video_settings['transition_duration'] = transition_duration
    
    # Pexels API
    st.subheader("🔑 API Keys")
    pexels_key = st.text_input("Pexels API Key", type="password")
    
    # Project actions
    st.subheader("💾 Project")
    if st.button("🗑️ Clear Project"):
        st.session_state.project_scenes = []
        st.session_state.project_images = []
        st.session_state.current_audio_file = None
        st.session_state.final_video_path = None
        st.success("Project cleared!")
        st.rerun()

# TAB 1: AUDIO GENERATION
with tab1:
    st.header("🎙️ Audio Creation")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Audio source selection
        audio_mode = st.radio(
            "Choose audio method:",
            ["🤖 AI Text-to-Speech", "🎙️ Upload Recording", "🎵 Background Music Only"],
            horizontal=True
        )
        
        if audio_mode == "🤖 AI Text-to-Speech":
            # TTS Interface
            st.subheader("📝 Script Input")
            
            # Quick templates
            template = st.selectbox("Template:", [
                "Custom", "Product Review", "Tutorial", "Vlog", "News", "Educational"
            ])
            
            templates = {
                "Product Review": "Today I'm reviewing [product]. Let me show you the key features and my honest opinion after using it for [time period].",
                "Tutorial": "In this tutorial, I'll teach you how to [skill] step by step. By the end, you'll be able to [outcome].",
                "Vlog": "Hey everyone! Today I want to share [experience/story] with you. It's been quite a journey and I learned [lesson].",
                "News": "Breaking news about [topic]. Here are the key facts you need to know and why this matters.",
                "Educational": "Let's explore [topic] together. We'll cover the basics, see real examples, and understand why it's important."
            }
            
            script = st.text_area(
                "Your script:",
                value=templates.get(template, ""),
                height=200,
                placeholder="Enter your video script here..."
            )
            
            # TTS settings
            col_lang, col_speed = st.columns(2)
            with col_lang:
                language = st.selectbox("Language", ["en", "es", "fr", "de", "it"])
            with col_speed:
                speed = st.selectbox("Speed", ["slow", "normal", "fast"])
            
            if st.button("🎙️ Generate AI Voice", type="primary"):
                if script:
                    with st.spinner("Creating AI voice..."):
                        try:
                            tts = gTTS(text=script, lang=language, slow=(speed=="slow"))
                            audio_path = os.path.join(st.session_state.temp_dir, "tts_audio.mp3")
                            tts.save(audio_path)
                            st.session_state.current_audio_file = audio_path
                            st.success("✅ AI voice generated!")
                        except Exception as e:
                            st.error(f"Error: {e}")
        
        elif audio_mode == "🎙️ Upload Recording":
            # File upload
            uploaded_audio = st.file_uploader(
                "Upload your audio file",
                type=['mp3', 'wav', 'm4a', 'ogg'],
                help="Drag and drop or click to browse"
            )
            
            if uploaded_audio:
                # Save uploaded file
                audio_path = os.path.join(st.session_state.temp_dir, f"uploaded_{uploaded_audio.name}")
                with open(audio_path, 'wb') as f:
                    f.write(uploaded_audio.getbuffer())
                st.session_state.current_audio_file = audio_path
                st.success("✅ Audio uploaded!")
        
        else:  # Background music only
            st.info("📢 Creating silent video with background music (add in Effects tab)")
            st.session_state.current_audio_file = None
    
    with col2:
        st.subheader("🎵 Audio Preview")
        
        if st.session_state.current_audio_file and os.path.exists(st.session_state.current_audio_file):
            # Audio player
            with open(st.session_state.current_audio_file, 'rb') as f:
                audio_data = f.read()
            
            st.audio(audio_data)
            
            # Audio info
            if MOVIEPY_AVAILABLE:
                try:
                    audio_clip = AudioFileClip(st.session_state.current_audio_file)
                    duration = audio_clip.duration
                    st.metric("⏱️ Duration", f"{duration:.1f}s")
                    audio_clip.close()
                except:
                    st.info("Audio loaded successfully")
            
            # Download option
            st.download_button(
                "📥 Download Audio",
                audio_data,
                f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3",
                "audio/mp3"
            )
        else:
            st.info("No audio loaded yet")

# TAB 2: IMAGE MANAGEMENT
with tab2:
    st.header("🖼️ Image Collection")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🔍 Find Images")
        
        # Search method
        search_method = st.radio("Image source:", ["🌐 Pexels API", "📁 Upload Images"])
        
        if search_method == "🌐 Pexels API":
            if pexels_key:
                search_query = st.text_input("Search for:", placeholder="business, technology, nature...")
                num_images = st.slider("Number of images", 1, 10, 5)
                
                if st.button("🔍 Search Images") and search_query:
                    with st.spinner("Searching Pexels..."):
                        try:
                            headers = {"Authorization": pexels_key}
                            url = "https://api.pexels.com/v1/search"
                            params = {
                                "query": search_query,
                                "per_page": num_images,
                                "orientation": "landscape"
                            }
                            
                            response = requests.get(url, headers=headers, params=params)
                            if response.status_code == 200:
                                photos = response.json().get('photos', [])
                                
                                # Download and save images
                                for i, photo in enumerate(photos):
                                    img_response = requests.get(photo['src']['large'])
                                    if img_response.status_code == 200:
                                        img_path = os.path.join(st.session_state.temp_dir, f"pexels_{i}.jpg")
                                        with open(img_path, 'wb') as f:
                                            f.write(img_response.content)
                                        
                                        st.session_state.project_images.append({
                                            'path': img_path,
                                            'source': 'pexels',
                                            'photographer': photo['photographer'],
                                            'duration': 3.0  # default duration
                                        })
                                
                                st.success(f"✅ Added {len(photos)} images to project!")
                            else:
                                st.error("Failed to search images. Check your API key.")
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.warning("⚠️ Add Pexels API key in sidebar")
        
        else:  # Upload images
            uploaded_images = st.file_uploader(
                "Upload image files",
                type=['jpg', 'jpeg', 'png', 'gif'],
                accept_multiple_files=True
            )
            
            if uploaded_images:
                for uploaded_img in uploaded_images:
                    img_path = os.path.join(st.session_state.temp_dir, uploaded_img.name)
                    with open(img_path, 'wb') as f:
                        f.write(uploaded_img.getbuffer())
                    
                    st.session_state.project_images.append({
                        'path': img_path,
                        'source': 'upload',
                        'filename': uploaded_img.name,
                        'duration': 3.0
                    })
                
                st.success(f"✅ Uploaded {len(uploaded_images)} images!")
    
    with col2:
        st.subheader("📚 Image Library")
        
        if st.session_state.project_images:
            for i, img_data in enumerate(st.session_state.project_images):
                if os.path.exists(img_data['path']):
                    col_img, col_ctrl = st.columns([2, 1])
                    
                    with col_img:
                        img = Image.open(img_data['path'])
                        st.image(img, width=200)
                    
                    with col_ctrl:
                        # Duration control
                        new_duration = st.number_input(
                            f"Duration (s)",
                            min_value=0.5,
                            max_value=10.0,
                            value=img_data['duration'],
                            step=0.5,
                            key=f"duration_{i}"
                        )
                        st.session_state.project_images[i]['duration'] = new_duration
                        
                        # Remove button
                        if st.button(f"🗑️ Remove", key=f"remove_{i}"):
                            st.session_state.project_images.pop(i)
                            st.rerun()
                    
                    st.markdown("---")
        else:
            st.info("No images in project yet")

# TAB 3: TIMELINE EDITOR
with tab3:
    st.header("✂️ Video Timeline Editor")
    
    if not MOVIEPY_AVAILABLE:
        st.error("⚠️ MoviePy required for timeline editing. Install with: pip install moviepy")
        st.stop()
    
    # Timeline controls
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("🎬 Scene Timeline")
        
        # Auto-generate scenes from images and audio
        if st.button("🔄 Auto-Generate Timeline"):
            if st.session_state.project_images:
                st.session_state.project_scenes = []
                
                # Calculate timing
                if st.session_state.current_audio_file:
                    try:
                        audio_clip = AudioFileClip(st.session_state.current_audio_file)
                        total_audio_duration = audio_clip.duration
                        audio_clip.close()
                        
                        # Distribute images across audio duration
                        num_images = len(st.session_state.project_images)
                        duration_per_image = total_audio_duration / num_images
                        
                        for i, img_data in enumerate(st.session_state.project_images):
                            st.session_state.project_scenes.append({
                                'type': 'image',
                                'content': img_data['path'],
                                'start_time': i * duration_per_image,
                                'duration': duration_per_image,
                                'text_overlay': '',
                                'transition': 'crossfade'
                            })
                    except:
                        # Fallback: use image durations
                        current_time = 0
                        for img_data in st.session_state.project_images:
                            st.session_state.project_scenes.append({
                                'type': 'image',
                                'content': img_data['path'],
                                'start_time': current_time,
                                'duration': img_data['duration'],
                                'text_overlay': '',
                                'transition': 'crossfade'
                            })
                            current_time += img_data['duration']
                else:
                    # No audio - use image durations
                    current_time = 0
                    for img_data in st.session_state.project_images:
                        st.session_state.project_scenes.append({
                            'type': 'image',
                            'content': img_data['path'],
                            'start_time': current_time,
                            'duration': img_data['duration'],
                            'text_overlay': '',
                            'transition': 'crossfade'
                        })
                        current_time += img_data['duration']
                
                st.success("✅ Timeline generated!")
                st.rerun()
        
        # Display and edit timeline
        if st.session_state.project_scenes:
            st.subheader("📋 Scene List")
            
            for i, scene in enumerate(st.session_state.project_scenes):
                with st.expander(f"Scene {i+1} ({scene['start_time']:.1f}s - {scene['start_time']+scene['duration']:.1f}s)"):
                    col_preview, col_settings = st.columns([1, 2])
                    
                    with col_preview:
                        if scene['type'] == 'image' and os.path.exists(scene['content']):
                            img = Image.open(scene['content'])
                            st.image(img, width=150)
                    
                    with col_settings:
                        # Scene settings
                        new_duration = st.number_input(
                            "Duration (s)",
                            min_value=0.1,
                            value=scene['duration'],
                            step=0.1,
                            key=f"scene_duration_{i}"
                        )
                        
                        text_overlay = st.text_input(
                            "Text Overlay",
                            value=scene.get('text_overlay', ''),
                            key=f"text_overlay_{i}"
                        )
                        
                        transition = st.selectbox(
                            "Transition",
                            ["crossfade", "slide_left", "slide_right", "fade_black", "none"],
                            index=0,
                            key=f"transition_{i}"
                        )
                        
                        # Update scene
                        st.session_state.project_scenes[i]['duration'] = new_duration
                        st.session_state.project_scenes[i]['text_overlay'] = text_overlay
                        st.session_state.project_scenes[i]['transition'] = transition
                        
                        # Move/delete controls
                        col_up, col_down, col_del = st.columns(3)
                        with col_up:
                            if st.button("⬆️", key=f"up_{i}") and i > 0:
                                st.session_state.project_scenes[i], st.session_state.project_scenes[i-1] = \
                                    st.session_state.project_scenes[i-1], st.session_state.project_scenes[i]
                                st.rerun()
                        with col_down:
                            if st.button("⬇️", key=f"down_{i}") and i < len(st.session_state.project_scenes)-1:
                                st.session_state.project_scenes[i], st.session_state.project_scenes[i+1] = \
                                    st.session_state.project_scenes[i+1], st.session_state.project_scenes[i]
                                st.rerun()
                        with col_del:
                            if st.button("🗑️", key=f"delete_{i}"):
                                st.session_state.project_scenes.pop(i)
                                st.rerun()
        else:
            st.info("👆 Add images first, then click 'Auto-Generate Timeline'")
    
    with col2:
        st.subheader("📊 Timeline Info")
        
        if st.session_state.project_scenes:
            total_video_duration = sum(scene['duration'] for scene in st.session_state.project_scenes)
            
            st.metric("🎬 Total Scenes", len(st.session_state.project_scenes))
            st.metric("⏱️ Video Duration", f"{total_video_duration:.1f}s")
            
            if st.session_state.current_audio_file:
                try:
                    audio_clip = AudioFileClip(st.session_state.current_audio_file)
                    audio_duration = audio_clip.duration
                    audio_clip.close()
                    
                    st.metric("🎵 Audio Duration", f"{audio_duration:.1f}s")
                    
                    # Sync warning
                    if abs(total_video_duration - audio_duration) > 1.0:
                        st.warning(f"⚠️ Video/Audio sync issue: {total_video_duration - audio_duration:.1f}s difference")
                except:
                    pass

# TAB 4: EFFECTS & TEXT
with tab4:
    st.header("🎨 Effects & Text Overlays")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✨ Visual Effects")
        
        # Global effects
        add_intro = st.checkbox("📽️ Add Intro Title")
        if add_intro:
            intro_text = st.text_input("Intro Text", "Welcome to My Video")
            intro_duration = st.slider("Intro Duration (s)", 1.0, 5.0, 2.0)
        
        add_outro = st.checkbox("🎭 Add Outro")
        if add_outro:
            outro_text = st.text_input("Outro Text", "Thanks for Watching!")
            outro_duration = st.slider("Outro Duration (s)", 1.0, 5.0, 2.0)
        
        # Image effects
        st.subheader("🖼️ Image Effects")
        zoom_effect = st.checkbox("🔍 Ken Burns Effect (Zoom)")
        fade_edges = st.checkbox("🌫️ Fade Edges")
        
        # Color adjustments
        brightness = st.slider("☀️ Brightness", 0.5, 2.0, 1.0)
        contrast = st.slider("🌓 Contrast", 0.5, 2.0, 1.0)
        saturation = st.slider("🎨 Saturation", 0.0, 2.0, 1.0)
    
    with col2:
        st.subheader("📝 Text Settings")
        
        # Default text styling
        font_size = st.slider("Font Size", 20, 100, 40)
        font_color = st.color_picker("Font Color", "#FFFFFF")
        
        # Text position
        text_position = st.selectbox("Text Position", 
            ["bottom", "top", "center", "bottom-left", "bottom-right"])
        
        # Text background
        text_bg = st.checkbox("Text Background")
        if text_bg:
            bg_color = st.color_picker("Background Color", "#000000")
            bg_opacity = st.slider("Background Opacity", 0.0, 1.0, 0.7)
        
        # Animation
        text_animation = st.selectbox("Text Animation", 
            ["none", "fade_in", "slide_up", "typewriter"])
        
        # Preview text styling
        st.subheader("👀 Preview")
        preview_text = st.text_input("Preview Text", "Sample Text")
        if preview_text:
            # Create preview image
            img = Image.new('RGB', (400, 200), color='gray')
            draw = ImageDraw.Draw(img)
            
            # Try to use a basic font
            try:
                # Note: In production, you'd want to include font files
                font = ImageFont.load_default()
            except:
                font = None
            
            # Draw text (simplified preview)
            text_y = 150 if text_position == "bottom" else 50
            draw.text((50, text_y), preview_text, fill=font_color, font=font)
            
            st.image(img, caption="Text Preview")

# TAB 5: EXPORT
with tab5:
    st.header("📤 Export Your Video")
    
    if not st.session_state.project_scenes:
        st.warning("⚠️ No scenes to export. Create your timeline first!")
        st.stop()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("⚙️ Export Settings")
        
        # Quality settings
        quality = st.selectbox("Quality Preset", 
            ["🔥 High (Best)", "⚡ Medium (Balanced)", "💨 Low (Fast)"])
        
        # Format settings
        video_format = st.selectbox("Format", ["MP4 (Recommended)", "AVI", "MOV"])
        
        # Advanced settings
        with st.expander("🔧 Advanced Settings"):
            custom_bitrate = st.checkbox("Custom Bitrate")
            if custom_bitrate:
                bitrate = st.text_input("Bitrate", "2000k")
            
            custom_fps = st.checkbox("Custom Frame Rate")
            if custom_fps:
                export_fps = st.number_input("FPS", 1, 60, fps)
        
        # Big export button
        if st.button("🚀 GENERATE VIDEO", type="primary", use_container_width=True):
            if MOVIEPY_AVAILABLE:
                with st.spinner("🎬 Creating your video... This may take a few minutes"):
                    try:
                        # Progress tracking
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Create video clips from scenes
                        status_text.text("📸 Processing images...")
                        video_clips = []
                        
                        for i, scene in enumerate(st.session_state.project_scenes):
                            if scene['type'] == 'image' and os.path.exists(scene['content']):
                                # Create image clip
                                img_clip = ImageClip(scene['content'], duration=scene['duration'])
                                
                                # Resize to target resolution
                                target_size = [int(x) for x in st.session_state.video_settings['resolution'].split('x')]
                                img_clip = img_clip.resize(target_size)
                                
                                # Add text overlay if specified
                                if scene.get('text_overlay'):
                                    text_clip = TextClip(
                                        scene['text_overlay'],
                                        fontsize=font_size,
                                        color=font_color,
                                        font='Arial-Bold'
                                    ).set_duration(scene['duration'])
                                    
                                    # Position text
                                    if text_position == "bottom":
                                        text_clip = text_clip.set_position(('center', 'bottom'))
                                    elif text_position == "top":
                                        text_clip = text_clip.set_position(('center', 'top'))
                                    else:
                                        text_clip = text_clip.set_position('center')
                                    
                                    # Composite text over image
                                    img_clip = CompositeVideoClip([img_clip, text_clip])
                                
                                video_clips.append(img_clip)
                            
                            progress_bar.progress((i + 1) / len(st.session_state.project_scenes) * 0.5)
                        
                        if not video_clips:
                            st.error("No valid video clips created!")
                            st.stop()
                        
                        # Concatenate video clips
                        status_text.text("🎬 Assembling video...")
                        if len(video_clips) > 1:
                            # Add transitions between clips
                            final_clips = []
                            for i, clip in enumerate(video_clips):
                                if i > 0 and transition_duration > 0:
                                    clip = clip.crossfadein(transition_duration)
                                if i < len(video_clips) - 1 and transition_duration > 0:
                                    clip = clip.crossfadeout(transition_duration)
                                final_clips.append(clip)
                            
                            final_video = concatenate_videoclips(final_clips, method="compose")
                        else:
                            final_video = video_clips[0]
                        
                        progress_bar.progress(0.7)
                        
                        # Add audio if available
                        if st.session_state.current_audio_file and os.path.exists(st.session_state.current_audio_file):
                            status_text.text("🎵 Adding audio...")
                            audio_clip = AudioFileClip(st.session_state.current_audio_file)
                            
                            # Match audio duration to video or vice versa
                            if audio_clip.duration > final_video.duration:
                                audio_clip = audio_clip.subclip(0, final_video.duration)
                            elif audio_clip.duration < final_video.duration:
                                final_video = final_video.subclip(0, audio_clip.duration)
                            
                            final_video = final_video.set_audio(audio_clip)
                        
                        progress_bar.progress(0.8)
                        
                        # Export video
                        status_text.text("💾 Exporting final video...")
                        output_path = os.path.join(st.session_state.temp_dir, 
                                                 f"final_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
                        
                        # Set codec based on quality
                        if quality == "🔥 High (Best)":
                            codec_params = {'codec': 'libx264', 'bitrate': '3000k'}
                        elif quality == "⚡ Medium (Balanced)":
                            codec_params = {'codec': 'libx264', 'bitrate': '1500k'}
                        else:
                            codec_params = {'codec': 'libx264', 'bitrate': '800k'}
                        
                        final_video.write_videofile(
                            output_path,
                            fps=st.session_state.video_settings['fps'],
                            **codec_params,
                            audio_codec='aac',
                            temp_audiofile=os.path.join(st.session_state.temp_dir, 'temp_audio.m4a'),
                            remove_temp=True,
                            verbose=False,
                            logger=None
                        )
                        
                        progress_bar.progress(1.0)
                        status_text.text("✅ Video export complete!")
                        
                        # Store final video path
                        st.session_state.final_video_path = output_path
                        
                        # Cleanup clips
                        for clip in video_clips:
                            clip.close()
                        final_video.close()
                        if 'audio_clip' in locals():
                            audio_clip.close()
                        
                        st.success("🎉 Video created successfully!")
                        
                    except Exception as e:
                        st.error(f"❌ Export failed: {str(e)}")
                        st.error("Try reducing video length or image resolution")
            else:
                st.error("MoviePy required for video export")
    
    with col2:
        st.subheader("📊 Export Preview")
        
        # Project summary
        if st.session_state.project_scenes:
            total_duration = sum(scene['duration'] for scene in st.session_state.project_scenes)
            
            st.metric("🎬 Scenes", len(st.session_state.project_scenes))
            st.metric("⏱️ Duration", f"{total_duration:.1f}s")
            st.metric("📹 Resolution", st.session_state.video_settings['resolution'])
            st.metric("🎞️ Frame Rate", f"{st.session_state.video_settings['fps']} fps")
            
            # Estimated file size
            estimated_size = (total_duration * 2) / 60  # Rough estimate in MB
            st.metric("📁 Est. Size", f"{estimated_size:.1f} MB")
        
        # Final video download
        if st.session_state.final_video_path and os.path.exists(st.session_state.final_video_path):
            st.subheader("🎉 Your Video")
            
            # Video preview
            st.video(st.session_state.final_video_path)
            
            # File info
            file_size = os.path.getsize(st.session_state.final_video_path) / (1024 * 1024)
            st.info(f"📁 Size: {file_size:.1f} MB")
            
            # Download button
            with open(st.session_state.final_video_path, 'rb') as f:
                video_data = f.read()
            
            st.download_button(
                label="📥 Download Video",
                data=video_data,
                file_name=f"ai_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                mime="video/mp4",
                use_container_width=True
            )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <strong>🎬 Complete AI Video Editor</strong><br>
    Professional video creation made simple • All-in-one solution • Export ready videos
</div>
""", unsafe_allow_html=True)
