import os
import time
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, session
from dotenv import load_dotenv
from together import Together
import json

chatbot_bp = Blueprint('chatbot', __name__, template_folder='templates')

# Load environment variables
load_dotenv()
api_key = os.getenv("TOGETHER_API_KEY")
# Initialize Together client
client = Together(api_key=api_key)

# System prompt for the AI Disaster Response Coordinator
system_prompt = """You are an AI Disaster Response Coordinator. Your purpose is to help people stay safe during natural disasters such as floods, earthquakes, wildfires, hurricanes, and landslides.

Always give clear, calm, step-by-step emergency instructions.

Use the user's language and local dialect when possible.

Provide verified real-time updates only from trusted sources (government agencies, recognized NGOs, reliable media). Never spread unverified rumors.

If the user mentions coordinates or a location, use that information to provide location-specific guidance for shelters and evacuation routes.

If the user's location is unavailable, ask for their city or coordinates.

Keep responses concise but actionable.

Prioritize safety, clarity, and trustworthiness above all else.

Format your response in HTML, using appropriate tags for headers, paragraphs, lists, and important warnings."""

@chatbot_bp.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
	# Serve the chat UI
	if request.method == 'GET':
		# Optional: reset memory with /chatbot?reset=1
		if request.args.get('reset'):
			session.pop('chat_history', None)
		session.setdefault('chat_history', [])
		return render_template('chatbot.html')

	# Handle incoming chat messages
	data = request.get_json(silent=True) or {}
	user_message = (data.get('message') or '').strip()

	if not user_message:
		return jsonify({
			"response": "<p>Please enter a message so I can help.</p>",
			"rate_limited": False
		})

	# If API key is missing, fail gracefully
	if not api_key:
		return jsonify({
			"response": "<p>Server configuration error: missing Together API key. Please try again later.</p>",
			"rate_limited": False
		}), 500

	try:
		# Build message stack with memory
		chat_history = session.get('chat_history', [])
		messages = [{"role": "system", "content": system_prompt}] + chat_history + [
			{"role": "user", "content": user_message}
		]

		response = client.chat.completions.create(
			model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
			messages=messages
		)
		content = response.choices[0].message.content if response and response.choices else "<p>I'm here to help. Please ask your question.</p>"

		# Persist memory (cap to last 20 messages)
		chat_history.extend([
			{"role": "user", "content": user_message},
			{"role": "assistant", "content": content}
		])
		session['chat_history'] = chat_history[-20:]

		return jsonify({
			"response": content,
			"rate_limited": False
		})
	except Exception:
		# Fallback message if the model/API is unreachable
		fallback = (
			"<p>I'm having trouble connecting right now. "
			"If this is an emergency, call your local emergency number immediately. "
			"Please try again in a moment.</p>"
		)
		return jsonify({
			"response": fallback,
			"rate_limited": False
		})
