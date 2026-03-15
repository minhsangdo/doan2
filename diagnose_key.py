import google.generativeai as genai

keys_to_test = [
    "AIzaSyBUoeOvN4LCB0_vcz7Wqv4wJhQibyw8MkI", # User text
    "AIzaSyBUoeOvN4LCB0_vcz7Wqv4wJhQibyw8Mkl", # small l
    "AIzaSyBUoeOvN4LCB0_vcz7Wqv4wJhQibyw8Mk1", # number 1
]

for key in keys_to_test:
    print(f"\n--- Testing key: {key} ---")
    try:
        genai.configure(api_key=key)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Found model: {m.name}")
                # Try a quick test with the first model found
                model = genai.GenerativeModel(m.name)
                resp = model.generate_content("Hi", generation_config={"max_output_tokens": 1})
                print(f"Test Success with {m.name}!")
                break
    except Exception as e:
        print(f"FAILED: {e}")
