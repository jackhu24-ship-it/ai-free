import pytest
from src.security.ppm_vault import PPMVault

def test_ppm_vault_initialization():
    vault = PPMVault()
    assert "ML-KEM-1024" in vault.pqc_algorithms
    assert "Falcon-1024" in vault.pqc_algorithms
    assert "LMS/HSS" in vault.pqc_algorithms
    assert vault.gas_reduction_factor == 0.40

def test_generate_pq_starks_signature():
    vault = PPMVault()
    tx_data = "tx_sample_payload_quantum_verification"
    result = vault.generate_pq_starks_signature(tx_data)
    
    assert isinstance(result, dict)
    assert "signature" in result
    assert isinstance(result["signature"], str)
    assert len(result["signature"]) == 64  # sha256 hexdigest length
    assert result["algorithms_used"] == vault.pqc_algorithms
    assert result["is_quantum_secure"] is True
    assert "generation_time_ms" in result
    assert result["generation_time_ms"] > 0

def test_estimate_gas_cost():
    vault = PPMVault()
    base_gas = 100000
    reduced = vault.estimate_gas_cost(base_gas)
    # 40% reduction target -> 100000 * 0.6 = 60000
    assert reduced == 60000

def test_estimate_gas_cost_zero():
    vault = PPMVault()
    assert vault.estimate_gas_cost(0) == 0
