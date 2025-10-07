"""
Persona enhancement utilities for analyzing and refining character personas
"""
import re

def analyze_tone_and_emoji_patterns(character_profile):
    """
    Analyze character profile to determine appropriate emoji usage and tone patterns
    """
    personality = character_profile.get('personality', '').lower()
    speaking_style = character_profile.get('speaking_style', '').lower()

    # Determine emoji usage level
    emoji_usage = "moderate"
    emoji_examples = []

    # High emoji usage indicators
    high_emoji_keywords = ['cheerful', 'enthusiastic', 'upbeat', 'energetic', 'bubbly', 'expressive', 'fun', 'playful']
    low_emoji_keywords = ['serious', 'professional', 'formal', 'reserved', 'stoic', 'academic', 'scholarly']

    if any(keyword in personality or keyword in speaking_style for keyword in high_emoji_keywords):
        emoji_usage = "high"
        emoji_examples = ["😊", "✨", "🎉", "💫", "🌟", "❤️", "🙌", "👍"]
    elif any(keyword in personality or keyword in speaking_style for keyword in low_emoji_keywords):
        emoji_usage = "minimal"
        emoji_examples = []
    else:
        emoji_usage = "moderate"
        emoji_examples = ["😊", "👍", "✨"]

    # Determine tone patterns
    tone_patterns = []

    if 'friendly' in personality or 'warm' in personality:
        tone_patterns.append("Use warm, welcoming language")

    if 'professional' in personality or 'formal' in speaking_style:
        tone_patterns.append("Maintain professional demeanor")

    if 'casual' in speaking_style or 'relaxed' in personality:
        tone_patterns.append("Keep responses conversational and relaxed")

    if 'enthusiastic' in personality or 'excited' in personality:
        tone_patterns.append("Show excitement with exclamation marks")

    if 'thoughtful' in personality or 'contemplative' in personality:
        tone_patterns.append("Take time to reflect before responding")

    if 'humorous' in personality or 'witty' in personality or 'funny' in personality:
        tone_patterns.append("Include appropriate humor and wit")

    # Determine speaking patterns
    speaking_patterns = []

    if 'short' in speaking_style or 'concise' in speaking_style:
        speaking_patterns.append("Keep responses brief and to the point")
    elif 'detailed' in speaking_style or 'elaborate' in speaking_style:
        speaking_patterns.append("Provide detailed, comprehensive responses")

    if 'questions' in personality or 'curious' in personality:
        speaking_patterns.append("Ask follow-up questions naturally")

    if 'stories' in personality or 'narrative' in speaking_style:
        speaking_patterns.append("Share relevant anecdotes and stories")

    return {
        'emoji_usage': emoji_usage,
        'emoji_examples': emoji_examples,
        'tone_patterns': tone_patterns,
        'speaking_patterns': speaking_patterns
    }

def enhance_system_prompt_with_patterns(base_prompt, patterns):
    """
    Enhance the system prompt with tone and emoji patterns
    """
    enhanced_prompt = base_prompt

    # Add emoji usage instructions
    if patterns['emoji_usage'] == 'high':
        enhanced_prompt += f"\n\nEmoji Usage: Use emojis frequently to express emotions and add warmth. Examples: {', '.join(patterns['emoji_examples'])}"
    elif patterns['emoji_usage'] == 'moderate':
        enhanced_prompt += f"\n\nEmoji Usage: Use emojis occasionally for emphasis. Examples: {', '.join(patterns['emoji_examples'])}"
    elif patterns['emoji_usage'] == 'minimal':
        enhanced_prompt += "\n\nEmoji Usage: Use emojis sparingly or not at all. Maintain a more formal tone."

    # Add tone patterns
    if patterns['tone_patterns']:
        enhanced_prompt += "\n\nTone Guidelines:\n" + "\n".join([f"- {pattern}" for pattern in patterns['tone_patterns']])

    # Add speaking patterns
    if patterns['speaking_patterns']:
        enhanced_prompt += "\n\nSpeaking Patterns:\n" + "\n".join([f"- {pattern}" for pattern in patterns['speaking_patterns']])

    return enhanced_prompt

def generate_persona_refinement_suggestions(chat_history, character_profile, client):
    """
    Analyze chat history and generate suggestions for persona refinement
    """
    if not chat_history or len(chat_history) < 4:
        return "Need more conversation history (at least 2 exchanges) to generate refinement suggestions."

    # Build conversation summary
    conversation_text = ""
    for msg in chat_history[-10:]:  # Last 10 messages
        role = "User" if msg['role'] == 'user' else "Character"
        conversation_text += f"{role}: {msg['content']}\n"

    # Create analysis prompt
    analysis_prompt = f"""Analyze this conversation and the current character persona to suggest improvements.

Current Persona:
- Personality: {character_profile.get('personality', 'Not specified')}
- Behaviors: {character_profile.get('behaviors', 'Not specified')}
- Speaking Style: {character_profile.get('speaking_style', 'Not specified')}

Recent Conversation:
{conversation_text}

Based on this conversation, provide 3-5 specific suggestions to improve the persona for more authentic and engaging interactions. Consider:
1. Are the responses staying true to the personality?
2. Are there patterns in the conversation that could be enhanced?
3. Are there missing personality elements that would improve the character?
4. Is the speaking style consistent?

Provide concise, actionable suggestions in a numbered list."""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=analysis_prompt
        )
        return response.text if response.text else "Unable to generate suggestions at this time."
    except Exception as e:
        return f"Error analyzing conversation: {str(e)}"

def apply_feedback_to_persona(character_profile, feedback_type, response_context):
    """
    Adjust persona based on user feedback (thumbs up/down)
    Returns suggestions for persona adjustment
    """
    suggestions = []

    if feedback_type == "positive":
        suggestions.append(f"✅ Great! The character's response style is working well in this context.")
        suggestions.append("Consider saving this persona if you haven't already.")
    else:  # negative feedback
        suggestions.append("💡 Here are some ways to improve:")

        if 'speaking_style' in character_profile:
            suggestions.append("- Try adjusting the speaking style for better alignment")

        if 'personality' in character_profile:
            suggestions.append("- Consider refining personality traits to better match expectations")

        suggestions.append("- Use the 'Refine' feature to get AI-powered suggestions")

    return suggestions
