import os
from dotenv import load_dotenv
import google.genai as genai

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

if api_key:
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='models/gemini-2.0-flash',
            contents='Say hello and confirm you are working for Smart EV Charging platform in one line'
        )
        print('✅ Gemini API Connection Successful!')
        print(f'📝 Response: {response.text}')
    except Exception as e:
        print(f'❌ Error: {str(e)[:300]}')
else:
    print('❌ API Key not found')
