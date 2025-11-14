import streamlit as st
import openai
from audio_recorder_streamlit import audio_recorder
import base64
import os
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Fort Siloso Voice Assistant",
    page_icon="🏰",
    layout="centered"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        padding: 0.75rem;
        font-size: 1.1rem;
        border-radius: 10px;
        border: none;
        cursor: pointer;
    }
    .stButton button:hover {
        background-color: #45a049;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 5px solid #2196F3;
    }
    .assistant-message {
        background-color: #f1f8e9;
        border-left: 5px solid #4CAF50;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''

# Fort Siloso context for the AI
FORT_SILOSO_CONTEXT = """You are a knowledgeable guide about Fort Siloso, a historical coastal artillery battery located on Sentosa Island in Singapore. 

Key information about Fort Siloso:
- Built in the 1880s as part of Singapore's coastal defenses
- Located on the westernmost point of Sentosa Island
- Originally armed with guns to protect the western entrance to Keppel Harbour
- Played a role during World War II
- Now serves as a military museum and heritage site
- Features underground tunnels, gun emplacements, and historical exhibits
- Showcases Singapore's military history from the 1800s through WWII
- Includes displays about the British surrender to Japanese forces in 1942
- Visitors can explore barracks, ammunition stores, and coastal gun positions
- Part of the larger Sentosa Island tourist destination

Provide helpful, accurate, and engaging information about Fort Siloso. Keep responses concise and conversational (2-3 sentences for simple questions, longer for complex ones). If asked about topics unrelated to Fort Siloso or Singapore history, politely redirect the conversation back to Fort Siloso."""

def initialize_openai(api_key):
    """Initialize OpenAI client with API key"""
    openai.api_key = api_key

def transcribe_audio(audio_bytes):
    """Transcribe audio using OpenAI Whisper API"""
    try:
        # Save audio bytes to temporary file
        temp_audio_path = "/tmp/temp_audio.wav"
        with open(temp_audio_path, "wb") as f:
            f.write(audio_bytes)
        
        # Transcribe using Whisper
        with open(temp_audio_path, "rb") as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        return transcript.text
    except Exception as e:
        st.error(f"Transcription error: {str(e)}")
        return None

def get_ai_response(user_message):
    """Get response from OpenAI GPT"""
    try:
        messages = [
            {"role": "system", "content": FORT_SILOSO_CONTEXT},
        ]
        
        # Add conversation history (last 5 exchanges to keep context manageable)
        for msg in st.session_state.messages[-10:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"AI response error: {str(e)}")
        return None

def text_to_speech(text):
    """Convert text to speech using OpenAI TTS"""
    try:
        response = openai.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        
        # Save audio to temporary file
        temp_audio_path = "/tmp/response_audio.mp3"
        response.stream_to_file(temp_audio_path)
        
        # Read and return audio bytes
        with open(temp_audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        
        return audio_bytes
    except Exception as e:
        st.error(f"Text-to-speech error: {str(e)}")
        return None

def autoplay_audio(audio_bytes):
    """Auto-play audio in the browser"""
    b64 = base64.b64encode(audio_bytes).decode()
    md = f"""
        <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
    st.markdown(md, unsafe_allow_html=True)

# Main App UI
st.title("🏰 Fort Siloso Voice Assistant")
st.markdown("### Ask me anything about Fort Siloso!")
st.markdown("Record your question using the button below, and I'll respond with voice.")

# Sidebar for API key
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key_input = st.text_input(
        "OpenAI API Key",
        type="password",
        value=st.session_state.api_key,
        help="Enter your OpenAI API key. Get one at https://platform.openai.com/api-keys"
    )
    
    if api_key_input:
        st.session_state.api_key = api_key_input
        initialize_openai(api_key_input)
        st.success("✅ API Key configured!")
    else:
        st.warning("⚠️ Please enter your OpenAI API key to use the chatbot.")
    
    st.markdown("---")
    st.markdown("### About")
    st.info("""
    This voice assistant helps you learn about Fort Siloso, 
    a historic military fort on Sentosa Island, Singapore.
    
    **How to use:**
    1. Enter your OpenAI API key
    2. Click the microphone to record
    3. Ask your question
    4. Listen to the AI response
    """)
    
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

# Main content area
if not st.session_state.api_key:
    st.warning("👈 Please enter your OpenAI API key in the sidebar to begin.")
else:
    # Voice recorder
    st.markdown("### 🎤 Record Your Question")
    audio_bytes = audio_recorder(
        text="Click to record",
        recording_color="#e74c3c",
        neutral_color="#3498db",
        icon_name="microphone",
        icon_size="3x"
    )
    
    # Process audio when recorded
    if audio_bytes and len(audio_bytes) > 0:
        with st.spinner("🎧 Processing your voice..."):
            # Transcribe audio
            user_text = transcribe_audio(audio_bytes)
            
            if user_text:
                st.success(f"**You asked:** {user_text}")
                
                # Add user message to chat history
                st.session_state.messages.append({
                    "role": "user",
                    "content": user_text
                })
                
                # Get AI response
                with st.spinner("🤔 Thinking..."):
                    ai_response = get_ai_response(user_text)
                
                if ai_response:
                    # Add assistant message to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": ai_response
                    })
                    
                    # Convert response to speech
                    with st.spinner("🔊 Generating voice response..."):
                        audio_response = text_to_speech(ai_response)
                    
                    if audio_response:
                        # Display text response
                        st.markdown(f"**Assistant:** {ai_response}")
                        
                        # Auto-play audio response
                        autoplay_audio(audio_response)
                        
                        # Also provide download option
                        st.download_button(
                            label="📥 Download Response Audio",
                            data=audio_response,
                            file_name="fort_siloso_response.mp3",
                            mime="audio/mp3"
                        )

# Display conversation history
if st.session_state.messages:
    st.markdown("---")
    st.markdown("### 💬 Conversation History")
    
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>👤 You:</strong><br>{message["content"]}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>🏰 Assistant:</strong><br>{message["content"]}
                </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>Powered by OpenAI GPT-4 & Whisper | Built with Streamlit</small>
</div>
""", unsafe_allow_html=True)
