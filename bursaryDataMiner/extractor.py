# bursaryDataMiner/extractor.py
import re
def extract_requirements(text: str) -> dict:
    d = {}
    m = re.search(r'(\d{2})\s*%.*(average|aggregate)', text, re.I)
    if m: d["min_average"] = int(m.group(1))
    if re.search(r'\bSouth African citizen\b', text, re.I):
        d["citizenship"] = "ZA"
    # add field-of-study keyword bags etc.
    return d
