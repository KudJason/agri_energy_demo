import os

def consolidate_region(region):
    source_dir = f"/Users/jasonjia/Documents/industry_policy/agri_energy_demo/data/markdown/belgium/{region}/extra"
    output_file = f"/Users/jasonjia/Documents/industry_policy/agri_energy_demo/data/markdown/belgium/{region}/all_extra_measures.md"
    
    if not os.path.exists(source_dir):
        print(f"Directory not found: {source_dir}")
        return

    markdown_files = sorted([f for f in os.listdir(source_dir) if f.endswith(".md")])
    
    with open(output_file, "w", encoding="utf-8") as outfile:
        outfile.write(f"# All Extra Measures - {region.capitalize()}\n\n")
        outfile.write(f"This file contains a consolidation of {len(markdown_files)} policy measures.\n\n")
        outfile.write("---\n\n")
        
        for filename in markdown_files:
            filepath = os.path.join(source_dir, filename)
            with open(filepath, "r", encoding="utf-8") as infile:
                content = infile.read()
                
            outfile.write(f"## File: {filename}\n\n")
            outfile.write(content)
            outfile.write("\n\n---\n\n")
            
    print(f"Consolidated {len(markdown_files)} files into {output_file}")

consolidate_region("flanders")
consolidate_region("wallonia")
