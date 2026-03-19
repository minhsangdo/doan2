"""
Knowledge Graph Builder script that reads parsed JSON and drives Neo4j Creation.
"""
import os
import sys
import json
import logging
import time

# Update Python Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.neo4j_client import get_neo4j_client
from core.embeddings import get_embedding_service

logger = logging.getLogger(__name__)

class GraphBuilder:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.db = get_neo4j_client()
        self.embedder = get_embedding_service()
        
    def rebuild_all(self):
        """Clean slate, create schema and ingest all facts."""
        logger.info("Starting Graph Build Process...")
        
        # 1. Clear Data & Set Constraints
        logger.info("Clearing old data and creating constraints...")
        self.db.clear_all()
        self.db.create_constraints()
        self.db.create_vector_index()
        
        # 2. Read JSONs
        try:
            with open(os.path.join(self.data_dir, "phuong_thuc.json"), "r", encoding="utf-8") as f:
                phuong_thuc = json.load(f)
            with open(os.path.join(self.data_dir, "tohop_mon.json"), "r", encoding="utf-8") as f:
                tohop_mon = json.load(f)
            with open(os.path.join(self.data_dir, "nganh_hoc.json"), "r", encoding="utf-8") as f:
                nganh_hoc = json.load(f)
            with open(os.path.join(self.data_dir, "diem_chuan.json"), "r", encoding="utf-8") as f:
                diem_chuan = json.load(f)
            hoc_bong_path = os.path.join(self.data_dir, "hoc_bong.json")
            hoc_bong = json.load(open(hoc_bong_path, "r", encoding="utf-8")) if os.path.exists(hoc_bong_path) else []
        except Exception as e:
            logger.error(f"Error reading JSON datasets: {e}")
            raise e

        # 3. Create PhuongThuc nodes
        logger.info(f"Creating {len(phuong_thuc)} PhuongThuc nodes...")
        for pt in phuong_thuc:
            self.db.create_phuong_thuc(pt)

        # 4. Create TohopMon nodes
        logger.info(f"Creating {len(tohop_mon)} Tổ hợp môn nodes...")
        for t in tohop_mon:
            self.db.create_tohop_mon(t)

        # 4b. Create HocBong (scholarship) nodes
        if hoc_bong:
            logger.info(f"Creating {len(hoc_bong)} HocBong nodes...")
            for hb in hoc_bong:
                self.db.create_hoc_bong(hb)
            
        # 5. Create NhomNganh Nodes
        groups = set([ng.get("nhom") for ng in nganh_hoc if ng.get("nhom")])
        logger.info(f"Creating {len(groups)} Nhóm ngành nodes...")
        for group in groups:
            self.db.create_nhom_nganh(group)

        # 6. Build Majors and Link 
        logger.info(f"Creating {len(nganh_hoc)} Majors, relationships, and embeddings...")
        
        # Link diem_chuan reference
        dc_map = {d["ma_nganh"]: d for d in diem_chuan}
        
        for idx, nganh in enumerate(nganh_hoc):
            # Create node
            self.db.create_nganh({
                "ma_nganh": nganh["ma_nganh"],
                "ten": nganh["ten"],
                "nhom": nganh["nhom"],
                "mo_ta": nganh.get("mo_ta", ""),
                "stt": nganh.get("stt", 0)
            })
            
            # Link Group
            self.db.link_nganh_nhom(nganh["ma_nganh"], nganh["nhom"])
            
            # Link TohopMon
            for th in nganh.get("tohop_mon", []):
                self.db.link_nganh_tohop(nganh["ma_nganh"], th)
                
            # Score Node (DiemChuan)
            if nganh["ma_nganh"] in dc_map:
                dc = dc_map[nganh["ma_nganh"]]
                dc["ten"] = f"Điểm chuẩn {nganh['ten']} 2025"
                self.db.create_diem_chuan(dc)
                
            # Embeddings (rate limiting safe via batching or delays)
            # DNC Major info is around 50 vectors, we can do it row by row
            try:
                # Text used for querying includes Name, combos, and code
                text_to_embed = f"Ngành {nganh['ten']} ({nganh['ma_nganh']}). Nhóm: {nganh['nhom']}. Xét tuyển khối: {','.join(nganh.get('tohop_mon', []))}."
                vec = self.embedder.get_embedding(text_to_embed)
                self.db.update_node_embedding(nganh["ma_nganh"], vec)
                time.sleep(0.1) # Small delay to respect rate limits
            except Exception as e:
                logger.warning(f"Failed embedding for {nganh['ten']}: {e}")
                
            if (idx + 1) % 10 == 0:
                logger.info(f"Progress: {idx+1}/{len(nganh_hoc)} majors created.")
                
        # Link All Phuong Thuc to all Majors
        # Assuming DNC allows the 9 methods for all majors
        logger.info("Linking 9 admission methods to all majors...")
        for nganh in nganh_hoc:
            for pt in phuong_thuc:
                self.db.link_nganh_phuong_thuc(nganh["ma_nganh"], pt["ma_pt"])

        logger.info("Knowledge Graph seeded successfully!")
        
        # Print Stats
        stats = self.db.get_kg_stats()
        logger.info(f"Final Graph Stats: {json.dumps(stats, indent=2, ensure_ascii=False)}")
