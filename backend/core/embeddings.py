"""
Service for generating embeddings using Google Gemini API instead of OpenAI.
The user provided a Google API key in OPENAI_API_KEY env.
"""
import os
import logging
from typing import List, Union
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        # The user put a gemini key in the OPENAI_API_KEY slot, we read it
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "models/gemini-embedding-001" # Use gemini embedding
        
        if not self.api_key:
            logger.warning("API_KEY is not set. Embeddings will fail.")
            self.client = None
        else:
            genai.configure(api_key=self.api_key)
            self.client = True

    def get_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for a single text string."""
        if not self.client:
            raise ValueError("API key not configured")
            
        try:
            text = text.replace("\n", " ")
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_document"
            )
            
            # Gemini embeddings are 768 dimensions by default. Neo4j is configured for 1536.
            # We must pad it or reconfigure Neo4j. It's safer to pad it to 1536
            # so we don't need to rebuild the Neo4j index schema.
            emb = result['embedding']
            if len(emb) < 1536:
                emb.extend([0.0] * (1536 - len(emb)))
            elif len(emb) > 1536:
                emb = emb[:1536]
            return emb
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise e

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate vectors for multiple text strings."""
        if not self.client:
            raise ValueError("API key not configured")
            
        try:
            cleaned_texts = [t.replace("\n", " ") for t in texts]
            result = genai.embed_content(
                model=self.model,
                content=cleaned_texts,
                task_type="retrieval_document"
            )
            embs = result['embedding']
            final_embs = []
            for emb in embs:
                if len(emb) < 1536:
                    emb.extend([0.0] * (1536 - len(emb)))
                elif len(emb) > 1536:
                    emb = emb[:1536]
                final_embs.append(emb)
            return final_embs
        except Exception as e:
            logger.error(f"Error generating embeddings batch: {e}")
            raise e

_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
