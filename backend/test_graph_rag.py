import os, sys
import logging
logging.basicConfig(level=logging.DEBUG)

sys.path.append(r'e:\doan2_chatboxtuyensinh_DoMinhSang\backend')
from core.graph_rag import get_graph_rag_engine

try:
    engine = get_graph_rag_engine()
    res = engine.process_query('điểm chuẩn ngành công nghệ thông tin', 'test1')
    print("Result:", res)
except Exception as e:
    print("Exception!!", e)
    import traceback
    traceback.print_exc()
