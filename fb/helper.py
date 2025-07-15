from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv  

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GEMINI_API_KEY,
)

def detect_ethnicity_from_name(name):
    prompt = f"""
Given the following name, categorize the most likely ethnicity as one of these five options: South Asian, Arabic, Asian, White, or Black. If unsure, choose the closest category.

Name: {name}
Ethnicity:
"""
    response = llm.invoke(prompt)
    return response.content if hasattr(response, 'content') else response
