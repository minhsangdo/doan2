"""
Neo4j client for connecting and querying the graph database.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class Neo4jClient:
    """Client for Neo4j graph database operations."""

    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self._driver = None

    @property
    def driver(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
        return self._driver

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

    def verify_connectivity(self) -> bool:
        """Test the connection to Neo4j."""
        try:
            self.driver.verify_connectivity()
            logger.info("Neo4j connection verified successfully.")
            return True
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            return False

    def run_query(self, query: str, parameters: dict = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results."""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def run_write_query(self, query: str, parameters: dict = None) -> Any:
        """Execute a write Cypher query."""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            summary = result.consume()
            return summary

    # === Knowledge Graph CRUD ===

    def create_nganh(self, nganh: dict) -> None:
        """Create or update a Nganh (major) node."""
        query = """
        MERGE (n:Nganh {ma_nganh: $ma_nganh})
        SET n.ten = $ten,
            n.nhom = $nhom,
            n.mo_ta = $mo_ta,
            n.stt = $stt
        """
        self.run_write_query(query, nganh)

    def create_diem_chuan(self, dc: dict) -> None:
        """Create or update DiemChuan node and link to Nganh."""
        query = """
        MERGE (d:DiemChuan {ma_nganh: $ma_nganh, nam: $nam})
        SET d.diem_thpt = $diem_thpt,
            d.diem_hocba = $diem_hocba,
            d.diem_dgnl = $diem_dgnl,
            d.diem_vsat = $diem_vsat,
            d.ten = $ten
        WITH d
        MATCH (n:Nganh {ma_nganh: $ma_nganh})
        MERGE (n)-[:HAS_SCORE]->(d)
        """
        self.run_write_query(query, dc)

    def create_tohop_mon(self, tohop: dict) -> None:
        """Create or update TohopMon (subject combination) node."""
        query = """
        MERGE (t:TohopMon {ma_tohop: $ma_tohop})
        SET t.ten = $ten,
            t.cac_mon = $cac_mon
        """
        self.run_write_query(query, {
            "ma_tohop": tohop["ma_tohop"],
            "ten": tohop["ten"],
            "cac_mon": json.dumps(tohop.get("cac_mon", []), ensure_ascii=False)
        })

    def create_phuong_thuc(self, pt: dict) -> None:
        """Create or update PhuongThuc (admission method) node."""
        query = """
        MERGE (p:PhuongThuc {ma_pt: $ma_pt})
        SET p.ten = $ten,
            p.mo_ta = $mo_ta
        """
        self.run_write_query(query, pt)

    def create_nhom_nganh(self, nhom: str) -> None:
        """Create or update NhomNganh (major group) node."""
        query = """
        MERGE (ng:NhomNganh {ten: $ten})
        """
        self.run_write_query(query, {"ten": nhom})

    def create_hoc_bong(self, hb: dict) -> None:
        """Create or update HocBong (scholarship) node."""
        query = """
        MERGE (h:HocBong {ma_hb: $ma_hb})
        SET h.ten = $ten,
            h.mo_ta = $mo_ta,
            h.dieu_kien = $dieu_kien,
            h.gia_tri = $gia_tri,
            h.doi_tuong = $doi_tuong
        """
        self.run_write_query(query, {
            "ma_hb": hb["ma_hb"],
            "ten": hb.get("ten", ""),
            "mo_ta": hb.get("mo_ta", ""),
            "dieu_kien": hb.get("dieu_kien", ""),
            "gia_tri": hb.get("gia_tri", ""),
            "doi_tuong": hb.get("doi_tuong", ""),
        })

    def get_all_hoc_bong(self) -> List[Dict]:
        """Get all HocBong nodes for context."""
        query = """
        MATCH (h:HocBong)
        RETURN h.ma_hb AS ma_hb,
               h.ten AS ten,
               h.mo_ta AS mo_ta,
               h.dieu_kien AS dieu_kien,
               h.gia_tri AS gia_tri,
               h.doi_tuong AS doi_tuong
        ORDER BY h.ma_hb
        """
        return self.run_query(query)

    def link_nganh_tohop(self, ma_nganh: str, ma_tohop: str) -> None:
        """Create USES_COMBO relationship between Nganh and TohopMon."""
        query = """
        MATCH (n:Nganh {ma_nganh: $ma_nganh})
        MATCH (t:TohopMon {ma_tohop: $ma_tohop})
        MERGE (n)-[:USES_COMBO]->(t)
        """
        self.run_write_query(query, {"ma_nganh": ma_nganh, "ma_tohop": ma_tohop})

    def link_nganh_nhom(self, ma_nganh: str, nhom: str) -> None:
        """Create BELONGS_TO relationship between Nganh and NhomNganh."""
        query = """
        MATCH (n:Nganh {ma_nganh: $ma_nganh})
        MATCH (ng:NhomNganh {ten: $nhom})
        MERGE (n)-[:BELONGS_TO]->(ng)
        """
        self.run_write_query(query, {"ma_nganh": ma_nganh, "nhom": nhom})

    def link_nganh_phuong_thuc(self, ma_nganh: str, ma_pt: str) -> None:
        """Create ACCEPTS_METHOD relationship."""
        query = """
        MATCH (n:Nganh {ma_nganh: $ma_nganh})
        MATCH (p:PhuongThuc {ma_pt: $ma_pt})
        MERGE (n)-[:ACCEPTS_METHOD]->(p)
        """
        self.run_write_query(query, {"ma_nganh": ma_nganh, "ma_pt": ma_pt})

    # === Vector Search ===

    def update_node_embedding(self, ma_nganh: str, embedding: List[float]) -> None:
        """Update the embedding vector for a Nganh node."""
        query = """
        MATCH (n:Nganh {ma_nganh: $ma_nganh})
        SET n.embedding = $embedding
        """
        self.run_write_query(query, {"ma_nganh": ma_nganh, "embedding": embedding})

    def create_vector_index(self) -> None:
        """Create vector index for similarity search."""
        query = """
        CREATE VECTOR INDEX entity_embedding IF NOT EXISTS
        FOR (n:Nganh) ON (n.embedding)
        OPTIONS {indexConfig: {
            `vector.dimensions`: 1536,
            `vector.similarity_function`: 'cosine'
        }}
        """
        try:
            self.run_write_query(query)
            logger.info("Vector index created successfully.")
        except Exception as e:
            logger.warning(f"Vector index may already exist: {e}")

    def vector_search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """Perform vector similarity search on Nganh nodes."""
        query = """
        CALL db.index.vector.queryNodes('entity_embedding', $top_k, $embedding)
        YIELD node, score
        RETURN node.ma_nganh AS ma_nganh, 
               node.ten AS ten, 
               node.nhom AS nhom,
               node.mo_ta AS mo_ta,
               score
        ORDER BY score DESC
        """
        return self.run_query(query, {"embedding": query_embedding, "top_k": top_k})

    def get_nganh_context(self, ma_nganh: str) -> Dict:
        """Get full context for a Nganh including relationships (1-2 hop)."""
        query = """
        MATCH (n:Nganh {ma_nganh: $ma_nganh})
        OPTIONAL MATCH (n)-[:HAS_SCORE]->(d:DiemChuan)
        OPTIONAL MATCH (n)-[:USES_COMBO]->(t:TohopMon)
        OPTIONAL MATCH (n)-[:BELONGS_TO]->(ng:NhomNganh)
        OPTIONAL MATCH (n)-[:ACCEPTS_METHOD]->(p:PhuongThuc)
        RETURN n.ma_nganh AS ma_nganh,
               n.ten AS ten_nganh,
               n.nhom AS nhom,
               n.mo_ta AS mo_ta,
               d.diem_thpt AS diem_thpt,
               d.diem_hocba AS diem_hocba,
               d.diem_dgnl AS diem_dgnl,
               d.diem_vsat AS diem_vsat,
               d.nam AS nam,
               collect(DISTINCT t.ma_tohop) AS tohop_mon,
               collect(DISTINCT t.ten) AS ten_tohop,
               ng.ten AS nhom_nganh,
               collect(DISTINCT p.ten) AS phuong_thuc
        """
        results = self.run_query(query, {"ma_nganh": ma_nganh})
        return results[0] if results else {}

    def get_related_nganh(self, ma_nganh: str) -> List[Dict]:
        """Get ngành cùng nhóm (related majors in same group)."""
        query = """
        MATCH (n:Nganh {ma_nganh: $ma_nganh})-[:BELONGS_TO]->(ng:NhomNganh)
        MATCH (related:Nganh)-[:BELONGS_TO]->(ng)
        WHERE related.ma_nganh <> $ma_nganh
        OPTIONAL MATCH (related)-[:HAS_SCORE]->(d:DiemChuan)
        RETURN related.ma_nganh AS ma_nganh,
               related.ten AS ten,
               d.diem_thpt AS diem_thpt
        ORDER BY d.diem_thpt DESC
        LIMIT 5
        """
        return self.run_query(query, {"ma_nganh": ma_nganh})

    # === Query Helpers ===

    def search_nganh_by_profile(self, diem: float, tohop: str = None) -> List[Dict]:
        """Search Nganh matching user profile (score and optionally block)."""
        params = {"diem": diem}
        
        query = """
        MATCH (n:Nganh)-[:HAS_SCORE]->(d:DiemChuan)
        WHERE d.diem_thpt <= $diem AND d.diem_thpt > 0
        """
        
        if tohop:
            query += "MATCH (n)-[:USES_COMBO]->(t:TohopMon) WHERE toLower(t.ma_tohop) = toLower($tohop)\n"
            params["tohop"] = tohop

        query += """
        RETURN n.ma_nganh AS ma_nganh,
               n.ten AS ten,
               d.diem_thpt AS diem_thpt,
               n.mo_ta AS mo_ta
        ORDER BY d.diem_thpt DESC
        LIMIT 5
        """
        return self.run_query(query, params)

    def search_nganh_by_name(self, keyword: str) -> List[Dict]:
        """Search Nganh by name keyword (full text)."""
        query = """
        MATCH (n:Nganh)
        WHERE toLower(n.ten) CONTAINS toLower($keyword)
        OPTIONAL MATCH (n)-[:HAS_SCORE]->(d:DiemChuan)
        RETURN n.ma_nganh AS ma_nganh,
               n.ten AS ten,
               n.nhom AS nhom,
               d.diem_thpt AS diem_thpt,
               d.diem_hocba AS diem_hocba,
               d.diem_dgnl AS diem_dgnl,
               d.diem_vsat AS diem_vsat
        ORDER BY n.ten
        """
        return self.run_query(query, {"keyword": keyword})

    def get_all_nganh(self) -> List[Dict]:
        """Get all majors with scores."""
        query = """
        MATCH (n:Nganh)
        OPTIONAL MATCH (n)-[:HAS_SCORE]->(d:DiemChuan)
        OPTIONAL MATCH (n)-[:USES_COMBO]->(t:TohopMon)
        RETURN n.ma_nganh AS ma_nganh,
               n.ten AS ten,
               n.nhom AS nhom,
               n.mo_ta AS mo_ta,
               d.diem_thpt AS diem_thpt,
               d.diem_hocba AS diem_hocba,
               d.diem_dgnl AS diem_dgnl,
               d.diem_vsat AS diem_vsat,
               collect(DISTINCT t.ma_tohop) AS tohop_mon,
               coalesce(n.search_count, 0) as search_count
        ORDER BY n.stt
        """
        return self.run_query(query)

    def increment_search_count(self, ma_nganh_list: List[str]) -> None:
        """Increment search counter for analytical stats."""
        if not ma_nganh_list:
            return
        query = """
        UNWIND $ma_nganh_list as ma_nganh
        MATCH (n:Nganh {ma_nganh: ma_nganh})
        SET n.search_count = coalesce(n.search_count, 0) + 1
        """
        self.run_write_query(query, {"ma_nganh_list": ma_nganh_list})

    def get_popular_majors(self) -> List[Dict]:
        """Get top majors by search queries for admin dashboard."""
        query = """
        MATCH (n:Nganh)
        WHERE n.search_count IS NOT NULL AND n.search_count > 0
        RETURN n.ma_nganh AS ma_nganh, n.ten AS ten, n.search_count AS count
        ORDER BY count DESC LIMIT 10
        """
        return self.run_query(query)

    def update_nganh_and_score(self, data: dict) -> None:
        """Update major and its score directly from Admin panel."""
        query = """
        MATCH (n:Nganh {ma_nganh: $ma_nganh})
        SET n.ten = $ten, n.nhom = $nhom, n.mo_ta = $mo_ta
        WITH n
        OPTIONAL MATCH (n)-[:HAS_SCORE]->(d:DiemChuan)
        SET d.diem_thpt = $diem_thpt,
            d.diem_hocba = $diem_hocba
        RETURN n
        """
        self.run_write_query(query, data)

    def get_diem_chuan_by_nganh(self, ma_nganh: str) -> Optional[Dict]:
        """Get score thresholds for a specific major."""
        query = """
        MATCH (n:Nganh {ma_nganh: $ma_nganh})-[:HAS_SCORE]->(d:DiemChuan)
        RETURN n.ten AS ten_nganh,
               n.ma_nganh AS ma_nganh,
               d.diem_thpt AS diem_thpt,
               d.diem_hocba AS diem_hocba,
               d.diem_dgnl AS diem_dgnl,
               d.diem_vsat AS diem_vsat,
               d.nam AS nam
        """
        results = self.run_query(query, {"ma_nganh": ma_nganh})
        return results[0] if results else None

    def get_nganh_by_nhom(self, nhom: str) -> List[Dict]:
        """Get all majors in a group."""
        query = """
        MATCH (ng:NhomNganh {ten: $nhom})<-[:BELONGS_TO]-(n:Nganh)
        OPTIONAL MATCH (n)-[:HAS_SCORE]->(d:DiemChuan)
        RETURN n.ma_nganh AS ma_nganh,
               n.ten AS ten,
               d.diem_thpt AS diem_thpt,
               d.diem_hocba AS diem_hocba
        ORDER BY d.diem_thpt DESC
        """
        return self.run_query(query, {"nhom": nhom})

    def get_nganh_by_tohop(self, ma_tohop: str) -> List[Dict]:
        """Get all majors that accept a specific subject combination."""
        query = """
        MATCH (t:TohopMon {ma_tohop: $ma_tohop})<-[:USES_COMBO]-(n:Nganh)
        OPTIONAL MATCH (n)-[:HAS_SCORE]->(d:DiemChuan)
        RETURN n.ma_nganh AS ma_nganh,
               n.ten AS ten,
               n.nhom AS nhom,
               d.diem_thpt AS diem_thpt,
               d.diem_hocba AS diem_hocba
        ORDER BY d.diem_thpt DESC
        """
        return self.run_query(query, {"ma_tohop": ma_tohop})

    def get_kg_stats(self) -> Dict:
        """Get Knowledge Graph statistics."""
        stats = {}
        # Node counts
        node_query = """
        CALL db.labels() YIELD label
        CALL apoc.cypher.run('MATCH (n:`' + label + '`) RETURN count(n) as count', {})
        YIELD value
        RETURN label, value.count as count
        """
        try:
            results = self.run_query(node_query)
            stats["node_counts"] = {r["label"]: r["count"] for r in results}
        except Exception:
            # Fallback without APOC
            for label in ["Nganh", "DiemChuan", "TohopMon", "PhuongThuc", "NhomNganh", "HocBong"]:
                try:
                    q = f"MATCH (n:{label}) RETURN count(n) as count"
                    r = self.run_query(q)
                    stats.setdefault("node_counts", {})[label] = r[0]["count"] if r else 0
                except Exception:
                    pass

        # Relationship counts
        for rel_type in ["HAS_SCORE", "USES_COMBO", "BELONGS_TO", "ACCEPTS_METHOD"]:
            try:
                q = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
                r = self.run_query(q)
                stats.setdefault("relationship_counts", {})[rel_type] = r[0]["count"] if r else 0
            except Exception:
                pass

        stats["total_nodes"] = sum(stats.get("node_counts", {}).values())
        stats["total_relationships"] = sum(stats.get("relationship_counts", {}).values())
        return stats

    def clear_all(self) -> None:
        """Delete all nodes and relationships (use with caution!)."""
        self.run_write_query("MATCH (n) DETACH DELETE n")
        logger.warning("All data cleared from Neo4j!")

    def create_constraints(self) -> None:
        """Create uniqueness constraints for node labels."""
        constraints = [
            "CREATE CONSTRAINT nganh_unique IF NOT EXISTS FOR (n:Nganh) REQUIRE n.ma_nganh IS UNIQUE",
            "CREATE CONSTRAINT diemchuan_unique IF NOT EXISTS FOR (d:DiemChuan) REQUIRE (d.ma_nganh, d.nam) IS UNIQUE",
            "CREATE CONSTRAINT tohopmon_unique IF NOT EXISTS FOR (t:TohopMon) REQUIRE t.ma_tohop IS UNIQUE",
            "CREATE CONSTRAINT phuongthuc_unique IF NOT EXISTS FOR (p:PhuongThuc) REQUIRE p.ma_pt IS UNIQUE",
            "CREATE CONSTRAINT nhomnganh_unique IF NOT EXISTS FOR (ng:NhomNganh) REQUIRE ng.ten IS UNIQUE",
            "CREATE CONSTRAINT hocbong_unique IF NOT EXISTS FOR (h:HocBong) REQUIRE h.ma_hb IS UNIQUE",
        ]
        for c in constraints:
            try:
                self.run_write_query(c)
            except Exception as e:
                logger.warning(f"Constraint may already exist: {e}")


# Singleton instance
_client = None


def get_neo4j_client() -> Neo4jClient:
    global _client
    if _client is None:
        _client = Neo4jClient()
    return _client
