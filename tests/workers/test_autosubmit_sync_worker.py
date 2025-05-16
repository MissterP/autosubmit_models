"""
Tests for Autosubmit Sync Worker.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.workers.workers.autosubmit_sync_worker import AutosubmitSyncWorker


@pytest.fixture
def mock_experiments():
    """Fixture for mock experiment data."""
    return [
        MagicMock(
            exp_id="exp1",
            name="test_experiment_1",
            model="EC-Earth",
            credated=datetime(2023, 1, 1),
            branch="main",
            hpc="marenostrum",
        ),
        MagicMock(
            exp_id="exp2",
            name="test_experiment_2",
            model="EC-Earth/",  # Con barra al final para probar la limpieza
            credated=datetime(2023, 1, 2),
            branch="main",
            hpc="marenostrum",
        ),
        MagicMock(
            exp_id="exp3",
            name="test_experiment_3",
            model="'CMCC-ESM2'",  # Con comillas para probar la limpieza
            credated=datetime(2023, 1, 3),
            branch="develop",
            hpc="marenostrum",
        ),
    ]


@pytest.fixture
def worker():
    """Fixture for autosubmit sync worker instance."""
    return AutosubmitSyncWorker()


@patch("src.workers.workers.autosubmit_sync_worker.get_autosubmit_db_session")
def test_extract_autosubmit_experiments(mock_db_session, worker, mock_experiments):
    """Test extracting experiments from Autosubmit database."""
    # Mock session and query result
    mock_session = MagicMock()
    mock_db_session.return_value.__enter__.return_value = mock_session

    mock_result = MagicMock()
    mock_session.execute.return_value = mock_result
    mock_result.scalars.return_value.all.return_value = mock_experiments.copy()

    # Execute function
    result = worker._extract_autosubmit_experiments()

    # Assertions
    assert len(result) == 3
    mock_session.execute.assert_called_once()

    # Verify model names are cleaned
    assert result[0].model == "EC-Earth"
    assert result[1].model == "EC-Earth"  # Trailing slash removed
    assert result[2].model == "CMCC-ESM2"  # Quotes removed


def test_clean_model_name(worker):
    """Test cleaning of model names."""
    assert worker._clean_model_name("EC-Earth/") == "EC-Earth"
    assert worker._clean_model_name("'CMCC-ESM2'") == "CMCC-ESM2"
    assert worker._clean_model_name("EC-Earth///") == "EC-Earth"
    assert worker._clean_model_name("'EC-Earth'") == "EC-Earth"
    assert worker._clean_model_name("EC-Earth") == "EC-Earth"


def test_process_experiments(worker, mock_experiments):
    """Test processing experiments into model data."""
    # Execute function
    result = worker._process_experiments(mock_experiments)

    # Assertions
    assert len(result) == 2  # Two unique models (after cleaning)
    assert "EC-Earth" in result
    assert "CMCC-ESM2" in result
    assert result["EC-Earth"]["count"] == 2
    assert result["CMCC-ESM2"]["count"] == 1
    assert len(result["EC-Earth"]["experiments"]) == 2
    assert len(result["CMCC-ESM2"]["experiments"]) == 1

    # Check that correct experiment fields are being used
    assert result["EC-Earth"]["experiments"][0]["id"] == "exp1"
    assert result["EC-Earth"]["experiments"][0]["name"] == "test_experiment_1"
    assert result["EC-Earth"]["experiments"][0]["created_time"] == datetime(2023, 1, 1)


@patch("src.workers.workers.autosubmit_sync_worker.get_db_session")
def test_update_timescaledb(mock_db_session, worker):
    """Test updating TimescaleDB with processed data."""
    # Mock data
    models_data = {
        "EC-Earth": {
            "model": "EC-Earth",
            "count": 2,
            "experiments": [
                {
                    "id": "exp1",
                    "name": "test_experiment_1",
                    "created_time": datetime(2023, 1, 1),
                },
                {
                    "id": "exp2",
                    "name": "test_experiment_2",
                    "created_time": datetime(2023, 1, 2),
                },
            ],
        }
    }
    current_time = datetime(2023, 1, 5)

    # Mock session
    mock_session = MagicMock()
    mock_db_session.return_value.__enter__.return_value = mock_session

    # No experiments exist in the database
    mock_session.exec.return_value.first.return_value = None

    # Execute function
    worker._update_timescaledb(models_data, current_time)

    # Assertions
    mock_session.add.assert_called()
    assert mock_session.add.call_count == 3  # 1 model + 2 experiments
    mock_session.commit.assert_called_once()
