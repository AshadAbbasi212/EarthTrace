"""Unit tests for ModelManager."""
import pytest
from geolocator.models.model_manager import ModelManager


def test_model_manager_registration_and_lifecycle():
    manager = ModelManager()

    class FakeModel:
        def __init__(self):
            self.loaded = True

    manager.register_loader("fake", lambda: FakeModel())

    # Load model
    m1 = manager.load("fake")
    assert isinstance(m1, FakeModel)
    assert manager.current_model_name == "fake"

    # Context manager acquire
    with manager.acquire("fake") as m2:
        assert isinstance(m2, FakeModel)

    # After exiting context without keep_loaded, it should be unloaded
    assert manager.current_model is None
    assert manager.current_model_name is None


def test_model_manager_vram_info():
    manager = ModelManager()
    info = manager.get_vram_info()
    assert "allocated_mb" in info
    assert "total_mb" in info
    assert "free_mb" in info
