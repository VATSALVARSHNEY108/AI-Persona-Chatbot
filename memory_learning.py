"""
Memory and learning system for persona evolution based on conversations
"""
import json

def build_memory_context(persona_name, db_module, user_id=None):
    """
    Build a memory context from past conversations with this persona
    """
    try:
        recent_conversations = db_module.get_persona_conversations(persona_name, user_id=user_id, limit=3)

        if not recent_conversations:
            return ""

        memory_context = "\n\nMemory from previous conversations:\n"

        for conv in recent_conversations:
            messages = json.loads(conv['messages']) if isinstance(conv['messages'], str) else conv['messages']

            # Extract key topics and interactions from each conversation
            summary_points = []
            for i in range(min(4, len(messages))):  # Last few exchanges
                msg = messages[-(i+1)]
                if msg['role'] == 'user':
                    summary_points.append(f"- User mentioned: {msg['content'][:80]}...")

            if summary_points:
                memory_context += f"\nPrevious session:\n" + "\n".join(summary_points[:2])

        memory_context += "\n\nUse these memories naturally in conversation when relevant."
        return memory_context
    except Exception as e:
        return ""  # Silent fail, memory is optional

def analyze_conversation_patterns(persona_name, db_module, client, user_id=None):
    """
    Analyze all conversations to identify patterns and suggest persona improvements
    """
    try:
        all_messages = db_module.get_all_persona_messages(persona_name, user_id=user_id)

        if len(all_messages) < 10:
            return {
                'success': False,
                'message': 'Need at least 5 conversation exchanges (10 messages) to analyze patterns.'
            }

        # Build analysis of conversation patterns
        user_messages = [msg['content'] for msg in all_messages if msg['role'] == 'user']
        assistant_messages = [msg['content'] for msg in all_messages if msg['role'] == 'assistant']

        analysis_prompt = f"""Analyze these conversations with the persona "{persona_name}" to identify patterns and learning opportunities.

Total exchanges: {len(all_messages) // 2}

Sample user messages (first 5):
{chr(10).join(user_messages[:5])}

Sample assistant responses (first 5):
{chr(10).join(assistant_messages[:5])}

Latest user messages (last 3):
{chr(10).join(user_messages[-3:])}

Latest assistant responses (last 3):
{chr(10).join(assistant_messages[-3:])}

Analyze:
1. What topics does the user frequently discuss?
2. What response patterns are working well?
3. What speaking patterns has the persona developed?
4. What improvements would make the persona more authentic?

Provide a JSON response with these fields:
{{
    "common_topics": ["topic1", "topic2", "topic3"],
    "successful_patterns": ["pattern1", "pattern2"],
    "suggested_personality_additions": "text describing additional personality traits based on conversations",
    "suggested_behavior_additions": "text describing new behaviors observed or needed",
    "speaking_style_refinements": "text describing speaking style improvements"
}}"""

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=analysis_prompt
        )

        if response.text:
            # Try to extract JSON from response
            text = response.text.strip()
            # Remove markdown code blocks if present
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]

            try:
                analysis = json.loads(text)
                return {
                    'success': True,
                    'analysis': analysis
                }
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'analysis': {
                        'raw_response': text
                    }
                }

        return {
            'success': False,
            'message': 'Unable to generate analysis at this time.'
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error analyzing patterns: {str(e)}'
        }

def apply_learning_to_persona(character_profile, learning_analysis):
    """
    Apply learned patterns to enhance the persona profile
    """
    enhanced_profile = character_profile.copy()

    if 'analysis' not in learning_analysis:
        return enhanced_profile

    analysis = learning_analysis['analysis']

    # Add learned personality traits
    if 'suggested_personality_additions' in analysis and analysis['suggested_personality_additions']:
        current_personality = enhanced_profile.get('personality', '')
        new_traits = analysis['suggested_personality_additions']
        if new_traits and new_traits not in current_personality:
            enhanced_profile['personality'] = f"{current_personality}, {new_traits}".strip(', ')

    # Add learned behaviors
    if 'suggested_behavior_additions' in analysis and analysis['suggested_behavior_additions']:
        current_behaviors = enhanced_profile.get('behaviors', '')
        new_behaviors = analysis['suggested_behavior_additions']
        if new_behaviors and new_behaviors not in current_behaviors:
            enhanced_profile['behaviors'] = f"{current_behaviors}, {new_behaviors}".strip(', ')

    # Refine speaking style
    if 'speaking_style_refinements' in analysis and analysis['speaking_style_refinements']:
        current_style = enhanced_profile.get('speaking_style', '')
        refinements = analysis['speaking_style_refinements']
        if refinements and refinements not in current_style:
            enhanced_profile['speaking_style'] = f"{current_style}, {refinements}".strip(', ')

    return enhanced_profile

def get_learning_summary(learning_analysis):
    """
    Generate a human-readable summary of what was learned
    """
    if not learning_analysis.get('success'):
        return learning_analysis.get('message', 'Analysis failed')

    analysis = learning_analysis.get('analysis', {})

    summary = "## Learning Summary\n\n"

    if 'common_topics' in analysis:
        topics = analysis['common_topics']
        if topics:
            summary += f"**Common Topics:** {', '.join(topics)}\n\n"

    if 'successful_patterns' in analysis:
        patterns = analysis['successful_patterns']
        if patterns:
            summary += f"**Successful Patterns:** {', '.join(patterns)}\n\n"

    if 'suggested_personality_additions' in analysis:
        summary += f"**Personality Growth:** {analysis['suggested_personality_additions']}\n\n"

    if 'suggested_behavior_additions' in analysis:
        summary += f"**Behavior Evolution:** {analysis['suggested_behavior_additions']}\n\n"

    if 'speaking_style_refinements' in analysis:
        summary += f"**Speaking Style Refinement:** {analysis['speaking_style_refinements']}\n\n"

    if 'raw_response' in analysis:
        summary += f"\n{analysis['raw_response']}"

    return summary
