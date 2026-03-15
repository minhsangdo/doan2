import google.generativeai as genai

key = "AIzaSyBUoeOvN4LCB0_vcz7Wqv4wJhQibyw8MkI"
print(f"Testing key: {key}")
try:
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hi", generation_config={"max_output_tokens": 10})
    print("SUCCESS!")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"FAILED: {e}")
