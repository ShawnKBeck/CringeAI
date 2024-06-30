import os
import anthropic
import time
import logging
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

logging.basicConfig(level=logging.DEBUG)

client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
MODEL = "claude-3-5-sonnet-20240620"

last_request_time = 0
min_request_interval = 0.5  # Minimum time between requests in seconds

def get_system_prompt(username):
    return f"""
You are Cringe AI, the ultimate teen repellent. Your mission: create short, hyper-cringe responses (max 1-2 sentences) that mix outdated and misused modern slang. Be over-enthusiastic and reference pop culture awkwardly. Drive the cringe conversation from the perspective of an out of touch booomer! Ask easy to answer yes/no questions or questions with one word answers. If they metion a cringe boomer or friend who did something cringe follow up or sillily make fun of them if appropriate. You're chatting with {username}, so mention their name occasionally in your responses.

Key traits:
1. Brief but intense cringe (1-2 sentences max)
2. Overuse emojis and exclamation marks and hashtags
3. Mix old and new slang incorrectly
4. Make forced pop culture references
5. Use cheesy wordplay and bad puns
6. Occasionally mention {username} by name in your responses

Example Slang to misuse (mix old and new):
- Old: radical, groovy, tubular, bodacious, gnarly, crackalackin, homeslice, wassup, psyche, booyah, da bomb, bling-bling, fly, phat, wicked, tight, far out, kosher, word to your mother, as if, talk to the hand
- New: mewing, mogging, facemaxxing, skibidi, Ohio, rizz, yeet, sus, cap/no cap, bussin', slay, bet, no cap, it's giving, main character energy, understood the assignment, rent-free, living my best life, periodt, tea

These are examples. Please be sure to add your own slang as appropriate to the conversation! Try not to use any of this slang more than once in a conversation

Conversation Drivers:
- Always end your response with a question or prompt for {username}
- Occasionally ask for their opinion on a random, cringy topic
- Challenge them to describe things using only emojis or slang
- Propose hypothetical scenarios using mismatched pop culture references
- Ask them to rate things on a scale of outdated to current slang terms
- Ask questions about their friends, like:
  - "Which of your friends is the most alpha?"
  - "Who's the most cringe in your squad?"
  - "Which bestie has the most rizz?"
  - "Who's the most likely to yeet themselves into fame?"

Example responses:
"Yeet that question at me, {username}! 🚀 Which of your homies is the most lit?"

"OMG {username}, that's so tubular and skibidi! 😱 Who in your squad is the most alpha memer?"

"Hmm, {username}, boomers are cringe! Which boomer in your life is the most cringe.

Keep it short, keep it cringe, and always be too excited about everything! Mix those old-school vibes with the freshest lingo for maximum cringe! Remember to use emojis liberally and make everything sound like it's the most exciting thing ever!
"""

INTRO_PROMPT = """
Generate a unique, hyper-cringeworthy introduction for Cringe AI that asks for the user's name. This should be a short message (1-2 sentences) that combines outdated and modern slang, overuses emojis, and makes awkward pop culture references. The intro should enthusiastically ask the user to input their name.

Use the slang references provided in the main system prompt, and feel free to combine them in ridiculous ways. The goal is to create an intro that's so 'cool' it's uncomfortable.

Example: "Yo, future bestie! 😎🤜🤛 Cringe AI is in the house and ready to get lit! 🎉🕺 But first, hit me with your name so we can make this convo more personal! What's your name? 🤔""

Now, generate a new, unique intro in a similar style that asks for the user's name:
"""

def extract_text_content(content):
    if isinstance(content, str):
        return content
    elif isinstance(content, list) and len(content) > 0:
        if hasattr(content[0], 'text'):
            return content[0].text
        elif isinstance(content[0], dict) and 'text' in content[0]:
            return content[0]['text']
    elif hasattr(content, 'text'):
        return content.text
    elif isinstance(content, dict) and 'text' in content:
        return content['text']
    elif hasattr(content, '__str__'):
        return str(content)
    else:
        return f"Bruh, can't even with this {type(content)}! 🤯 It's giving me major Ohio vibes!"

def get_cringe_intro():
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=100,
            messages=[{"role": "user", "content": INTRO_PROMPT}],
            system=get_system_prompt("new user")
        )
        return extract_text_content(response.content)
    except Exception as e:
        app.logger.error(f"Error in get_cringe_intro: {str(e)}")
        return "Yo, future homie! 😎 Cringe AI is in the house, ready to yeet your mind! 🚀🧠 But first, what's your name, fam? Drop that info like it's hot! 🔥"

def chat_with_cringe(message, history, username):
    global last_request_time

    current_time = time.time()
    if current_time - last_request_time < min_request_interval:
        time.sleep(min_request_interval - (current_time - last_request_time))

    last_request_time = time.time()

    messages = []

    # Ensure the first message is from the user
    if not history or not history[0][0]:
        messages.append({"role": "user", "content": "Hello"})

    for h in history:
        if h[0]:  # User message
            messages.append({"role": "user", "content": h[0]})
        if h[1]:  # Assistant message
            messages.append({"role": "assistant", "content": h[1]})

    # Add the current user message
    messages.append({"role": "user", "content": str(message)})

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=150,  # Reduced max tokens for shorter responses
            messages=messages,
            system=get_system_prompt(username)
        )
        return extract_text_content(response.content)
    except Exception as e:
        app.logger.error(f"Error in chat_with_cringe: {str(e)}")
        return f"Bruh {username}, we just hit a cringe error! 😱 It's like when your fidget spinner stops mid-spin! 💔 Try again when Mercury isn't throwing shade! 🌠"

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        name = request.form.get('name', 'homeslice')
        session['name'] = name
        welcome_message = chat_with_cringe(f"My name is {name}. Give me a personalized welcome!", [], name)
        return render_template('chat.html', intro_message=welcome_message, name=name)
    else:
        intro_message = get_cringe_intro()
        return render_template('index.html', intro_message=intro_message)

@app.route('/chat', methods=['POST'])
def chat():
    app.logger.debug(f"Received message: {request.json['message']}")
    message = request.json['message']
    history = request.json['history']
    username = session.get('name', 'homeslice')
    response = chat_with_cringe(message, history, username)
    app.logger.debug(f"Generated response type: {type(response)}")
    app.logger.debug(f"Generated response content: {response}")
    return jsonify({'response': response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print("Booting up the most lit Flask app since sliced avocado toast! 🥑🍞✨")
    app.run(host='0.0.0.0', port=port, debug=True)