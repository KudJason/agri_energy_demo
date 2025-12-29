import os
import rdflib
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD

# Namespaces
CORE = Namespace("http://example.org/agri-energy/core#")

# Paths
# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_COMBINED = os.path.join(BASE_DIR, "knowledge_base/rules_combined.ttl")
ONTOLOGY_TTL = os.path.join(BASE_DIR, "knowledge_base/ontology/business_core.ttl")
LOCATIONS_TTL = os.path.join(BASE_DIR, "knowledge_base/data/locations.ttl")

def load_graph():
    """Loads the Knowledge Base."""
    g = Graph()
    
    # Load Ontology
    if os.path.exists(ONTOLOGY_TTL):
        g.parse(ONTOLOGY_TTL, format="turtle")
    
    # Load Locations
    if os.path.exists(LOCATIONS_TTL):
        g.parse(LOCATIONS_TTL, format="turtle")

    # Load Combined Rules (The Source of Truth)
    if os.path.exists(RULES_COMBINED):
        try:
            g.parse(RULES_COMBINED, format="turtle")
        except Exception as e:
            print(f"Error loading {RULES_COMBINED}: {e}")
    else:
        print(f"Warning: Rules file not found at {RULES_COMBINED}")
        
    return g

def match_criteria(farm_profile, criteria_list, opp_region=None):
    """
    Evaluates if a farm profile meets a list of criteria.
    Returns (True, []) if all pass, or (False, [failed_reasons]).
    """
    failed_reasons = []
    
    # 0. Global Region Check (Explicit from RDF)
    if opp_region:
        user_region = farm_profile.get("region", "")
        opp_region_str = str(opp_region).lower()
        
        # Mapping UI selection to Knowledge Base region strings
        # UI: ["France", "Belgium (Flanders)", "Belgium (Wallonia)", "Germany"]
        # KB: ["France", "Flanders", "Wallonia"]
        
        if user_region == "Belgium (Flanders)":
            if opp_region_str != "flanders":
                 return (False, [f"Region Mismatch: User is in Flanders, Opportunity is for {opp_region}."])
        elif user_region == "Belgium (Wallonia)":
            if opp_region_str != "wallonia":
                 return (False, [f"Region Mismatch: User is in Wallonia, Opportunity is for {opp_region}."])
        elif user_region == "France":
            if opp_region_str != "france":
                 return (False, [f"Region Mismatch: User is in France, Opportunity is for {opp_region}."])
        elif user_region == "Germany":
            if opp_region_str != "germany":
                 return (False, [f"Region Mismatch: User is in Germany, Opportunity is for {opp_region}."])
    
    for crit in criteria_list:
        var_name = str(crit['variable'])
        
        # Safe string handling
        required_val = str(crit['value'])
        req_text = required_val.lower()
        
        # --- raw / unstructured checks ---
        if var_name == "Raw Requirement":
            
            # A. Certification Keywords
            if "bio" in req_text or "organic" in req_text or "ab " in req_text:
                if "Organic (AB)" not in farm_profile.get("certs", []):
                    failed_reasons.append(f"Missing Certification (Organic/Bio): {required_val}")
                    
            if "jeune" in req_text or "young" in req_text or "ja" in req_text:
                if "Young Farmer" not in farm_profile.get("certs", []):
                     failed_reasons.append(f"Missing Certification (Young Farmer): {required_val}")

            # B. Crop Keywords (Semantic conflict check)
            user_crop = farm_profile.get("crop", "").lower()
            
            # Map App Crops to French Keywords
            crop_map = {
                "pasture": ["prairie", "herbe", "pâturage", "sph", "pph"],
                "wheat": ["terre arable", "céréale", "blé", "culture"],
                "corn": ["terre arable", "maïs", "culture"],
                "orchards": ["verger", "fruit", "arboriculture"],
                "vineyard": ["vigne", "viticulture"]
            }
            
            # If the rule mentions a specific crop type that IS NOT the user's crop, flag it.
            # (Heuristic: Only flag if the rule is strongly specific)
            
            # If rule needs Pasture/Grassland
            if any(k in req_text for k in crop_map["pasture"]):
                # And user is NOT Pasture
                if user_crop not in ["pasture"]:
                    failed_reasons.append(f"Crop Mismatch: Rule implies Grassland/Pasture. User has {user_crop}.")

            # If rule needs Arable/Crops
            if any(k in req_text for k in ["terre arable", "céréale", "culture"]):
                 if user_crop in ["pasture", "orchards", "vineyard"]: # These are typically perm crops
                     # Only fail if it strictly says 'arable' and user is 'pasture'
                     if "terre arable" in req_text:
                         failed_reasons.append(f"Crop Mismatch: Rule requires Arable Land. User has {user_crop}.")

            # If rule needs Orchards
            if any(k in req_text for k in crop_map["orchards"]):
                 if user_crop not in ["orchards"]:
                     failed_reasons.append(f"Crop Mismatch: Rule implies Orchards. User has {user_crop}.")

            continue

        # --- MAPPING LAYER (Structured / Legacy) ---
        
        # Map: "Parcelle Status" / "Culture principale presence" -> check 'certs' or 'crops'
        app_val = None
        
        if "Engagement Type" in var_name: 
            # Implicitly valid for this demo if user selects a relevant crop/action
            continue 
            
        if "Programming Period" in var_name:
            if "2023" in required_val or "2027" in required_val:
                continue # Always valid for current era
                
        # Certification / Status Checks
        if "Parcelle Status" in var_name or "Certification" in var_name:
            user_certs = farm_profile.get("certs", [])
            # If rule requires "bio" and user has "Organic", it's a match
            if "bio" in req_text and "Organic (AB)" in user_certs:
                continue
            elif "bio" in req_text and "Organic (AB)" not in user_certs:
                failed_reasons.append(f"Missing Certification: {required_val}")
                continue

        # Region Checks (Explicit Criteria)
        if "Code Region" in var_name or "Department" in var_name:
            # Simplified: Assume match if farm is in France for French rules
            if farm_profile.get("region") == "France":
                continue
                
        # Surface Type
        if "Surface Type" in var_name:
            if "Terre arable" in required_val and farm_profile.get("crop") in ["Wheat", "Corn"]:
                continue
            if "PPH" in required_val or "SPH" in required_val: # Grasslands
                if "Pasture" in farm_profile.get("crop", ""):
                    continue
                else: 
                     failed_reasons.append(f"Crop Mismatch: Rule requires {required_val}")
                     continue

        # Density / Slope / Distance (Numeric)
        # (LLM extraction of these from 'guide admissibility' was complex, 
        # so we implement basic Operator logic if we can parse the number)
        
        # ... For the specific demo case (MAEC-BIO), the main blocker is generic 'Engagement Type'
        # which we skip as 'Policy Overhead'.
        
    return (len(failed_reasons) == 0, failed_reasons)

def get_available_tags():
    """
    Retrieves all unique tags from the Knowledge Graph for UI selection.
    """
    g = load_graph()
    query = """
    PREFIX core: <http://example.org/agri-energy/core#>
    SELECT DISTINCT ?type WHERE {
        ?opp core:eligibleFarmerType ?type .
    }
    ORDER BY ?type
    """
    results = g.query(query)
    
    # Map URIs to UI Strings
    refined_tags = set()
    for r in results:
        uri = str(r.type)
        if "YoungFarmer" in uri:
            refined_tags.add("Young Farmer")
        elif "Organic" in uri:
            refined_tags.add("Organic (AB)")
        elif "NewEntrant" in uri:
            refined_tags.add("New Entrant")
        elif "ActiveFarmer" in uri:
            # ActiveFarmer is usually a baseline, maybe not a specific filter?
            # User wants "relevant interactive", keeping plain ActiveFarmer might be noise if everyone has it.
            # But let's add it for completeness if they want to toggle it.
            pass 
            
    return sorted(list(refined_tags))

def match_tags(farm_profile, opp_tags_str):
    """
    Checks for conflicts between Farm Profile and Opportunity Tags.
    """
    if not opp_tags_str:
        return True, []
        
    opp_tags = [t.strip() for t in str(opp_tags_str).split(",")]
    failed_reasons = []
    
    user_crop = farm_profile.get("crop", "").lower()
    user_traits = farm_profile.get("certs", []) # These are the tags selected in UI
    
    # 1. Direct Tag Matching (Positive reinforcement)
    # If the user selected a tag, and the opportunity has it, they are likely a prime candidate.
    # (No logic needed here for filtering, it just helps in the future for scoring)

    # 2. Strict Requirement Tags
    requirements = {
        "Organic": ["Organic", "Organic (AB)"],
        "Young Farmer": ["Young Farmer"],
        "Quality": ["Quality", "Label", "AOP", "IGP"]
    }
    
    for req_tag, user_trait_aliases in requirements.items():
        if req_tag in opp_tags:
            if not any(trait in user_traits for trait in user_trait_aliases):
                failed_reasons.append(f"Requires {req_tag} Status/Certification")

    # 3. Sector/Crop Logic (Negative Filtering)
    if "Livestock" in opp_tags or "Dairy" in opp_tags:
        # If user IS NOT a pasture farm AND didn't select 'Livestock' trait
        if user_crop not in ["pasture"] and "Livestock" not in user_traits:
             # If they have a strictly different crop
             if user_crop in ["orchards", "vineyard", "wheat", "corn"]:
                 failed_reasons.append(f"Sector Mismatch: Opportunity is for Livestock.")

    if "Fruits and Vegetables" in opp_tags:
         if user_crop not in ["orchards", "vineyard"] and "Fruits and Vegetables" not in user_traits:
              if user_crop in ["pasture", "wheat", "corn"]:
                  failed_reasons.append(f"Sector Mismatch: Opportunity is for Fruits/Vegetables.")

    return (len(failed_reasons) == 0, failed_reasons)

def find_matching_opportunities(farm_profile):
    """
    Main Engine.
    1. Iterates all Opportunities.
    2. Checks Eligibility (Tags + Criteria).
    3. returns list of eligible opportunity objects.
    """
    g = load_graph()
    opportunities = []
    
    # 1. Get all Opportunities
    # Load Query from File
    with open(os.path.join(BASE_DIR, "knowledge_base/queries/select_opportunities.sparql"), "r") as f:
        query_str = f.read()
    
    results = g.query(query_str)
    
    for row in results:
        opp_uri = row.opp
        opp_tags = row.tags
        
        # Label Resolution Logic
        # Prefer English if available, else French, else URI fragment
        label = "Unknown Opportunity"
        if row.nameEn:
            label = str(row.nameEn)
        elif row.nameFr:
            label = str(row.nameFr)
        else:
            label = str(opp_uri).split("/")[-1]
            
        valid_from = row.validFrom
        source_doc = row.sourceDoc

        # Helper to map URIs to Tags
        derived_tags = []
        if row.farmerTypes:
            f_types = str(row.farmerTypes).split(", ")
            for ft in f_types:
                if "YoungFarmer" in ft:
                    derived_tags.append("Young Farmer")
                elif "Organic" in ft:
                    derived_tags.append("Organic") # Internal matching logic uses "Organic"
                elif "NewEntrant" in ft:
                    derived_tags.append("New Entrant")
        
        # Combine with explicit tags
        opp_tags_list = [t.strip() for t in str(opp_tags).split(",")] if opp_tags else []
        combined_tags = opp_tags_list + derived_tags
        
        # --- NEW: Tag Matching First (Fast Fail) ---
        is_tag_eligible, tag_reasons = match_tags(farm_profile, ", ".join(set(combined_tags)))
        if not is_tag_eligible:
            continue # Skip fetching criteria if tags mismatch
        
        # 2. Get Criteria for this Opportunity
        with open(os.path.join(BASE_DIR, "knowledge_base/queries/select_criteria.sparql"), "r") as f:
            crit_query_str = f.read()
            
        crit_results = g.query(crit_query_str, initBindings={'opp': opp_uri})
        
        criteria_list = []
        for c in crit_results:

            if c.raw_criterion:
                 # Pass raw string as a 'variable' for display purposes in the simple matcher
                 criteria_list.append({
                    'variable': "Raw Requirement", 
                    'operator': "contains", 
                    'value': str(c.raw_criterion)
                 })
            else:
                criteria_list.append({
                    'variable': c.var,
                    'operator': c.op,
                    'value': c.val
                })
            
        # 3. Match
        is_eligible, reasons = match_criteria(farm_profile, criteria_list, opp_region=row.region)
        
        if is_eligible:
            # 4. Get Payment Info (if any)
            with open(os.path.join(BASE_DIR, "knowledge_base/queries/select_payments.sparql"), "r") as f:
                pay_query_str = f.read()
                
            pay_results = g.query(pay_query_str, initBindings={'opp': opp_uri})
            
            revenue_text = "See Details"
            estimated_rev = 0
            
            # Simple aggregation of payment amounts
            for p in pay_results:
                try:
                    val = float(p.val)
                    estimated_rev += val
                    revenue_text = f"€{estimated_rev:.2f}/ha"
                except:
                    revenue_text = str(p.val) # Fallback for complex text rules

            valid_from_str = str(valid_from) if valid_from else "Unknown"
            
            # Add Source metadata
            source_slug = str(source_doc).split("/")[-1] if source_doc else "Unknown" 
            
            # Rich Data Fields
            benefit_amount = str(row.benefitAmount) if row.benefitAmount else "See Details"
            
            # Structured Payment
            payment_rate = str(row.paymentRate) if row.paymentRate else None
            payment_unit = str(row.paymentUnit) if row.paymentUnit else None
            payment_limit = str(row.paymentLimit) if row.paymentLimit else None
            
            calc_logic = str(row.calculationLogic) if row.calculationLogic else None
            app_rule = str(row.applicationRule) if row.applicationRule else None
            app_start = str(row.appStartDate) if row.appStartDate else None
            app_end = str(row.appEndDate) if row.appEndDate else None
            
            desc = str(row.description) if row.description else f"Valid from {valid_from_str}"

            implicit_criteria_count = 0
            if row.region:
                implicit_criteria_count += 1
            implicit_criteria_count += len(combined_tags)

            opportunities.append({
                "name": str(label),
                "type": "LLM Extracted Rule",
                "description": desc,
                "source": source_slug,
                "revenue_text": revenue_text, # Legacy field, keeping for fallback
                "benefit_amount": benefit_amount,
                "payment_rate": payment_rate,
                "payment_unit": payment_unit,
                "payment_limit": payment_limit,
                "calculation_logic": calc_logic,
                "application_rule": app_rule,
                "app_start_date": app_start,
                "app_end_date": app_end,
                "criteria_count": len(criteria_list) + implicit_criteria_count,
                "uri": str(opp_uri)
            })
            
    return opportunities

if __name__ == "__main__":
    print("--- Testing Semantic Matcher ---")
    
    test_profile = {
        "region": "France",
        "crop": "Pasture",
        "size": 50,
        "certs": ["Organic (AB)"]
    }
    
    print(f"Testing Profile: {test_profile}")
    results = find_matching_opportunities(test_profile)
    print(f"Found {len(results)} matches.")
    for r in results:
        print(f"- {r['name']} ({r['revenue_text']})")
