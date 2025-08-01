from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
from google.genai import types
import os
import asyncio


def call_gemini(prompt, use_search=True, url_context=True, temperature=0.9, model_name="gemini-2.0-flash"):
    """
    Call Gemini with Google Search capability
    
    Args:
        prompt (str): The input prompt/question
        use_search (bool): Whether to enable Google Search
    
    Returns:
        str: The response from Gemini
    """
    
    # Configure the model
    client = genai.Client(api_key=api_key)  
    model_id = model_name   

    
    # Enable Google Search if requested
    tools = []
    if use_search:
        tools.append(Tool(google_search = GoogleSearch()))
    if url_context:
        tools.append(Tool(url_context=types.UrlContext()))

    try:
        # Generate response
        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
            config=GenerateContentConfig(
            tools=tools,
            response_modalities=["TEXT"],
            temperature=temperature,  
            max_output_tokens=2048,   
    )
        )
        
        return response
    
    except Exception as e:
        return f"Error: {str(e)}"

async def async_call_gemini(*args, **kwargs):
    return await asyncio.to_thread(call_gemini, *args, **kwargs)