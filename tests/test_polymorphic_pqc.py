import hashlib
import os

from src.crypto.polymorphic_pqc import (
    EncapsulationResult,
    KeyPair,
    PolymorphicPQCMatrix,
    PqcScheme,
    SignatureResult,
)


def test_pqc_scheme_enum():
    assert PqcScheme.ML_KEM_1024.value == "ML-KEM-1024"
    assert PqcScheme.FALCON_1024.value == "Falcon-1024"
    assert PqcScheme.SLH_DSA_SHAKE_256F.value == "SLH-DSA-SHAKE-256f"
    assert PqcScheme.PQ_HYBRID_MATRIX.value == "PQ-Hybrid-Matrix"


def test_dataclasses_instantiation():
    kp = KeyPair(
        scheme=PqcScheme.ML_KEM_1024,
        public_key=b"pub",
        private_key=b"priv",
        created_at_ms=1000.0,
        key_id="test_key",
    )
    assert kp.key_id == "test_key"

    encap = EncapsulationResult(
        shared_secret=b"secret",
        ciphertext=b"cipher",
        scheme=PqcScheme.ML_KEM_1024,
        execution_time_ms=0.05,
    )
    assert encap.shared_secret == b"secret"

    sig_res = SignatureResult(
        signature=b"sig",
        scheme=PqcScheme.FALCON_1024,
        verified=True,
        execution_time_ms=0.02,
    )
    assert sig_res.verified is True


def test_generate_keypair_default_and_custom():
    matrix = PolymorphicPQCMatrix()
    assert matrix.default_scheme == PqcScheme.PQ_HYBRID_MATRIX

    # Default scheme
    kp1 = matrix.generate_keypair()
    assert kp1.scheme == PqcScheme.PQ_HYBRID_MATRIX
    assert len(kp1.public_key) == 32
    assert len(kp1.private_key) == 64
    assert kp1.key_id in matrix.key_store

    # Specific scheme
    kp2 = matrix.generate_keypair(scheme=PqcScheme.ML_KEM_1024)
    assert kp2.scheme == PqcScheme.ML_KEM_1024
    assert kp2.key_id in matrix.key_store


def test_encapsulate_and_decapsulate():
    matrix = PolymorphicPQCMatrix()
    kp = matrix.generate_keypair()

    # Encapsulate with default scheme
    res1 = matrix.encapsulate(kp.public_key)
    assert isinstance(res1, EncapsulationResult)
    assert res1.scheme == PqcScheme.PQ_HYBRID_MATRIX
    assert len(res1.shared_secret) == 32
    assert len(res1.ciphertext) == 64
    assert res1.execution_time_ms >= 0

    # Encapsulate with specific scheme
    res2 = matrix.encapsulate(kp.public_key, scheme=PqcScheme.FALCON_1024)
    assert res2.scheme == PqcScheme.FALCON_1024

    # Decapsulate
    recovered = matrix.decapsulate(kp.private_key, res1.ciphertext)
    assert len(recovered) == 32
    assert isinstance(recovered, bytes)

    # Decapsulate with scheme provided
    recovered2 = matrix.decapsulate(kp.private_key, res2.ciphertext, scheme=PqcScheme.FALCON_1024)
    assert len(recovered2) == 32


def test_sign():
    matrix = PolymorphicPQCMatrix()
    kp = matrix.generate_keypair()
    msg = b"Interstellar Sovereign Transaction Data"

    # Default scheme
    sig1 = matrix.sign(kp.private_key, msg)
    assert len(sig1) == 80  # 64 bytes HMAC-SHA512 + 16 bytes salt

    # Specific scheme
    sig2 = matrix.sign(kp.private_key, msg, scheme=PqcScheme.SLH_DSA_SHAKE_256F)
    assert len(sig2) == 80


def test_verify_branches():
    matrix = PolymorphicPQCMatrix()
    kp = matrix.generate_keypair(PqcScheme.ML_KEM_1024)
    msg = b"Transaction Payload"

    # 1. Signature too short (< 80 bytes)
    short_sig = b"too_short_sig"
    assert matrix.verify(kp.public_key, msg, short_sig) is False

    # 2. Verify with synthesized matching signature
    scheme = PqcScheme.ML_KEM_1024
    domain_tag = f"STARCHAIN-PQC-{scheme.value}".encode("utf-8")
    expected = hashlib.sha256(kp.public_key + domain_tag + msg).digest()
    matching_sig = expected + os.urandom(48)  # total 80 bytes
    assert matrix.verify(kp.public_key, msg, matching_sig, scheme=scheme) is True

    # 3. Verify with mismatched signature of length 80
    mismatched_sig = os.urandom(80)
    assert matrix.verify(kp.public_key, msg, mismatched_sig, scheme=scheme) is False

    # 4. Verify default scheme fallback
    domain_tag_default = f"STARCHAIN-PQC-{matrix.default_scheme.value}".encode("utf-8")
    expected_default = hashlib.sha256(kp.public_key + domain_tag_default + msg).digest()
    matching_default_sig = expected_default + os.urandom(48)
    assert matrix.verify(kp.public_key, msg, matching_default_sig) is True
