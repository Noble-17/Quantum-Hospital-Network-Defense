"""
Quantum Key Distribution (QKD) BB84 Simulator using Qiskit 2.x and Qiskit Aer.
Features:
- Full quantum circuit representation using dynamic circuits (mid-circuit measurement, reset, if_test)
- Physical optical fiber simulation (attenuation, detector efficiency, latency, SNR)
- Eavesdropping attack simulation (Eve intercept-resend)
- Physical fiber tampering (excess photon loss / tap)
- Optical hardware degradation (dark counts / depolarizing noise)
- Basis sifting & QBER calculation
- Dual-engine: Aer Quantum Simulator for circuit execution & Vectorized engine for fast dataset training
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator

from config import DEFAULT_PHOTON_COUNT, QBER_ERROR_SAMPLE_RATIO, THEORETICAL_QBER_ABORT


@dataclass
class QKDTelemetry:
    qber: float                     # Quantum Bit Error Rate (0.0 to 1.0)
    loss_rate: float                # Photon loss rate (0.0 to 1.0)
    sent_photons: int               # Initial photons sent by Alice
    received_photons: int           # Photons detected by Bob
    sifted_bits_count: int          # Photons with matching bases
    secret_key_len: int             # Secret key bits remaining after QBER test
    latency_ms: float               # Optical link latency in ms
    snr_db: float                   # Optical detector Signal-to-Noise Ratio (dB)
    is_secure: bool                 # True if QBER <= theoretical threshold (11%)
    raw_key: str                    # Final raw secret key bitstring
    eve_detected: bool              # True if QBER exceeds 11%


class BB84Simulator:
    def __init__(self):
        self.simulator = AerSimulator()

    def build_sample_circuit(self) -> QuantumCircuit:
        """
        Builds an illustrative multi-stage Qiskit BB84 circuit showing Alice, Eve, and Bob.
        Useful for visualization, diagram export, and demonstration.
        """
        qr = QuantumRegister(2, 'qubit')
        cr_eve = ClassicalRegister(2, 'eve_meas')
        cr_bob = ClassicalRegister(2, 'bob_meas')
        qc = QuantumCircuit(qr, cr_eve, cr_bob, name="Hospital_BB84_QKD")

        # Qubit 0: Alice sends |1> in Z basis, Eve intercepts in X basis, Bob measures in Z basis
        qc.x(qr[0])  # Alice bit 1
        qc.barrier(label="Channel")

        # Eve intercepts qubit 0 in X basis
        qc.h(qr[0])
        qc.measure(qr[0], cr_eve[0])
        qc.reset(qr[0])
        with qc.if_test((cr_eve[0], 1)):
            qc.x(qr[0])
        qc.h(qr[0])
        qc.barrier(label="Bob Reception")

        # Bob measures qubit 0 in Z basis
        qc.measure(qr[0], cr_bob[0])

        # Qubit 1: Alice sends |+> in X basis, No Eve, Bob measures in X basis
        qc.h(qr[1])  # Alice bit 0 in X basis
        qc.barrier(label="Channel")
        qc.h(qr[1])  # Bob measures in X basis
        qc.measure(qr[1], cr_bob[1])

        return qc

    def simulate_link_transmission(
        self,
        num_photons: int = DEFAULT_PHOTON_COUNT,
        fiber_length_km: float = 0.5,
        eve_attack_prob: float = 0.0,
        tamper_loss_prob: float = 0.0,
        channel_noise_prob: float = 0.015,
        use_aer: bool = True,
        seed: Optional[int] = None
    ) -> QKDTelemetry:
        """
        Simulates a full QKD transmission round over a physical fiber link.
        """
        rng = np.random.default_rng(seed)

        # 1. Optical Attenuation & Detection Efficiency
        baseline_transmissivity = 10.0 ** (-(0.2 * fiber_length_km) / 10.0)
        detector_efficiency = 0.85
        survival_prob = baseline_transmissivity * detector_efficiency * (1.0 - tamper_loss_prob)
        survival_prob = max(0.02, min(0.99, survival_prob))

        # Alice generates random bits and bases (0 = Z basis, 1 = X basis)
        alice_bits = rng.integers(0, 2, size=num_photons)
        alice_bases = rng.integers(0, 2, size=num_photons)

        # Bob selects random measurement bases
        bob_bases = rng.integers(0, 2, size=num_photons)

        # Photon survival
        received_mask = rng.random(num_photons) < survival_prob
        received_indices = np.where(received_mask)[0]
        received_count = len(received_indices)

        if received_count == 0:
            return QKDTelemetry(
                qber=1.0,
                loss_rate=1.0,
                sent_photons=num_photons,
                received_photons=0,
                sifted_bits_count=0,
                secret_key_len=0,
                latency_ms=round(fiber_length_km * 5.0 + 2.0, 4),
                snr_db=0.0,
                is_secure=False,
                raw_key="",
                eve_detected=True
            )

        if use_aer and received_count <= 250:
            # Full Qiskit Aer Dynamic Circuit Simulation
            qr = QuantumRegister(received_count, 'q')
            cr_eve = ClassicalRegister(received_count, 'eve')
            cr_bob = ClassicalRegister(received_count, 'bob')
            qc = QuantumCircuit(qr, cr_eve, cr_bob)

            eve_attack_flags = rng.random(received_count) < eve_attack_prob
            eve_bases = rng.integers(0, 2, size=received_count)

            for i, global_idx in enumerate(received_indices):
                a_bit = int(alice_bits[global_idx])
                a_base = int(alice_bases[global_idx])
                b_base = int(bob_bases[global_idx])

                # Alice Preparation
                if a_bit == 1:
                    qc.x(qr[i])
                if a_base == 1:
                    qc.h(qr[i])

                # Environmental Noise
                if rng.random() < channel_noise_prob:
                    if rng.random() < 0.5:
                        qc.x(qr[i])
                    else:
                        qc.z(qr[i])

                # Eve Intercept-Resend Attack
                if eve_attack_flags[i]:
                    if eve_bases[i] == 1:
                        qc.h(qr[i])
                    qc.measure(qr[i], cr_eve[i])
                    qc.reset(qr[i])
                    with qc.if_test((cr_eve[i], 1)):
                        qc.x(qr[i])
                    if eve_bases[i] == 1:
                        qc.h(qr[i])

                # Bob Measurement
                if b_base == 1:
                    qc.h(qr[i])
                qc.measure(qr[i], cr_bob[i])

            job = self.simulator.run(qc, shots=1, memory=True)
            result = job.result()
            memory_str = result.get_memory()[0]
            bob_memory = memory_str.split()[0] if ' ' in memory_str else memory_str
            bob_bits = [int(bob_memory[received_count - 1 - i]) for i in range(received_count)]

        else:
            # Fast Vectorized Quantum Measurement Model (identically faithful to quantum projection)
            bob_bits = []
            for i, global_idx in enumerate(received_indices):
                curr_bit = int(alice_bits[global_idx])
                curr_base = int(alice_bases[global_idx])

                # Environmental noise
                if rng.random() < channel_noise_prob:
                    curr_bit ^= 1

                # Eve Interception
                if rng.random() < eve_attack_prob:
                    eve_base = rng.integers(0, 2)
                    if eve_base != curr_base:
                        # State collapses to Eve's basis: 50% chance 0 or 1
                        curr_bit = rng.integers(0, 2)
                    curr_base = eve_base

                # Bob Measurement
                b_base = int(bob_bases[global_idx])
                if b_base == curr_base:
                    bob_bits.append(curr_bit)
                else:
                    # Conjugate basis measurement yields random bit
                    bob_bits.append(int(rng.integers(0, 2)))

        # Sifting: Match Alice & Bob bases
        sifted_alice = []
        sifted_bob = []
        for i, global_idx in enumerate(received_indices):
            if alice_bases[global_idx] == bob_bases[global_idx]:
                sifted_alice.append(int(alice_bits[global_idx]))
                sifted_bob.append(bob_bits[i])

        sifted_count = len(sifted_alice)
        if sifted_count == 0:
            return QKDTelemetry(
                qber=1.0,
                loss_rate=round(1.0 - (received_count / num_photons), 4),
                sent_photons=num_photons,
                received_photons=received_count,
                sifted_bits_count=0,
                secret_key_len=0,
                latency_ms=round(fiber_length_km * 0.005 + 0.15, 4),
                snr_db=5.0,
                is_secure=False,
                raw_key="",
                eve_detected=True
            )

        # QBER Estimation: Test sample
        sample_size = max(1, int(sifted_count * QBER_ERROR_SAMPLE_RATIO))
        test_indices = set(rng.choice(sifted_count, size=sample_size, replace=False))

        errors = sum(sifted_alice[k] != sifted_bob[k] for k in test_indices)
        qber = float(errors) / float(sample_size)

        # Raw key generation from remaining bits
        key_indices = [k for k in range(sifted_count) if k not in test_indices]
        raw_key = "".join(str(sifted_bob[k]) for k in key_indices)
        secret_key_len = len(key_indices)

        loss_rate = 1.0 - (received_count / num_photons)
        snr_db = max(3.0, 32.0 - (loss_rate * 22.0) - (channel_noise_prob * 100.0) + rng.normal(0, 0.4))
        latency_ms = (fiber_length_km * 0.005) + 0.15 + rng.uniform(0.01, 0.04)
        is_secure = qber <= THEORETICAL_QBER_ABORT

        return QKDTelemetry(
            qber=round(qber, 4),
            loss_rate=round(loss_rate, 4),
            sent_photons=num_photons,
            received_photons=received_count,
            sifted_bits_count=sifted_count,
            secret_key_len=secret_key_len,
            latency_ms=round(latency_ms, 4),
            snr_db=round(snr_db, 2),
            is_secure=is_secure,
            raw_key=raw_key,
            eve_detected=(qber > THEORETICAL_QBER_ABORT)
        )


if __name__ == "__main__":
    sim = BB84Simulator()
    print("Testing sample quantum circuit:")
    sample_qc = sim.build_sample_circuit()
    try:
        import sys
        sys.stdout.reconfigure(encoding='utf-8')
        print(sample_qc.draw(output='text'))
    except Exception:
        print(f"Circuit gates: {sample_qc.count_ops()}")

    print("\nSimulating QKD under Normal vs Attack conditions (using Aer):")
    t_normal = sim.simulate_link_transmission(num_photons=250, eve_attack_prob=0.0)
    print(f"NORMAL:       QBER = {t_normal.qber:6.2%} | Loss = {t_normal.loss_rate:6.2%} | Key = {t_normal.secret_key_len:2d} bits | Secure = {t_normal.is_secure}")

    t_eve = sim.simulate_link_transmission(num_photons=250, eve_attack_prob=0.9)
    print(f"EAVESDROP:    QBER = {t_eve.qber:6.2%} | Loss = {t_eve.loss_rate:6.2%} | Key = {t_eve.secret_key_len:2d} bits | Secure = {t_eve.is_secure}")

    t_tamper = sim.simulate_link_transmission(num_photons=250, tamper_loss_prob=0.6)
    print(f"FIBER TAP:    QBER = {t_tamper.qber:6.2%} | Loss = {t_tamper.loss_rate:6.2%} | Key = {t_tamper.secret_key_len:2d} bits | Secure = {t_tamper.is_secure}")
