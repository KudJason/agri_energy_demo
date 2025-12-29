
import sys
import os

# Add parent directory to path to find utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.match_opportunities import load_graph, find_matching_opportunities

def test_loading():
    print("Loading graph...")
    g = load_graph()
    print(f"Graph loaded with {len(g)} triples.")
    
    # Check if we have Opportunities
    query = """
    PREFIX core: <http://example.org/agri-energy/core#>
    SELECT (COUNT(?s) AS ?count) WHERE {
        ?s a core:Opportunity .
    }
    """
    res = g.query(query)
    for row in res:
        print(f"Found {row['count']} Opportunities.")
        
    print("Test Complete.")

if __name__ == "__main__":
    test_loading()
