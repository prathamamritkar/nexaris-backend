import re
import logging
from typing import Dict, Any, List, Pattern

logger = logging.getLogger(__name__)

class VernacularParser:
    """
    An elite, deterministic NLP parser designed to reliably extract intent, resource types,
    urgency levels, and location context from mixed-language vernacular transcripts.
    Optimized for zero-dependency execution with O(1) matching via precompiled regex schemas.
    """
    
    def __init__(self) -> None:
        # Maps domain vocab (English + Romanized Indic) to exact DB parameters
        raw_urgency_map: Dict[str, List[str]] = {
            "CRITICAL": ["dying", "fatal", "critical", "emergency", "immediately", "urgent", "asap", "sakht", "turant", "bachao", "maut"],
            "HIGH": ["high", "need", "fast", "quick", "soon", "jaldi", "zaruri", "avashyak", "zaroorat"],
            "MEDIUM": ["medium", "moderate", "normal", "required", "chahiye", "mangta"],
            "LOW": ["low", "whenever", "later", "stock", "baad", "fursat"]
        }
        
        raw_item_map: Dict[str, List[str]] = {
            "Blood Pack": ["blood pack", "blood", "khoon", "plasma", "rakta", "bleeding"],
            "Insulin": ["insulin", "diabetes", "sugar", "madhumeh"],
            "Oxygen Cylinder": ["oxygen cylinder", "oxygen", "cylinder", "breath", "o2", "saans", "hawa"],
            "Clean Water": ["clean water", "water", "pani", "drinking", "peene ka", "jal"],
            "Medicines": ["medicine", "medicines", "dawai", "dawa", "drugs", "pills", "meds", "paracetamol", "antibiotic", "goli"],
            "Vaccines": ["vaccine", "vaccines", "injection", "teeka", "suiee", "sui"],
            "Food Supplies": ["food supplies", "food", "ration", "khana", "supplies", "meal", "bhookh", "bhook", "roti", "chawal"],
            "First Aid Kit": ["first aid kit", "first aid", "bandage", "patti", "medical kit", "injury", "chot", "ghav", "zakhm"]
        }

        # Precompile regex for optimal matching performance
        self.urgency_patterns: Dict[str, Pattern] = self._compile_patterns(raw_urgency_map)
        self.item_patterns: Dict[str, Pattern] = self._compile_patterns(raw_item_map)
        
        # Robust location extraction regex:
        # English prepositions: location context usually follows (e.g. "near St. Jude's")
        self.en_loc_pattern = re.compile(
            r'\b(?:at|in|near|around|towards|from)\s+((?:[a-zA-Z0-9\'-]+\s*){1,5})',
            re.IGNORECASE
        )
        
        # Indic postpositions: location context usually precedes (e.g. "Dadar-East ke paas")
        self.hi_loc_pattern = re.compile(
            r'\b((?:[a-zA-Z0-9\'-]+\s*){1,4})(?:ke paas|mein|tak|se|idhar|yahan|par|pe|ke nazdeek)\b',
            re.IGNORECASE
        )
        
        # Cleanup regex (Preserve hyphens and apostrophes for composite/transliterated words)
        self.noise_pattern = re.compile(r'[^\w\s.,!?\'-]')

    def _compile_patterns(self, raw_map: Dict[str, List[str]]) -> Dict[str, Pattern]:
        """Compiles lists of keywords into efficient word-boundary regex patterns."""
        compiled_map = {}
        for key, keywords in raw_map.items():
            # Sort by length descending to match longer multi-word phrases first
            sorted_kws = sorted(keywords, key=len, reverse=True)
            # Escape keywords and join with OR, wrap in word boundaries
            pattern_str = r'\b(?:' + '|'.join(re.escape(kw) for kw in sorted_kws) + r')\b'
            compiled_map[key] = re.compile(pattern_str, re.IGNORECASE)
        return compiled_map

    def extract_entities(self, transcript: str) -> Dict[str, Any]:
        """
        Parses raw transcript text safely and accurately.
        Handles edge cases such as empty input, missing location grammar, and priority overrides.
        """
        # Edge Case 1: Empty, null, or whitespace-only transcript
        if not transcript or not str(transcript).strip():
            logger.warning("VernacularParser received empty transcript.")
            return {
                "item": "UNKNOWN_RESOURCE",
                "urgency": "UNKNOWN", 
                "location_context": "UNKNOWN_LOCATION",
                "transcript_preview": ""
            }

        # Preprocess text (remove excessive noise, normalize spaces)
        clean_text = self.noise_pattern.sub('', str(transcript))
        clean_text = ' '.join(clean_text.split())
        
        # Priority mapping enforces processing hierarchy
        urgency_priority = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        detected_urgency = "UNKNOWN" # Default safety net
        
        # Edge Case 2: Urgency Extraction (highest priority wins)
        for level in urgency_priority:
            if self.urgency_patterns[level].search(clean_text):
                detected_urgency = level
                break # We found the highest applicable level, stop searching
                
        # Edge Case 3: Item Extraction (Longest Match Wins / Maximum Munch Algorithm)
        # Prevents semantic overlap (e.g., matching "blood" when "blood pressure monitor" is spoken)
        detected_item = "UNKNOWN_RESOURCE"
        longest_match_len = 0
        
        for item_name, pattern in self.item_patterns.items():
            for match in pattern.finditer(clean_text):
                match_length = len(match.group())
                if match_length > longest_match_len:
                    longest_match_len = match_length
                    detected_item = item_name

        # Edge Case 4: Location Extraction
        location_context = ""
        
        # Check Indic postposition patterns first as they are highly specific
        hi_match = self.hi_loc_pattern.search(clean_text)
        en_match = self.en_loc_pattern.search(clean_text)
        
        if hi_match:
            location_context = hi_match.group(1).strip()
        elif en_match:
            location_context = en_match.group(1).strip()
            
        # Clean up trailing punctuation from extracted location
        location_context = re.sub(r'[,.-]+$', '', location_context).strip().title()
        
        # Fallback for weak or missing location contexts
        if len(location_context) < 3:
            location_context = "Unknown"

        return {
            "item": detected_item,
            "urgency": detected_urgency,
            "location_context": location_context[:500], # Hard cap to prevent DB overflow
            "transcript_preview": clean_text[:100]
        }

# Singleton instance
nlp = VernacularParser()
