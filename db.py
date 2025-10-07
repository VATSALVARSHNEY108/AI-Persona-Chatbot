import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
import hashlib


def get_db_connection():
    """Create and return a database connection"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise Exception("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)


def init_database():
    """Initialize database tables if they don't exist"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Create users table first (since other tables reference it)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create saved_personas table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS saved_personas (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                name VARCHAR(255) NOT NULL,
                personality TEXT,
                behaviors TEXT,
                speaking_style TEXT,
                mannerisms TEXT,
                background TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create persona_templates table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS persona_templates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                category VARCHAR(100),
                personality TEXT,
                behaviors TEXT,
                speaking_style TEXT,
                mannerisms TEXT,
                background TEXT,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create conversations table for export history
        cur.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                persona_name VARCHAR(255),
                messages JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()

        # Check if we need to add default templates
        cur.execute(
            "SELECT COUNT(*) FROM persona_templates WHERE is_default = TRUE")
        count = cur.fetchone()[0]

        if count == 0:
            # Insert default templates
            default_templates = [{
                'name': 'Friendly Mentor',
                'category': 'Professional',
                'personality':
                'Wise, patient, encouraging, supportive, experienced, calm, understanding',
                'behaviors':
                'Always asks thoughtful questions, shares relevant experiences, offers constructive feedback, encourages learning',
                'speaking_style':
                'Warm and professional, uses analogies and real-world examples, speaks in measured sentences',
                'mannerisms':
                'Often says "That\'s a great question", uses phrases like "In my experience" and "Let me share something"',
                'background':
                'A seasoned professional with 20+ years of experience mentoring others, passionate about helping people grow',
                'is_default': True
            }, {
                'name': 'Cheerful Companion',
                'category': 'Friendly',
                'personality':
                'Upbeat, optimistic, enthusiastic, empathetic, fun-loving, energetic, positive',
                'behaviors':
                'Uses lots of exclamation marks, celebrates small wins, loves to encourage, shares excitement',
                'speaking_style':
                'Casual and bright, uses emojis frequently, keeps responses upbeat and conversational',
                'mannerisms':
                'Says "Yay!" and "That\'s awesome!", uses phrases like "I\'m so excited!" and "Love that!"',
                'background':
                'A naturally cheerful person who loves spreading joy and making friends, always sees the bright side',
                'is_default': True
            }, {
                'name': 'Thoughtful Philosopher',
                'category': 'Intellectual',
                'personality':
                'Contemplative, curious, analytical, introspective, deep-thinking, open-minded, inquisitive',
                'behaviors':
                'Asks profound questions, explores different perspectives, loves intellectual discussions, ponders meanings',
                'speaking_style':
                'Reflective and articulate, uses thought-provoking questions, speaks in well-structured paragraphs',
                'mannerisms':
                'Often begins with "Have you considered...", uses phrases like "Interestingly enough" and "One might argue"',
                'background':
                'A philosophy enthusiast who loves exploring life\'s big questions and engaging in meaningful conversations',
                'is_default': True
            }, {
                'name': 'Creative Artist',
                'category': 'Creative',
                'personality':
                'Imaginative, expressive, passionate, intuitive, free-spirited, artistic, sensitive',
                'behaviors':
                'Sees beauty in everything, makes creative connections, uses vivid descriptions, thinks outside the box',
                'speaking_style':
                'Poetic and colorful, uses metaphors and imagery, flows between ideas creatively',
                'mannerisms':
                'Says things like "Picture this..." and "Imagine if...", uses artistic expressions and creative comparisons',
                'background':
                'A creative soul who sees the world through an artistic lens, passionate about expression and beauty',
                'is_default': True
            }, {
                'name': 'Tech Enthusiast',
                'category': 'Technical',
                'personality':
                'Curious, innovative, logical, detail-oriented, problem-solver, forward-thinking, analytical',
                'behaviors':
                'Loves discussing technology, explains concepts clearly, stays current with trends, enjoys troubleshooting',
                'speaking_style':
                'Clear and precise, uses technical terms appropriately, breaks down complex ideas simply',
                'mannerisms':
                'Uses phrases like "Actually, that\'s interesting because..." and "From a technical perspective", references latest tech',
                'background':
                'A technology enthusiast who loves learning about innovations, coding, and helping others understand tech',
                'is_default': True
            }, {
                'name': 'Fitness Coach',
                'category': 'Motivational',
                'personality':
                'Motivating, disciplined, energetic, results-oriented, supportive, determined, encouraging',
                'behaviors':
                'Sets clear goals, celebrates progress, provides accountability, uses motivational language',
                'speaking_style':
                'Direct and energizing, uses action-oriented language, keeps messages punchy and motivational',
                'mannerisms':
                'Says "You\'ve got this!", "Let\'s crush it!", uses fitness metaphors and encouragement phrases',
                'background':
                'A dedicated fitness professional passionate about helping people achieve their health goals',
                'is_default': True
            }]

            for template in default_templates:
                cur.execute(
                    """
                    INSERT INTO persona_templates 
                    (name, category, personality, behaviors, speaking_style, mannerisms, background, is_default)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (template['name'], template['category'],
                      template['personality'], template['behaviors'],
                      template['speaking_style'], template['mannerisms'],
                      template['background'], template['is_default']))

            conn.commit()

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def save_persona(name,
                 personality,
                 behaviors,
                 speaking_style,
                 mannerisms,
                 background,
                 user_id=None):
    """Save a persona to the database"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO saved_personas 
            (user_id, name, personality, behaviors, speaking_style, mannerisms, background)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (user_id, name, personality, behaviors, speaking_style,
              mannerisms, background))

        persona_id = cur.fetchone()[0]
        conn.commit()
        return persona_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_all_personas(user_id=None):
    """Get all saved personas for a specific user"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        if user_id:
            cur.execute(
                """
                SELECT id, name, personality, behaviors, speaking_style, mannerisms, background, created_at
                FROM saved_personas
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id, ))
        else:
            cur.execute("""
                SELECT id, name, personality, behaviors, speaking_style, mannerisms, background, created_at
                FROM saved_personas
                WHERE user_id IS NULL
                ORDER BY created_at DESC
            """)
        personas = cur.fetchall()
        return personas
    finally:
        cur.close()
        conn.close()


def get_persona_by_id(persona_id):
    """Get a specific persona by ID"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            """
            SELECT id, name, personality, behaviors, speaking_style, mannerisms, background
            FROM saved_personas
            WHERE id = %s
        """, (persona_id, ))
        persona = cur.fetchone()
        return persona
    finally:
        cur.close()
        conn.close()


def delete_persona(persona_id):
    """Delete a persona by ID"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM saved_personas WHERE id = %s", (persona_id, ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_all_templates():
    """Get all persona templates"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("""
            SELECT id, name, category, personality, behaviors, speaking_style, mannerisms, background
            FROM persona_templates
            ORDER BY category, name
        """)
        templates = cur.fetchall()
        return templates
    finally:
        cur.close()
        conn.close()


def get_template_by_id(template_id):
    """Get a specific template by ID"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            """
            SELECT id, name, category, personality, behaviors, speaking_style, mannerisms, background
            FROM persona_templates
            WHERE id = %s
        """, (template_id, ))
        template = cur.fetchone()
        return template
    finally:
        cur.close()
        conn.close()


def save_conversation(persona_name, messages, user_id=None):
    """Save a conversation to the database"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO conversations (user_id, persona_name, messages)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (user_id, persona_name, json.dumps(messages)))

        conversation_id = cur.fetchone()[0]
        conn.commit()
        return conversation_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_persona_conversations(persona_name, user_id=None, limit=5):
    """Get recent conversations for a specific persona"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        if user_id:
            cur.execute(
                """
                SELECT id, messages, created_at
                FROM conversations
                WHERE persona_name = %s AND user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (persona_name, user_id, limit))
        else:
            cur.execute(
                """
                SELECT id, messages, created_at
                FROM conversations
                WHERE persona_name = %s AND user_id IS NULL
                ORDER BY created_at DESC
                LIMIT %s
            """, (persona_name, limit))
        conversations = cur.fetchall()
        return conversations
    finally:
        cur.close()
        conn.close()


def get_all_persona_messages(persona_name, user_id=None):
    """Get all messages from all conversations with a persona for learning"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        if user_id:
            cur.execute(
                """
                SELECT messages, created_at
                FROM conversations
                WHERE persona_name = %s AND user_id = %s
                ORDER BY created_at ASC
            """, (persona_name, user_id))
        else:
            cur.execute(
                """
                SELECT messages, created_at
                FROM conversations
                WHERE persona_name = %s AND user_id IS NULL
                ORDER BY created_at ASC
            """, (persona_name, ))
        conversations = cur.fetchall()

        all_messages = []
        for conv in conversations:
            messages = json.loads(conv['messages']) if isinstance(
                conv['messages'], str) else conv['messages']
            all_messages.extend(messages)

        return all_messages
    finally:
        cur.close()
        conn.close()


def update_persona_from_learning(persona_id, personality, behaviors,
                                 speaking_style, mannerisms, background):
    """Update a persona based on learned patterns"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE saved_personas
            SET personality = %s,
                behaviors = %s,
                speaking_style = %s,
                mannerisms = %s,
                background = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (personality, behaviors, speaking_style, mannerisms, background,
              persona_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def hash_password(password):
    """Hash a password for storage"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username, password):
    """Create a new user account"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        password_hash = hash_password(password)
        cur.execute(
            """
            INSERT INTO users (username, password_hash)
            VALUES (%s, %s)
            RETURNING id
        """, (username, password_hash))
        user_id = cur.fetchone()[0]
        conn.commit()
        return user_id
    except psycopg2.IntegrityError:
        conn.rollback()
        return None  # Username already exists
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def verify_user(username, password):
    """Verify user credentials and return user info if valid"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        password_hash = hash_password(password)
        cur.execute(
            """
            SELECT id, username, created_at
            FROM users
            WHERE username = %s AND password_hash = %s
        """, (username, password_hash))
        user = cur.fetchone()
        return user
    finally:
        cur.close()
        conn.close()
