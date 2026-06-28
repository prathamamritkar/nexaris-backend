import unittest
from nlp_engine import VernacularParser, nlp

class TestVernacularParser(unittest.TestCase):
    def setUp(self):
        self.parser = VernacularParser()

    def test_empty_input(self):
        """Test edge case 1: empty, null, or whitespace-only transcript"""
        cases = ["", "   ", None]
        for case in cases:
            res = self.parser.extract_entities(case)
            self.assertEqual(res["item"], "UNKNOWN_RESOURCE")
            self.assertEqual(res["urgency"], "UNKNOWN")
            self.assertEqual(res["location_context"], "UNKNOWN_LOCATION")

    def test_urgency_extraction_priorities(self):
        """Test edge case 2: highest priority urgency is extracted"""
        # "fatal" is CRITICAL, "need" is HIGH
        # CRITICAL should win
        res1 = self.parser.extract_entities("fatal need")
        self.assertEqual(res1["urgency"], "CRITICAL")

        res2 = self.parser.extract_entities("Need this low priority")
        self.assertEqual(res2["urgency"], "HIGH") # "need" is HIGH, "low" is LOW, HIGH wins

        res3 = self.parser.extract_entities("moderate priority whenever")
        self.assertEqual(res3["urgency"], "MEDIUM")

        # Unknown urgency
        res4 = self.parser.extract_entities("some random text")
        self.assertEqual(res4["urgency"], "UNKNOWN")

    def test_item_extraction_longest_match(self):
        """Test edge case 3: longest match item is extracted"""
        # "blood" (5) vs "blood pack" (10). Blood Pack should win
        res1 = self.parser.extract_entities("We need a blood pack right now")
        self.assertEqual(res1["item"], "Blood Pack")

        # Test just blood
        res2 = self.parser.extract_entities("He is bleeding, need blood")
        self.assertEqual(res2["item"], "Blood Pack")

        # Test Indic words
        res3 = self.parser.extract_entities("dawai chahiye")
        self.assertEqual(res3["item"], "Medicines")

        # Another test for oxygen
        res4 = self.parser.extract_entities("oxygen cylinder is required")
        self.assertEqual(res4["item"], "Oxygen Cylinder")

    def test_location_extraction(self):
        """Test edge case 4: location extraction for English and Indic patterns"""
        # English preposition
        res1 = self.parser.extract_entities("accident near St Jude hospital")
        self.assertEqual(res1["location_context"], "St Jude Hospital") # gets titled

        res2 = self.parser.extract_entities("We are at Main Street")
        self.assertEqual(res2["location_context"], "Main Street")

        # Indic postposition
        res3 = self.parser.extract_entities("Dadar-East ke paas accident")
        self.assertEqual(res3["location_context"], "Dadar-East")

        res4 = self.parser.extract_entities("Bandra station mein phasa hua hai")
        self.assertEqual(res4["location_context"], "Bandra Station")

        # Fallback / no location
        res5 = self.parser.extract_entities("Need help")
        self.assertEqual(res5["location_context"], "Unknown")

        # Too short location
        res6 = self.parser.extract_entities("at x")
        self.assertEqual(res6["location_context"], "Unknown")

    def test_full_transcript(self):
        """Test full extraction of all entities"""
        transcript = "Emergency we need insulin immediately near Bandra station"
        res = self.parser.extract_entities(transcript)

        self.assertEqual(res["urgency"], "CRITICAL")
        self.assertEqual(res["item"], "Insulin")
        self.assertEqual(res["location_context"], "Bandra Station")

if __name__ == "__main__":
    unittest.main()
