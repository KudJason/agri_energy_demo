import sys
import os

# Add custom path to imports
sys.path.append(os.path.abspath("utils"))

try:
    from match_opportunities import find_matching_opportunities
except ImportError:
    # Try alternate path if running from different CWD
    sys.path.append(os.path.abspath("../utils"))
    from match_opportunities import find_matching_opportunities

# Test Profile: Flanders
profile = {
    "region": "Belgium (Flanders)",
    "crop": "Wheat",
    "size": 50,
    "certs": ["Young Farmer"]
}

print(f"Testing Profile: {profile}")
results = find_matching_opportunities(profile)
print(f"Found {len(results)} matches.")

for r in results:
    print(f"- {r['name']} (Source: {r['source']})")
    # Check if any French rules snuck in
    if "transparence_gaec" in r['source'] or "france" in r['uri'].lower():
        print("ERROR: French rule found in Flanders results!")

print("\nVerification Complete.")
