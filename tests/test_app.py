import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import sys
from pathlib import Path

# Add the parent directory to sys.path so we can import app.py
sys.path.insert(0, str(Path(__file__).parent.parent))

import app

class TestApp(unittest.TestCase):

    @patch('app.st')
    def test_get_browser_language_valid_complex_header(self, mock_st):
        # Mock st.context.headers.get to return 'hi-IN,hi;q=0.9,en-US;q=0.8'
        mock_context = MagicMock()
        mock_headers = {'Accept-Language': 'hi-IN,hi;q=0.9,en-US;q=0.8'}
        mock_context.headers = mock_headers
        mock_st.context = mock_context

        result = app.get_browser_language()
        self.assertEqual(result, 'hi')

    @patch('app.st')
    def test_get_browser_language_simple_header(self, mock_st):
        # Mock st.context.headers.get to return 'mr'
        mock_context = MagicMock()
        mock_headers = {'Accept-Language': 'mr'}
        mock_context.headers = mock_headers
        mock_st.context = mock_context

        result = app.get_browser_language()
        self.assertEqual(result, 'mr')

    @patch('app.st')
    def test_get_browser_language_no_header_key(self, mock_st):
        # Mock st.context.headers where 'Accept-Language' is not present, should use dict get default 'en'
        mock_context = MagicMock()
        mock_context.headers = {}
        mock_st.context = mock_context

        result = app.get_browser_language()
        self.assertEqual(result, 'en')

    @patch('app.st')
    def test_get_browser_language_no_headers_attr(self, mock_st):
        # Mock st.context without headers attribute
        mock_context = MagicMock()
        del mock_context.headers
        mock_st.context = mock_context

        result = app.get_browser_language()
        self.assertEqual(result, 'en')

    @patch('app.st')
    def test_get_browser_language_no_context_attr(self, mock_st):
        # Mock st without context attribute
        del mock_st.context

        result = app.get_browser_language()
        self.assertEqual(result, 'en')

    @patch('app.st')
    def test_get_browser_language_exception(self, mock_st):
        # Mock an exception when accessing headers by using a PropertyMock
        mock_context = MagicMock()
        type(mock_context).headers = PropertyMock(side_effect=Exception("Test Exception"))
        mock_st.context = mock_context

        result = app.get_browser_language()
        self.assertEqual(result, 'en')

if __name__ == '__main__':
    unittest.main()
