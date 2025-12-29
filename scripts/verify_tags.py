import sys
import os

# Add custom path to imports
sys.path.append(os.path.abspath("utils"))

try:
    from match_opportunities import find_matching_opportunities
except ImportError:
    sys.path.append(os.path.abspath("../utils"))
    from match_opportunities import find_matching_opportunities

print("--- Testing Tag Filtering Logic ---")

# Case 1: With Young Farmer Tag
profile_with_tag = {
    "region": "Belgium (Flanders)",
    "crop": "Wheat",
    "size": 50,
    "certs": ["Young Farmer"]
}

results_with = find_matching_opportunities(profile_with_tag)
yf_opps_with = [r for r in results_with if "Young Farmer" in r['name'] or "young farmers" in r['name'].lower()]
print(f"Profile WITH Tag: Found {len(results_with)} total, {len(yf_opps_with)} Young Farmer opps.")

# Case 2: Without Young Farmer Tag
profile_without_tag = {
    "region": "Belgium (Flanders)",
    "crop": "Wheat",
    "size": 50,
    "certs": []
}

results_without = find_matching_opportunities(profile_without_tag)
yf_opps_without = [r for r in results_without if "Young Farmer" in r['name'] or "young farmers" in r['name'].lower()]
print(f"Profile WITHOUT Tag: Found {len(results_without)} total, {len(yf_opps_without)} Young Farmer opps.")

if len(yf_opps_with) > 0 and len(yf_opps_without) == 0:
    print("SUCCESS: Tag filtering is working strictly!")
elif len(yf_opps_without) > 0:
    print("FAILURE: Young Farmer opps found despite missing tag.")
    for r in yf_opps_without:
        print(f" - Leaked Opp: {r['name']}")
else:
    print("WARNING: No Young Farmer opps found at all. Check data.")
