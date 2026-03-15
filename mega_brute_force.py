import google.generativeai as genai
import itertools

# AIzaSy BUoe OvN4 LCB0 _ vcz7 Wqv4w JhQib yw8 Mkl
# 0-5    6-9  10-13 14-17 18 19-22 23-27 28-32 33-35 36-38

parts = [
    ["AIzaSy"],
    ["BUoe", "BU0e"],
    ["OvN4", "0vN4"],
    ["LCB0", "LCBO"],
    ["_"],
    ["vcz7", "vczT", "vczl"],
    ["Wqv4w", "Wqu4w"],
    ["JhQib"],
    ["yw8", "ywB"],
    ["Mkl", "MkI", "Mk1"]
]

all_combos = list(itertools.product(*parts))
print(f"Testing {len(all_combos)} combinations...")

found = False
for combo in all_combos:
    key = "".join(combo)
    try:
        genai.configure(api_key=key)
        m = genai.GenerativeModel('gemini-1.5-flash')
        m.generate_content("H", generation_config={"max_output_tokens": 1})
        print(f"!!! SUCCESS !!! KEY: {key}")
        found = True
        break
    except Exception as e:
        # print(f"Fail {key}: {e}")
        pass

if not found:
    print("None of the combinations worked.")
