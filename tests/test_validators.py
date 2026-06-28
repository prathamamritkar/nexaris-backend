import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validators import validate_citizen_id, ValidationError

class TestValidators(unittest.TestCase):
    def test_validate_citizen_id_valid(self):
        """Test valid citizen IDs"""
        self.assertEqual(validate_citizen_id("citizen_123"), "citizen_123")
        self.assertEqual(validate_citizen_id("CITIZEN-456"), "CITIZEN-456")
        self.assertEqual(validate_citizen_id("12345"), "12345")

    def test_validate_citizen_id_empty(self):
        """Test empty citizen ID raises ValidationError"""
        with self.assertRaises(ValidationError):
            validate_citizen_id("")

    def test_validate_citizen_id_too_short(self):
        """Test citizen ID too short raises ValidationError"""
        with self.assertRaises(ValidationError):
            validate_citizen_id("ab")

    def test_validate_citizen_id_too_long(self):
        """Test citizen ID too long raises ValidationError"""
        long_id = "a" * 65
        with self.assertRaises(ValidationError):
            validate_citizen_id(long_id)

    def test_validate_citizen_id_invalid_chars(self):
        """Test citizen ID with invalid chars raises ValidationError"""
        with self.assertRaises(ValidationError):
            validate_citizen_id("citizen@123")
        with self.assertRaises(ValidationError):
            validate_citizen_id("citizen 123")

    def test_validate_citizen_id_not_string(self):
        """Test non-string citizen ID raises ValidationError"""
        with self.assertRaises(ValidationError):
            validate_citizen_id(12345)
        with self.assertRaises(ValidationError):
            validate_citizen_id(None)

if __name__ == '__main__':
    unittest.main()
