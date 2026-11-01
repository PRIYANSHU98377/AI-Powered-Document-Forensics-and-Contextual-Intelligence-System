import re
from typing import Tuple, Dict, Any
from rapidfuzz import fuzz
import jellyfish

class MatchResult:
    EXACT_MATCH = "EXACT_MATCH"
    TOLERATED_VARIATION = "TOLERATED_VARIATION"
    CONFLICT = "CONFLICT"

def match_names(name1: str, name2: str) -> Tuple[str, float, str]:
    """
    Evaluates applicant name consistency across documents:
    - Exact match: identical casefolded strings.
    - Tolerated variation: initials/middle name abbreviation (Rahul K. Sharma vs Rahul Kumar Sharma),
      minor typographic/phonetic similarity (Jellyfish Metaphone).
    - True conflict: different individuals (Rahul Sharma vs Vikram Sharma).
    Returns (status, similarity_score, explanation).
    """
    if not name1 or not name2:
        return MatchResult.CONFLICT, 0.0, "Missing name string"
        
    n1 = " ".join(name1.lower().replace(".", " ").split())
    n2 = " ".join(name2.lower().replace(".", " ").split())
    
    if n1 == n2:
        return MatchResult.EXACT_MATCH, 1.0, f"Exact match ('{name1}' == '{name2}')"
        
    t1 = n1.split()
    t2 = n2.split()
    
    # Check initials variation: e.g. ["rahul", "k", "sharma"] vs ["rahul", "kumar", "sharma"]
    if len(t1) == len(t2) and len(t1) >= 2:
        if t1[0] == t2[0] and t1[-1] == t2[-1]:
            # First and last names match exactly
            # Check middle name initial
            middle_matches = True
            for i in range(1, len(t1) - 1):
                m1, m2 = t1[i], t2[i]
                if not (m1 == m2 or (len(m1) == 1 and m2.startswith(m1)) or (len(m2) == 1 and m1.startswith(m2))):
                    middle_matches = False
                    break
            if middle_matches:
                return MatchResult.TOLERATED_VARIATION, 0.95, f"Tolerated middle-name abbreviation/initial ('{name1}' vs '{name2}')"

    # Phonetic matching using Metaphone
    meta1 = " ".join([jellyfish.metaphone(tok) for tok in t1])
    meta2 = " ".join([jellyfish.metaphone(tok) for tok in t2])
    if meta1 == meta2:
        return MatchResult.TOLERATED_VARIATION, 0.92, f"Phonetic equivalence under Metaphone analysis ('{name1}' ~ '{name2}')"
        
    ratio = fuzz.token_sort_ratio(n1, n2) / 100.0
    if ratio >= 0.85:
        return MatchResult.TOLERATED_VARIATION, ratio, f"High lexical similarity ({ratio*100:.1f}%) within tolerated transcription threshold"
        
    return MatchResult.CONFLICT, ratio, f"Substantial name conflict: '{name1}' vs '{name2}' ({ratio*100:.1f}% similarity)"

def match_dob(dob1: str, dob2: str) -> Tuple[str, float, str]:
    """
    Strict date matching for Date of Birth.
    """
    if not dob1 or not dob2:
        return MatchResult.CONFLICT, 0.0, "Missing DOB value"
        
    d1 = dob1.strip()
    d2 = dob2.strip()
    
    if d1 == d2:
        return MatchResult.EXACT_MATCH, 1.0, f"Identical DOB: {d1}"
    else:
        return MatchResult.CONFLICT, 0.0, f"Conflicting DOB values: '{d1}' vs '{d2}'"

def match_address(addr1: str, addr2: str) -> Tuple[str, float, str]:
    """
    Address matching using token-based fuzzy similarity.
    Tolerates minor variations in abbreviations ('Rd' vs 'Road', 'Flr' vs 'Floor').
    """
    if not addr1 or not addr2:
        return MatchResult.CONFLICT, 0.0, "Missing address"
        
    # Clean and normalize common abbreviations
    def clean_addr(a):
        s = a.lower()
        s = re.sub(r"\broad\b", "rd", s)
        s = re.sub(r"\bstreet\b", "st", s)
        s = re.sub(r"\bapartment\b|\bapt\b", "flat", s)
        return " ".join(s.replace(",", " ").replace("-", " ").split())
        
    c1 = clean_addr(addr1)
    c2 = clean_addr(addr2)
    
    # Exact match
    if c1 == c2:
        return MatchResult.EXACT_MATCH, 1.0, "Exact residential address match"
        
    # Extract pin/postal codes if present (e.g. 560103 vs 560066)
    pin1 = re.findall(r"\b\d{6}\b", c1)
    pin2 = re.findall(r"\b\d{6}\b", c2)
    if pin1 and pin2 and pin1[0] != pin2[0]:
        return MatchResult.CONFLICT, 0.30, f"Conflicting postal PIN codes ({pin1[0]} vs {pin2[0]})"
        
    ratio = fuzz.token_sort_ratio(c1, c2) / 100.0
    if ratio >= 0.80:
        return MatchResult.TOLERATED_VARIATION, ratio, f"Tolerated address variation ({ratio*100:.1f}% lexical overlap)"
    else:
        return MatchResult.CONFLICT, ratio, f"Address geographical discrepancy ({ratio*100:.1f}% similarity)"

def match_ids(id1: str, id2: str) -> Tuple[str, float, str]:
    """
    Match ID or Account numbers (alphanumeric clean).
    """
    c1 = re.sub(r"[^A-Za-z0-9]", "", str(id1).upper())
    c2 = re.sub(r"[^A-Za-z0-9]", "", str(id2).upper())
    
    if c1 == c2:
        return MatchResult.EXACT_MATCH, 1.0, f"Exact identifier match ({c1})"
    else:
        return MatchResult.CONFLICT, 0.0, f"Conflicting identifiers ({c1} vs {c2})"
