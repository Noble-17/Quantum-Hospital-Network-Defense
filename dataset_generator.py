"""
Synthetic Dataset Generator for Hospital QKD Network Telemetry.
Simulates network scans under diverse normal operations (heavy normal representation),
eavesdropping attacks, physical fiber tampering, and hardware faults across all hospital links.
"""

from typing import List, Dict, Any
import numpy as np
import pandas as pd

from config import NETWORK_LINKS, THREAT_TYPES, LINK_MAP
from network_topology import HospitalNetwork


def generate_qkd_dataset(
    num_samples: int = 3300,
    output_csv: str = "hospital_qkd_telemetry_dataset.csv",
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates a rich, realistic dataset of hospital network quantum telemetry.
    Features robust representation of NORMAL operations alongside diverse attack vectors.
    """
    np.random.seed(seed)
    net = HospitalNetwork()
    records: List[Dict[str, Any]] = []

    print(f"Generating {num_samples} simulated hospital network telemetry events...")

    # Distribution:
    # 45% NORMAL transmissions (1,500 samples)
    # 55% Attacks (1,800 samples total -> 600 Eavesdropping, 600 Fiber Tamper, 600 Hardware Fault)
    normal_count = 1500
    attack_count_per_type = 600
    link_ids = [l.link_id for l in NETWORK_LINKS]

    # 1. Normal Conditions (Diverse daytime/nighttime variations across all hospital departments)
    print(f"Simulating {normal_count} NORMAL network transmissions...")
    for _ in range(normal_count):
        rec = net.scan_network_telemetry(attack_link_id=None, threat_type="NORMAL", fast_mode=True)
        records.append(rec)

    # 2. Eavesdropping Attacks (Data theft across all fiber links)
    print(f"Simulating {attack_count_per_type} EAVESDROPPING attacks across hospital wings...")
    for _ in range(attack_count_per_type):
        target_link = np.random.choice(link_ids)
        rec = net.scan_network_telemetry(attack_link_id=target_link, threat_type="EAVESDROPPING", fast_mode=True)
        records.append(rec)

    # 3. Fiber Tampering / Physical Photon Loss
    print(f"Simulating {attack_count_per_type} FIBER TAMPERING attacks across conduits...")
    for _ in range(attack_count_per_type):
        target_link = np.random.choice(link_ids)
        rec = net.scan_network_telemetry(attack_link_id=target_link, threat_type="FIBER_TAMPER", fast_mode=True)
        records.append(rec)

    # 4. Hardware Fault / Data Corruption
    print(f"Simulating {attack_count_per_type} HARDWARE FAULTS across transceivers...")
    for _ in range(attack_count_per_type):
        target_link = np.random.choice(link_ids)
        rec = net.scan_network_telemetry(attack_link_id=target_link, threat_type="HARDWARE_FAULT", fast_mode=True)
        records.append(rec)

    df = pd.DataFrame(records)
    # Shuffle dataset
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)

    df.to_csv(output_csv, index=False)
    print(f"\nDataset successfully created and saved to: {output_csv}")
    print(f"Dataset shape: {df.shape}")
    print(f"Threat distribution:\n{df['target_threat'].value_counts()}\n")
    print(f"Target link distribution:\n{df['target_link'].value_counts()}\n")

    return df


if __name__ == "__main__":
    df = generate_qkd_dataset(num_samples=3300)
