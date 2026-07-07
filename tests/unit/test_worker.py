import pytest
from unittest.mock import patch, MagicMock
from neo4j import exceptions as neo4j_exceptions

import worker

@pytest.fixture(autouse=True)
def reset_driver():
    """Reset the global driver before and after each test."""
    worker.driver = None
    yield
    worker.driver = None

@patch('worker.GraphDatabase.driver')
@patch('worker.time.sleep')
def test_get_db_driver_retry_logic(mock_sleep, mock_driver):
    """Test that get_db_driver retries connection upon ServiceUnavailable."""

    # Configure the mock to raise ServiceUnavailable twice, then return a valid driver
    mock_valid_driver = MagicMock()
    mock_driver.side_effect = [
        neo4j_exceptions.ServiceUnavailable("DB down"),
        neo4j_exceptions.ServiceUnavailable("DB down still"),
        mock_valid_driver
    ]

    driver = worker.get_db_driver()

    # Should be the valid driver we returned on the 3rd try
    assert driver is mock_valid_driver

    # driver() should have been called 3 times
    assert mock_driver.call_count == 3

    # sleep should have been called 2 times
    assert mock_sleep.call_count == 2

@patch('worker.GraphDatabase.driver')
@patch('worker.time.sleep')
def test_get_db_driver_retry_failure(mock_sleep, mock_driver):
    """Test that get_db_driver raises RuntimeError after exhausting retries."""

    mock_driver.side_effect = neo4j_exceptions.ServiceUnavailable("DB down")

    with pytest.raises(RuntimeError) as exc_info:
        worker.get_db_driver()

    assert str(exc_info.value) == "Failed to connect to Neo4j after all retries"
    assert mock_driver.call_count == worker.MAX_RETRIES
    assert mock_sleep.call_count == worker.MAX_RETRIES - 1

@patch('worker.GraphDatabase.driver')
def test_get_db_driver_auth_error(mock_driver):
    """Test that AuthError is raised immediately without retries."""

    mock_driver.side_effect = neo4j_exceptions.AuthError("Bad credentials")

    with pytest.raises(neo4j_exceptions.AuthError):
        worker.get_db_driver()

    # Auth errors should not be retried
    assert mock_driver.call_count == 1

@patch('worker.GraphDatabase.driver')
@patch('worker.time.sleep')
def test_get_db_driver_general_exception(mock_sleep, mock_driver):
    """Test that get_db_driver catches general exceptions and retries."""

    mock_valid_driver = MagicMock()
    mock_driver.side_effect = [
        Exception("Unknown error"),
        mock_valid_driver
    ]

    driver = worker.get_db_driver()

    assert driver is mock_valid_driver
    assert mock_driver.call_count == 2
    assert mock_sleep.call_count == 1

def test_get_db_driver_already_initialized():
    """Test that get_db_driver returns the existing driver if already initialized."""

    mock_driver = MagicMock()
    worker.driver = mock_driver

    with patch('worker.GraphDatabase.driver') as mock_graph_driver:
        driver = worker.get_db_driver()

        assert driver is mock_driver
        mock_graph_driver.assert_not_called()
