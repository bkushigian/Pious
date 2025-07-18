import pytest
import os
from pious.pio.database import CFRDatabase
from pious.pio.resources import get_test_database, get_database_root


def test_database_initialization():
    db: CFRDatabase = get_test_database()
    assert len(db) == 8


def test_database_isomorphic_retrieval():
    db: CFRDatabase = get_test_database()
    assert db["2h2c2d"] == os.path.join(get_database_root(), "2c2s2d.cfr")
    assert db["2s2c2d"] == os.path.join(get_database_root(), "2c2s2d.cfr")
    assert db["2s2h2d"] == os.path.join(get_database_root(), "2c2s2d.cfr")
    assert db["2s2h2c"] == os.path.join(get_database_root(), "2c2s2d.cfr")
    assert db["2h2s2c"] == os.path.join(get_database_root(), "2c2s2d.cfr")

    assert db["As9s6h"] == os.path.join(get_database_root(), "As9s6h.cfr")
    assert db["As9s6c"] == os.path.join(get_database_root(), "As9s6h.cfr")
    assert db["Ah9h6c"] == os.path.join(get_database_root(), "As9s6h.cfr")

    assert db["Qh8h2d"] == os.path.join(get_database_root(), "Qs8s2h.cfr")
    assert db["Qs8s2h"] == os.path.join(get_database_root(), "Qs8s2h.cfr")
    assert db["Qs8s2h"] == os.path.join(get_database_root(), "Qs8s2h.cfr")

    # Test on board that is out of order (this should be fixed to work later!)
    with pytest.raises(KeyError):
        db["2d8hQh"]

    # Test that non-existent boards raise KeyError
    with pytest.raises(KeyError):
        db["Qs8h2d"]

    with pytest.raises(KeyError):
        db["As9h2d"]

    with pytest.raises(KeyError):
        db["As9s2s"]
