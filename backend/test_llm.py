import os, sys
import logging

logging.basicConfig(level=logging.DEBUG)
sys.path.append(r'e:\doan2_chatboxtuyensinh_DoMinhSang\backend')
from core.llm_client import get_llm_client

try:
    client = get_llm_client()
    ans, suggestions = client.generate_response('Test question?', 'Test context')
    print("Answer:", ans)
    print("Suggestions:", suggestions)
except Exception as e:
    print("Exception occurred:", type(e), e)
