import re

class VernacularParser:
    def __init__(self):
        # Maps domain vocab (English + Romanized Indic) to exact DB parameters
        self.urgency_map = {
            "CRITICAL": ["dying", "fatal", "critical", "emergency", "immediately", "urgent", "asap", "sakh", "turant"],
            "HIGH": ["high", "need", "fast", "quick", "soon", "jaldi", "zaruri"],
            "MEDIUM": ["medium", "moderate", "normal", "required", "chahiye"],
            "LOW": ["low", "whenever", "later", "stock", "baad"]
        }
        
        self.item_map = {
            "Blood Pack": ["blood", "blood pack", "khoon", "plasma"],
            "Insulin": ["insulin", "diabetes", "sugar"],
            "Oxygen Cylinder": ["oxygen", "cylinder", "breath", "o2", "saans"],
            "Clean Water": ["water", "pani", "drinking", "clean water"],
            "Medicines": ["medicine", "dawai", "drugs", "pills", "meds", "paracetamol"],
            "Vaccines": ["vaccine", "injection", "teeka"],
            "Food Supplies": ["food", "ration", "khana", "supplies", "meal", "bhookh"],
            "First Aid Kit": ["first aid", "bandage", "patti", "medical kit", "injury"]
        }

    def extract_entities(self, transcript: str) -> dict:
        transcript_lower = transcript.lower()
        
        # 1. Edge Case: Empty Transcript
        if not transcript_lower.strip():
            return {"item": "Medicines", "urgency": "HIGH", "location_context": "Unknown (Empty Audio)"}
            
        # 2. Extract Urgency (Default to HIGH to ensure safety in civic infrastructure)
        detected_urgency = "HIGH" 
        for urgency_level, keywords in self.urgency_map.items():
            if any(kw in transcript_lower for kw in keywords):
                detected_urgency = urgency_level
                if detected_urgency == "CRITICAL": break # Highest priority overrides everything
                
        # 3. Extract Resource Item (Default to general Medicines)
        detected_item = "Medicines"
        for item_name, keywords in self.item_map.items():
            if any(kw in transcript_lower for kw in keywords):
                detected_item = item_name
                break
                
        # 4. Extract Location Context (Edge Case Handling)
        # Looks for prepositional phrases indicating location (at, near, in, paas, mein)
        location_match = re.search(r'\b(at|in|near|around|towards|paas|mein)\s+([a-zA-Z0-9\s,]+)', transcript_lower)
        
        if location_match:
            # Clean up the regex match, capitalize properly
            location_context = location_match.group(2)[:500].strip().title()
        else:
            # Fallback Edge Case: If no location grammar is found, pass the entire 
            # transcript so human admins don't lose the context.
            location_context = transcript[:500].strip()
            
        return {
            "item": detected_item,
            "urgency": detected_urgency,
            "location_context": location_context,
            "transcript_preview": transcript[:100]
        }

# Singleton instance
nlp = VernacularParser()
