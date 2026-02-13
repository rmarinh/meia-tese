
import json
import re

JSON_PATH = 'selected_studies.json'
BIB_PATH = 'template/Dissertacao_rm/mainbibliography.bib'
TABLE_PATH = 'new_studies_table.tex'

def generate_key(p):
    # AuthorYearTitleFirstWord
    # Authors format "Last, First; Last, First" or "A. Author"
    # Take first author's last name
    first_author = p['authors'].split(';')[0]
    # Remove initials if present "A. Ahammad" -> "Ahammad"
    if ',' in first_author:
        lastname = first_author.split(',')[0].strip()
    else:
        parts = first_author.strip().split()
        lastname = parts[-1] if parts else "Anonymous"
    
    # Title first word
    title_word = re.sub(r'\W+', '', p['title'].split()[0])
    
    key = f"{lastname}{p['year']}{title_word}".lower()
    return key

def main():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        papers = json.load(f)

    bib_entries = []
    table_rows = []

    print(f"Processing {len(papers)} papers...")

    for p in papers:
        key = generate_key(p)
        
        # BibTeX
        # Using @inproceedings for most, or @article if venue looks like journal?
        # Let's default to @inproceedings for conferences
        entry_type = "inproceedings"
        if "Journal" in p.get('source', '') or "Transactions" in p.get('venue', ''):
             entry_type = "article"

        bib = f"@{entry_type}{{{key},\n"
        bib += f"  author = {{{p['authors'].replace(';', ' and')}}},\n"
        bib += f"  title = {{{p['title']}}},\n"
        if entry_type == 'article':
            bib += f"  journal = {{{p['venue']}}},\n"
        else:
             bib += f"  booktitle = {{{p['venue']}}},\n"
        bib += f"  year = {{{p['year']}}},\n"
        bib += f"  abstract = {{{p['abstract'][:500] + '...' if len(p['abstract'])>500 else p['abstract']}}}\n"
        bib += "}\n"
        bib_entries.append(bib)

        # Table Row
        # \cite{key} & Title & Year \\
        # Truncate title for table
        short_title = (p['title'][:50] + '...') if len(p['title']) > 50 else p['title']
        short_title = short_title.replace('&', '\\&').replace('%', '\\%')
        venue = p['venue'].split('(')[-1].strip(')') if '(' in p['venue'] else p['venue'][:10]
        # Using a tabular format: Ref & Title & Venue & Year
        row = f"\\cite{{{key}}} & {short_title} & {venue} & {p['year']} \\\\ \\hline"
        table_rows.append(row)

    # Append to Bib file
    with open(BIB_PATH, 'a', encoding='utf-8') as f:
        f.write("\n% --- New SLR Entries ---\n")
        for bib in bib_entries:
            f.write(bib + "\n")
    
    # Write Table to file
    with open('template/Dissertacao_rm/ch2/assets/selected_studies_table.tex', 'w', encoding='utf-8') as f:
        f.write("% Generated Table Content\n")
        f.write("\\begin{table}[ht]\n")
        f.write("\\centering\n")
        f.write("\\caption{Selected Studies for MAS in Software Testing}\n")
        f.write("\\label{tab:selected_studies_new}\n")
        f.write("\\resizebox{\\textwidth}{!}{\n")
        f.write("\\begin{tabular}{|l|p{6cm}|l|l|l|}\n")
        f.write("\\hline\n")
        f.write("Ref & Title & Year & Source & RQs \\\\ \\hline\n")
        
        for p in papers:
            key = generate_key(p)
            
            # Infer RQs
            text = (p['title'] + " " + p['abstract']).lower()
            rqs = []
            if any(k in text for k in ['architecture', 'orchestra', 'collaboration', 'role', 'multi-agent', 'workflow']):
                rqs.append("RQ1")
            if any(k in text for k in ['rag', 'retrieval', 'knowledge', 'context', 'tool', 'api']):
                rqs.append("RQ2")
            if any(k in text for k in ['benchmark', 'evaluate', 'metric', 'coverage', 'pass@', 'comparison', 'empirical']):
                rqs.append("RQ3")
            
            rq_str = ", ".join(rqs) if rqs else "RQ1"

            # Truncate title
            short_title = (p['title'][:40] + '...') if len(p['title']) > 40 else p['title']
            short_title = short_title.replace('&', '\\&').replace('%', '\\%').replace('_', '\\_')
            
            # Source
            source = p.get('source', 'N/A')

            row = f"\\cite{{{key}}} & {short_title} & {p['year']} & {source} & {rq_str} \\\\ \\hline"
            f.write(row + "\n")

        f.write("\\end{tabular}\n")
        f.write("}\n")
        f.write("\\end{table}\n")

if __name__ == "__main__":
    main()
