
import csv
import re
import json
import os

# Define file paths
IEEE_S1_PATH = '/Users/ruimar1/rmhome/repos/isep/TPDIMEIA_3/IEEE/s1/ieee_search_string1_result.csv'
IEEE_S2_PATH = '/Users/ruimar1/rmhome/repos/isep/TPDIMEIA_3/IEEE/s2/ieee_search_string2_result.csv'
ACM_S1_PATH = '/Users/ruimar1/rmhome/repos/isep/TPDIMEIA_3/ACM/S1/search.md'
ACM_S2_PATH = '/Users/ruimar1/rmhome/repos/isep/TPDIMEIA_3/ACM/S2/search.md'

OUTPUT_JSON = 'selected_studies.json'
OUTPUT_TEX_TABLE = 'selected_studies_table.tex'

# Keywords for inclusion (Case Insensitive)
# Must have at least one from GROUP A (Agents) AND one from GROUP B (LLMs) AND one from GROUP C (SE/Testing)
GROUP_A = [r'\b(multi[- ]?agent|mas|agentic|autonomous agents?|collaborative agents?)\b']
GROUP_B = [r'\b(llm|large language models?|gpt|generative ai|genai|foundation models?)\b']
GROUP_C = [r'\b(software|test|testing|code|debugging|verification|validation|fuzzing|requirements)\b']

# Keywords for exclusion
EXCLUDE_KEYWORDS = [r'\b(robotics?|medical|healthcare|education|social|traffic|grid|energy|hardware)\b']

def is_relevant(title, abstract, keywords):
    text = f"{title} {abstract} {keywords}".lower()
    
    # Check Exclusion first
    for exc in EXCLUDE_KEYWORDS:
        if re.search(exc, text):
             # Exception: if it also strongly mentions "software engineering" or "code generation", maybe keep it?
             # For now, strict exclusion to filter out "RoboCup" or "Medical Diagnosis" papers unless they explicitly mention SE testing
             if "software" not in text and "code" not in text:
                 return False

    # Check Inclusion
    has_a = any(re.search(k, text) for k in GROUP_A)
    has_b = any(re.search(k, text) for k in GROUP_B)
    has_c = any(re.search(k, text) for k in GROUP_C)

    return has_a and has_b and has_c

def parse_ieee_csv(filepath):
    papers = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                papers.append({
                    'title': row.get('Document Title', '').strip(),
                    'authors': row.get('Authors', '').strip(),
                    'year': row.get('Publication Year', '').strip(),
                    'venue': row.get('Publication Title', '').strip(),
                    'abstract': row.get('Abstract', '').strip(),
                    'keywords': row.get('Author Keywords', '').strip(),
                    'source': 'IEEE',
                    'doi': row.get('DOI', '').strip()
                })
    except Exception as e:
        print(f"Error reading IEEE file {filepath}: {e}")
    return papers

def parse_acm_md(filepath):
    papers = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Simple parser for the markdown table format used in the file
        # Assuming format: Title, Conference, Year, Resume/Summary
        # or | Title | Conference | ... |
        
        # Detect if it's CSV-like or Pipe-table
        # Looking at the file content provided in context, it seems to be CSV-like lines:
        # Title,Conference,Year,Resume / Summary
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('Title'):
                continue
            
            # This is a naive split, might break if commas in title. 
            # Ideally use csv module with strict parsing if format is consistent.
            # Let's try csv.reader on lines
            parts = list(csv.reader([line]))[0]
            if len(parts) >= 3:
                title = parts[0].strip()
                venue = parts[1].strip()
                year = parts[2].strip()
                summary = parts[3].strip() if len(parts) > 3 else ""
                
                # Clean up quotes
                title = title.strip('"')
                summary = summary.strip('"')

                papers.append({
                    'title': title,
                    'authors': "N/A", # ACM file doesn't seem to have authors in the summary snippet provided
                    'year': year,
                    'venue': venue,
                    'abstract': summary, # Using summary as abstract
                    'keywords': "",
                    'source': 'ACM',
                    'doi': ""
                })
    except Exception as e:
        print(f"Error reading ACM file {filepath}: {e}")
    return papers

def main():
    all_papers = []
    
    # Load Data
    all_papers.extend(parse_ieee_csv(IEEE_S1_PATH))
    all_papers.extend(parse_ieee_csv(IEEE_S2_PATH))
    all_papers.extend(parse_acm_md(ACM_S1_PATH))
    all_papers.extend(parse_acm_md(ACM_S2_PATH))

    print(f"Total records processed: {len(all_papers)}")

    # Deduplicate by Title (normalized)
    unique_papers = {}
    for p in all_papers:
        norm_title = re.sub(r'\W+', '', p['title'].lower())
        if norm_title not in unique_papers:
            unique_papers[norm_title] = p
        else:
            # Merge info if needed (e.g. if one source has abstract and other doesn't)
            pass
            
    print(f"Unique records: {len(unique_papers)}")

    # Filter
    selected = []
    for p in unique_papers.values():
        if is_relevant(p['title'], p['abstract'], p['keywords']):
            selected.append(p)

    print(f"Selected relevant papers: {len(selected)}")

    # Save to JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(selected, f, indent=2)

    # Generate TeX Table rows
    # Format: \cite{ref} & Title & Venue & Year & Focus \\
    with open(OUTPUT_TEX_TABLE, 'w', encoding='utf-8') as f:
        f.write(r"% Auto-generated table rows" + "\n")
        for p in selected:
            # Create a mock label or citation key
            # In real scenario, we'd match with bibtex. 
            # Here we just output Title and Venue for the user to copy-paste or we generate lines.
            safe_title = p['title'].replace('&', '\\&').replace('%', '\\%')
            safe_venue = p['venue'].replace('&', '\\&')
            f.write(f"{safe_title} & {safe_venue} & {p['year']} \\\\ \\hline\n")

if __name__ == "__main__":
    main()
