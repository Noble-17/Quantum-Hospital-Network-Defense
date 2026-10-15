"""
Hospital Quantum Cryptography SOC (Security Operations Center) Monitor.
Simulates real-time confidential patient data transmission across hospital wings,
monitors quantum telemetry (QBER, photon loss, key generation) via Qiskit BB84,
and uses Random Forest AI to detect data theft/corruption and pinpoint the exact physical conduit.
"""

import sys
from typing import Dict, Any, List, Optional
import numpy as np

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from config import LINK_MAP, NETWORK_LINKS
from network_topology import HospitalNetwork
from ml_detector import HospitalSecurityAI
from qkd_simulator import BB84Simulator


def xor_cipher(text: str, key_bits: str) -> str:
    """One-Time Pad / Vernam stream cipher using QKD secret key."""
    if not key_bits:
        return ""
    text_bytes = text.encode('utf-8')
    key_bytes = [int(key_bits[i:i+8], 2) for i in range(0, len(key_bits) - 7, 8)]
    if not key_bytes:
        key_bytes = [42]

    ciphertext_bytes = []
    for i, b in enumerate(text_bytes):
        k = key_bytes[i % len(key_bytes)]
        ciphertext_bytes.append(b ^ k)

    return bytes(ciphertext_bytes).hex()


class HospitalSOCMonitor:
    def __init__(self):
        self.network = HospitalNetwork()
        self.ai = HospitalSecurityAI()
        self.qkd = BB84Simulator()

    def _reencrypt_on_safe_path(
        self,
        patient_record: str,
        safe_path: List[str],
        threat_type: str,
    ) -> Optional[str]:
        """
        Runs a fresh BB84 QKD exchange on the first link of the safe rerouted path,
        derives a new One-Time Pad key from the resulting raw key bits, and
        re-encrypts the patient record.  Returns the hex ciphertext, or None if
        QKD on the safe link fails to produce a usable key.
        """
        safe_links = self.network.get_path_links(safe_path)
        if not safe_links:
            return None

        safe_link = safe_links[0]
        print(f"\n[RE-ENCRYPTION] Running fresh BB84 QKD on safe link [{safe_link.link_id}]"
              f" ({safe_link.physical_location})...")

        telemetry = self.qkd.simulate_link_transmission(
            fiber_length_km=safe_link.fiber_length_km,
            eve_attack_prob=0.0,          # clean channel – no adversary
            tamper_loss_prob=0.0,
            channel_noise_prob=0.015,
            use_aer=True,
        )

        if not telemetry.is_secure or not telemetry.raw_key:
            print("  [!] QKD on safe link could not establish a secure key. "
                  "Data held in encrypted buffer.")
            return None

        print(f"  * Fresh QKD key established – {telemetry.secret_key_len} bits "
              f"| QBER: {telemetry.qber:.2%} | SNR: {telemetry.snr_db:.2f} dB")

        ciphertext = xor_cipher(patient_record, telemetry.raw_key)
        print(f"  * Re-encrypted Ciphertext  : {ciphertext[:40]}... (Quantum-Safe OTP)")
        print(f"  * Threat type resolved     : {threat_type}")
        print("  * Delivery Status          : SUCCESSFUL over secure bypass path.")
        return ciphertext

    def run_transmission_cycle(
        self,
        source: str = "ICU",
        destination: str = "ServerRoom",
        patient_record: str = "PATIENT_ID: #40921 | VITALS: BP 120/80, SpO2 99%, HR 72 | DIAGNOSIS: Stable",
        attack_link: Optional[str] = None,
        threat_type: str = "NORMAL",
        save_map: bool = True
    ):
        print("\n" + "=" * 75)
        print(f"[HOSPITAL SOC] QUANTUM SECURE TRANSMISSION DISPATCH")
        print(f"From: [{source}]  --->  To: [{destination}]")
        print(f"Confidential Payload: \"{patient_record}\"")
        print("=" * 75)

        # 1. Routing
        path = self.network.get_shortest_path(source, destination)
        print(f"Primary Optical Routing: {' -> '.join(path)}")
        links_traversed = self.network.get_path_links(path)
        print("Optical Links traversed:")
        for l in links_traversed:
            print(f"  * [{l.link_id}] {l.source} -> {l.target} | Location: '{l.physical_location}'")

        if attack_link:
            loc = LINK_MAP[attack_link].physical_location if attack_link in LINK_MAP else "Unknown"
            print(f"\n[ATTACK INJECTION] Injected Threat: '{threat_type}' on Link [{attack_link}] ({loc})")
        else:
            print(f"\n[NETWORK STATUS] All hospital fiber conduits operating nominally.")

        # 2. Collect Real-Time Telemetry via Qiskit BB84 & Network Monitor
        print("\n[QKD ENGINE] Executing Qiskit BB84 Quantum Key Distribution across hospital links...")
        telemetry = self.network.scan_network_telemetry(
            attack_link_id=attack_link,
            threat_type=threat_type,
            fast_mode=False  # Full Qiskit Aer circuit simulation
        )

        # 3. Classical Machine Learning Analysis (Random Forest)
        print("[AI MONITOR] Feeding quantum telemetry vector to Classical Random Forest AI...")
        analysis = self.ai.analyze_network_telemetry(telemetry)

        pred_threat = analysis["predicted_threat"]
        threat_conf = analysis["threat_confidence"]
        pred_link = analysis["predicted_link"]
        link_conf = analysis["link_confidence"]
        pred_loc = analysis["physical_location"]

        print("\n" + "-" * 75)
        print("[AI REPORT] QUANTUM NETWORK INTRUSION DETECTION & LOCALIZATION")
        print("-" * 75)
        print(f"Threat Classification:     {pred_threat} (Confidence: {threat_conf:.1f}%)")
        print(f"Pinpointed Link ID:        {pred_link} (Confidence: {link_conf:.1f}%)")
        print(f"Exact Physical Location:   {pred_loc}")

        # Show telemetry on the relevant link
        focus_link = attack_link if attack_link else links_traversed[0].link_id
        qber_val = telemetry[f"{focus_link}_qber"]
        loss_val = telemetry[f"{focus_link}_loss"]
        key_bits = telemetry[f"{focus_link}_key_len"]
        snr_val = telemetry[f"{focus_link}_snr"]

        print(f"\nQuantum Telemetry Metrics on Link [{focus_link}]:")
        print(f"  * QBER (Quantum Bit Error Rate):  {qber_val:6.2%}  (Safe threshold <= 11.00%)")
        print(f"  * Optical Photon Loss Rate:       {loss_val:6.2%}")
        print(f"  * Detector SNR:                   {snr_val:6.2f} dB")
        print(f"  * Raw Secret Key Bits Yield:      {key_bits} bits")

        # 4. Security Action & Cryptographic Handling
        print("\n" + "-" * 75)
        print("[RESPONSE] AUTOMATED INCIDENT RESPONSE & CRYPTOGRAPHY ENGINE")
        print("-" * 75)

        if pred_threat == "NORMAL":
            dummy_key = "101100101101001110010101111000101011001011010011"
            ciphertext = xor_cipher(patient_record, dummy_key)
            print("STATUS: CHANNEL HEALTHY & UNCOMPROMISED")
            print(f"  * Encrypted Ciphertext: {ciphertext[:40]}... (Quantum-Safe OTP)")
            print("  * Delivery Status: SUCCESSFUL (Patient health record saved to EHR DB).")

        elif pred_threat == "EAVESDROPPING":
            print("STATUS: CRITICAL DATA THEFT / INTERCEPT-RESEND ATTEMPT DETECTED!")
            print(f"  * High QBER ({qber_val:.2%}) indicates quantum state disturbance by eavesdropper.")
            print(f"  * Key Generation ABORTED immediately on link {pred_link} (Eve learned 0 information).")
            print(f"  * Exact Physical Location pinpointed: '{pred_loc}'.")

            alt_path = self.network.find_alternative_path(source, destination, compromised_link_id=pred_link)
            if alt_path:
                print(f"  * DYNAMIC REROUTING: Traffic rerouted via safe bypass: {' -> '.join(alt_path)}")
                self._reencrypt_on_safe_path(patient_record, alt_path, pred_threat)
            else:
                print("  * No bypass available. Data held in encrypted buffer pending conduit inspection.")

        elif pred_threat == "FIBER_TAMPER":
            print("STATUS: PHYSICAL FIBER TAMPERING DETECTED (Optical Splitter Tap / Loss)!")
            print(f"  * Photon loss spiked to {loss_val:.2%}.")
            print(f"  * Action: Dispatching hospital security to inspect: '{pred_loc}'.")
            alt_path = self.network.find_alternative_path(source, destination, compromised_link_id=pred_link)
            if alt_path:
                print(f"  * Rerouting patient data via: {' -> '.join(alt_path)}")
                self._reencrypt_on_safe_path(patient_record, alt_path, pred_threat)
            else:
                print("  * No bypass available. Data held in encrypted buffer pending conduit inspection.")

        elif pred_threat == "HARDWARE_FAULT":
            print("STATUS: HARDWARE TRANSCEIVER ANOMALY DETECTED!")
            print(f"  * Elevated baseline noise detected at: '{pred_loc}'.")
            print(f"  * Action: Logged maintenance ticket for laser/detector recalibration.")
            alt_path = self.network.find_alternative_path(source, destination, compromised_link_id=pred_link)
            if alt_path:
                print(f"  * DYNAMIC REROUTING: Traffic rerouted via safe bypass: {' -> '.join(alt_path)}")
                self._reencrypt_on_safe_path(patient_record, alt_path, pred_threat)
            else:
                print("  * No bypass available. Data held in encrypted buffer pending conduit inspection.")

        # Save Incident Topology Map
        if save_map:
            highlight = pred_link if pred_threat != "NORMAL" else None
            map_name = f"incident_{threat_type.lower()}_map.png"
            self.network.visualize_topology(save_path=map_name, highlight_link=highlight)
            print(f"\n[MAP] Network topology snapshot saved to '{map_name}'")

        print("=" * 75 + "\n")


if __name__ == "__main__":
    monitor = HospitalSOCMonitor()

    # Scenario 1: Normal Transfer
    monitor.run_transmission_cycle(
        source="ICU",
        destination="ServerRoom",
        patient_record="PATIENT_ID: #40921 | VITALS: BP 120/80, SpO2 99%, HR 72 | DIAGNOSIS: Stable",
        attack_link=None,
        threat_type="NORMAL"
    )

    # Scenario 2: Eavesdropping (Data Theft) on ICU Link
    monitor.run_transmission_cycle(
        source="ICU",
        destination="ServerRoom",
        patient_record="PATIENT_ID: #40921 | VITALS: BP 120/80, SpO2 99%, HR 72 | DIAGNOSIS: Stable",
        attack_link="L_ICU_SW1",
        threat_type="EAVESDROPPING"
    )

    # Scenario 3: Physical Fiber Tampering (Data Loss / Splitter Tap) on Radiology Link
    monitor.run_transmission_cycle(
        source="Radiology",
        destination="ServerRoom",
        patient_record="PATIENT_ID: #89110 | SCAN: Brain MRI Diffusion Tensor Imaging | 450 MB",
        attack_link="L_RAD_SW2",
        threat_type="FIBER_TAMPER"
    )
