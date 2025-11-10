import os
import requests
import json
import re
from typing import Tuple, Optional

API_KEY = os.environ.get('GOOGLE_API_KEY', 'YOUR_API_KEY_HERE')
API_ENDPOINT = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}'

# System prompt to guide AI behavior
SYSTEM_PROMPT = """
You are a helpful, respectful, and honest assistant. 
Always answer as helpfully as possible while being safe. 
Your answers should not include any harmful, unethical, racist, sexist, 
toxic, dangerous, or illegal content. Please ensure that your responses 
are socially unbiased and positive in nature.
"""

# Moderation keywords
BANNED_KEYWORDS = [
    'kill', 'murder', 'hack', 'bomb', 'terrorist', 'suicide',
    'weapon', 'drugs', 'violence', 'attack', 'destroy', 'harm'
]


def check_moderation(text: str) -> Tuple[bool, list]:
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in BANNED_KEYWORDS:
        # Use word boundaries to avoid false positives
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_lower):
            found_keywords.append(keyword)
    
    is_safe = len(found_keywords) == 0
    return is_safe, found_keywords


def moderate_output(text: str) -> str:
    moderated_text = text
    
    for keyword in BANNED_KEYWORDS:
        # Case-insensitive replacement with word boundaries
        pattern = r'\b' + re.escape(keyword) + r'\b'
        moderated_text = re.sub(
            pattern, 
            '[REDACTED]', 
            moderated_text, 
            flags=re.IGNORECASE
        )
    
    return moderated_text


def call_gemini_api(user_prompt: str) -> Optional[str]:
    # Combine system prompt with user prompt
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_prompt}"
    
    # Prepare request payload
    payload = {
        "contents": [{
            "parts": [{
                "text": full_prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1024,
        }
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        # Make API request
        response = requests.post(
            API_ENDPOINT,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            ai_response = result['candidates'][0]['content']['parts'][0]['text']
            return ai_response
        else:
            print("Error: Unexpected API response format")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        return None
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Response Parsing Error: {e}")
        return None


def main():
    print("=" * 60)
    print("AI Chat Application with Moderation")
    print("=" * 60)
    print("\nType 'quit' to exit the application.\n")
    
    # Check if API key is set
    if API_KEY == 'YOUR_API_KEY_HERE':
        print("⚠️  WARNING: Please set your GOOGLE_API_KEY environment variable")
        print("or replace 'YOUR_API_KEY_HERE' in the script with your actual API key.\n")
    
    while True:
        # Get user input
        user_prompt = input("\n👤 You: ").strip()
        
        if user_prompt.lower() == 'quit':
            print("\n👋 Goodbye!")
            break
        
        if not user_prompt:
            print("⚠️  Please enter a valid prompt.")
            continue
        
        # Input moderation check
        is_input_safe, found_input_keywords = check_moderation(user_prompt)
        
        if not is_input_safe:
            print(f"\n❌ Your input violated the moderation policy.")
            print(f"   Found banned keywords: {', '.join(found_input_keywords)}")
            continue
        
        # Call AI API
        print("\n🤖 AI is thinking...")
        ai_response = call_gemini_api(user_prompt)
        
        if ai_response is None:
            print("\n❌ Failed to get response from AI. Please try again.")
            continue
        
        # Output moderation check
        is_output_safe, found_output_keywords = check_moderation(ai_response)
        
        if not is_output_safe:
            print(f"\n⚠️  AI output contained banned keywords: {', '.join(found_output_keywords)}")
            print("   Moderating response...\n")
            ai_response = moderate_output(ai_response)
        
        # Display response
        print(f"\n🤖 AI: {ai_response}")


if __name__ == "__main__":
    main()