import streamlit as st
import os
from google import genai
from google.genai import types
import json
from datetime import datetime
import persona_enhancer


# Initialize client
@st.cache_resource
def get_gemini_client():
    """Initialize and cache the  client"""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        st.error("GEMINI_API_KEY environment variable is not set. Please provide your Gemini API key.")
        st.stop()
    return genai.Client(api_key=api_key)


def generate_system_prompt(character_profile):
    """Generate a system prompt based on the character profile"""
    prompt = "You are roleplaying as a character with the following attributes:\n\n"

    if character_profile.get('name'):
        prompt += f"Name: {character_profile['name']}\n\n"

    if character_profile.get('personality'):
        prompt += f"Personality Traits: {character_profile['personality']}\n\n"

    if character_profile.get('behaviors'):
        prompt += f"Behaviors and Habits: {character_profile['behaviors']}\n\n"

    if character_profile.get('speaking_style'):
        prompt += f"Speaking Style: {character_profile['speaking_style']}\n\n"

    if character_profile.get('mannerisms'):
        prompt += f"Mannerisms and Quirks: {character_profile['mannerisms']}\n\n"

    if character_profile.get('background'):
        prompt += f"Background: {character_profile['background']}\n\n"

    prompt += """
Instructions:
- Stay in character at all times
- Respond naturally as this person would
- Use the speaking style and mannerisms described
- Draw from the personality traits and behaviors when forming responses
- Be conversational and engaging
- If asked about things outside your character's knowledge, respond as that character would
"""

    return prompt


def chat_with_persona(client, character_profile, user_message, chat_history):
    """Generate AI response using the character persona with enhanced tone and emoji patterns"""
    try:
        system_prompt = generate_system_prompt(character_profile)

        # Analyze and enhance with tone/emoji patterns
        patterns = persona_enhancer.analyze_tone_and_emoji_patterns(character_profile)
        enhanced_prompt = persona_enhancer.enhance_system_prompt_with_patterns(system_prompt, patterns)

        # Build conversation context
        conversation_parts = []

        # Add chat history
        for message in chat_history:
            if message['role'] == 'user':
                conversation_parts.append(f"User: {message['content']}")
            else:
                conversation_parts.append(f"Character: {message['content']}")

        # Add current user message
        conversation_parts.append(f"User: {user_message}")
        conversation_context = "\n".join(conversation_parts)

        full_prompt = f"{enhanced_prompt}\n\nConversation:\n{conversation_context}\n\nCharacter:"

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.8,
                max_output_tokens=1000
            )
        )

        return response.text if response.text else "I'm having trouble responding right now."

    except Exception as e:
        return f"Error generating response: {str(e)}"


def main():
    st.set_page_config(
        page_title="AI Persona Chatbot",
        page_icon="🤖",
        layout="wide"
    )

    # Sidebar - About section
    with st.sidebar:
        st.header("👤 About")
        st.markdown("""
        **AI Persona Chatbot**

        Create and chat with custom AI characters!

        ---

        **Made by:** Vatsal Varshney 🤪

        **Connect:**
        - 🌐 [Website/Portfolio](https://inoneboxvatsalvarshney108.streamlit.app/)
        - 💼 [LinkedIn](https://www.linkedin.com/in/vatsal-varshney108/)
        - 😎 [CodeForces](https://codeforces.com/profile/Vatsal_Varshney-69)
        - 🫠 [Leet Code](https://leetcode.com/u/VATSAL_VARSHNEY/)
        - 📱 [Github](https://github.com/VATSALVARSHNEY108)
        """)

    # Main app
    st.title("🤖 AI Persona Chatbot")
    st.markdown("Create a personalized AI character and chat with them!")

    # Initialize session state
    if 'character_profile' not in st.session_state:
        st.session_state.character_profile = {}

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'persona_created' not in st.session_state:
        st.session_state.persona_created = False

    # Initialize client
    # Use st.status to hide the loading message when initializing the cached resource
    with st.status("Initializing AI...", expanded=False) as status:
        client = get_gemini_client()
        status.update(label="Bhai/Behn Vatsal ne banaya hai toh instructions niche jaakr dekhlo",
         "&& english galat likhoge tabhi saajh jayge NLP bahut ache se apply kari hai ", state="complete", expanded=False)

    # This is often sufficient to hide the loading message on the first run,
    # but the next method is more direct if you can't see the call stack.

    # No user authentication needed
    user_id = None

    # Create two columns for the layout
    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("📝 Character Builder")

        # Character creation section
        # Character profile input form
        with st.form("character_form"):
            st.subheader("Define Your Character")

            name = st.text_input(
                "Character Name (optional)",
                value=st.session_state.character_profile.get('name', ''),
                placeholder="e.g., Alex the Adventurer"
            )

            personality = st.text_area(
                "Personality Traits*",
                value=st.session_state.character_profile.get('personality', ''),
                placeholder="e.g., Cheerful, curious, optimistic, loves to help others, has a great sense of humor...",
                height=100
            )

            behaviors = st.text_area(
                "Behaviors & Habits",
                value=st.session_state.character_profile.get('behaviors', ''),
                placeholder="e.g., Always asks follow-up questions, tends to use metaphors, loves telling stories...",
                height=100
            )

            speaking_style = st.text_area(
                "Speaking Style",
                value=st.session_state.character_profile.get('speaking_style', ''),
                placeholder="e.g., Casual and friendly, uses lots of emojis, speaks in short sentences, formal tone...",
                height=80
            )

            mannerisms = st.text_area(
                "Mannerisms & Quirks",
                value=st.session_state.character_profile.get('mannerisms', ''),
                placeholder="e.g., Often says 'you know what I mean?', makes pop culture references, uses specific catchphrases...",
                height=80
            )

            background = st.text_area(
                "Background (optional)",
                value=st.session_state.character_profile.get('background', ''),
                placeholder="e.g., A travel blogger from California, former teacher, loves hiking and photography...",
                height=80
            )

            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
                create_persona = st.form_submit_button("🚀 Create Persona", type="primary", use_container_width=True)

            with col_btn2:
                clear_persona = st.form_submit_button("🗑️ Clear All", use_container_width=True)

        # Handle form submissions
        if create_persona:
            if personality and personality.strip():
                st.session_state.character_profile = {
                    'name': name,
                    'personality': personality,
                    'behaviors': behaviors,
                    'speaking_style': speaking_style,
                    'mannerisms': mannerisms,
                    'background': background
                }
                st.session_state.persona_created = True
                st.session_state.chat_history = []
                st.success("✅ Persona created successfully!")
                st.rerun()
            else:
                st.error("❌ Please provide at least personality traits to create a persona.")

        if clear_persona:
            st.session_state.character_profile = {}
            st.session_state.chat_history = []
            st.session_state.persona_created = False
            st.success("🧹 Persona cleared!")
            st.rerun()

        # Display current persona summary
        if st.session_state.persona_created and st.session_state.character_profile:
            st.divider()
            st.subheader("Current Persona")
            profile = st.session_state.character_profile

            if profile.get('name'):
                st.write(f"**Name:** {profile['name']}")

            if profile.get('personality'):
                st.write(
                    f"**Personality:** {profile['personality'][:100]}{'...' if len(profile['personality']) > 100 else ''}")

            st.write("✅ Ready to chat!")

    with col2:
        st.header("💬 Chat Interface")

        if not st.session_state.persona_created:
            st.info("👈 Please create a character persona first to start chatting!")
        else:
            # Chat history display
            chat_container = st.container()

            with chat_container:
                if st.session_state.chat_history:
                    for message in st.session_state.chat_history:
                        if message['role'] == 'user':
                            with st.chat_message("user"):
                                st.write(message['content'])
                        else:
                            with st.chat_message("assistant"):
                                st.write(message['content'])
                else:
                    character_name = st.session_state.character_profile.get('name', 'Your AI Character')
                    st.info(f"Start a conversation with {character_name}!")

            # Chat input
            user_input = st.chat_input("Type your message here...")

            if user_input:
                # Add user message to history
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': user_input
                })

                # Generate AI response
                with st.spinner("🤔 Thinking..."):
                    ai_response = chat_with_persona(
                        client,
                        st.session_state.character_profile,
                        user_input,
                        st.session_state.chat_history[:-1]  # Exclude the current message
                    )

                # Add AI response to history
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': ai_response
                })

                # Rerun to update the chat display
                st.rerun()

            # Clear chat button
            if st.session_state.chat_history:
                if st.button("🗑️ Clear Chat", use_container_width=True):
                    st.session_state.chat_history = []
                    st.rerun()

    # Footer
    st.markdown("---")
    st.markdown(
        "**💡 Tips:** Be specific with personality traits for authentic responses. "
        "The more detailed you are with behaviors and mannerisms, the more unique your AI character will be!"
    )
    st.header("VATSAL is the creator Instructions kuch nahi hai 😁")

if __name__ == "__main__":
    main()


