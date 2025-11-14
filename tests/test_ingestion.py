import pytest
from src.geocoding import geocode_with_here, geocode_with_google

def test_geocode_with_here_success():
    address = "123 Rue de la Paix, 75001 Paris, France"
    result = geocode_with_here(address)
    
    assert result["status"] == "OK"
    assert result["latitude"] is not None
    assert result["longitude"] is not None
    assert result["precision_level"] in ["ROOFTOP", "RANGE_INTERPOLATED"]

def test_geocode_with_here_invalid_address():
    address = "INVALID_ADDRESS_XYZ_123"
    result = geocode_with_here(address)
    
    assert result["status"] == "ZERO_RESULTS"
    assert result["latitude"] is None

def test_geocode_with_google_timeout():
    # Simuler un timeout
    import time
    address = "123 Test St"
    
    with pytest.raises(TimeoutError):
        geocode_with_google(address, timeout=0.001)


