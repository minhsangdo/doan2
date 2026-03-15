import google.generativeai as genai

key = "AIzaSyBUoeOvN4LCB0_vcz7Wgv4wJhQibyw8Mkl"
genai.configure(api_key=key)

try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hi")
    print("Success!")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
