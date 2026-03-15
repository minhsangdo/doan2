import sys
import os
import argparse
import logging
from dotenv import load_dotenv

# Ensure the backend directory is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from knowledge.graph_builder import GraphBuilder

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Seed DNC Neo4j Graph from JSON.")
    parser.add_argument(
        "--data-dir", 
        type=str, 
        default=os.path.join(os.path.dirname(__file__), "..", "data", "processed"),
        help="Path to the directory containing JSON files."
    )
    args = parser.parse_args()
    
    data_dir = os.path.abspath(args.data_dir)
    logging.info(f"Using data directory: {data_dir}")
    
    builder = GraphBuilder(data_dir=data_dir)
    builder.rebuild_all()

if __name__ == "__main__":
    main()
