import google.generativeai as genai

keys = [
    "AIzaSyBUoeOvN4LCB0_vcz7Wqv4wJhQibyw8MkI",
    "AIzaSyBUoeOvN4LCB0_vcz7Wqv4wJhQibyw8Mkl", # l
    "AIzaSyBUoeOvN4LCB0_vcz7Wqv4wJhQibyw8Mk1", # 1
    "AIzaSyBUoeOvN4LCB0_vcz7Wqv4wJhQibywBMkl", # B
    "AIzaSyBUoeOvN4LCBO_vcz7Wqv4wJhQibyw8Mkl", # O
]

for k in keys:
    try:
        genai.configure(api_key=k)
        # Try a real call
        m = genai.GenerativeModel('gemini-1.5-flash')
        m.generate_content("Hi", generation_config={"max_output_tokens": 1})
        print(f"CORRECT_KEY_FOUND: {k}")
        break
    except:
        pass
