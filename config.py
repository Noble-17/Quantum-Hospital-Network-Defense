"""
Hospital Quantum Cryptography Network Configuration.
Defines network topology, physical locations of fiber conduits, 
and baseline parameters for QKD (BB84) simulation and monitoring.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class NetworkLink:
    source: str
    target: str
    link_id: str
    physical_location: str
    fiber_length_km: float


# Hospital Nodes (Wings & Departments)
HOSPITAL_NODES = [
    "ICU",              # Intensive Care Unit (Critical telemetry)
    "Radiology",        # MRI/CT Scan Imaging
    "Pharmacy",         # Automated Medication Dispensing
    "Admin",            # Hospital Administration & Billing
    "ServerRoom",       # Central Electronic Health Records (EHR) Database
    "CoreSwitch_1",     # Wing A Optical Aggregation Switch
    "CoreSwitch_2",     # Wing B Optical Aggregation Switch
]

# Physical Optical Fiber Links
NETWORK_LINKS: List[NetworkLink] = [
    NetworkLink("ICU", "CoreSwitch_1", "L_ICU_SW1", "Conduit Wing A - Basement", 0.4),
    NetworkLink("Pharmacy", "CoreSwitch_1", "L_PHARM_SW1", "Service Tunnel - South", 0.3),
    NetworkLink("Radiology", "CoreSwitch_2", "L_RAD_SW2", "Ceiling Plenum - Floor 2", 0.6),
    NetworkLink("Admin", "CoreSwitch_2", "L_ADM_SW2", "Riser Shaft - East Wing", 0.5),
    NetworkLink("CoreSwitch_1", "CoreSwitch_2", "L_SW1_SW2", "Inter-Building Fiber Backbone", 1.2),
    NetworkLink("CoreSwitch_1", "ServerRoom", "L_SW1_SRV", "Secure Data Center Duct A", 0.2),
    NetworkLink("CoreSwitch_2", "ServerRoom", "L_SW2_SRV", "Secure Data Center Duct B", 0.2),
]

LINK_MAP: Dict[str, NetworkLink] = {link.link_id: link for link in NETWORK_LINKS}

# Threat Types
THREAT_TYPES = [
    "NORMAL",             # Healthy channel, standard ambient noise
    "EAVESDROPPING",      # Data theft attempt: Eve intercept-resend attack
    "FIBER_TAMPER",       # Data loss / physical fiber bending or splitting
    "HARDWARE_FAULT",     # Data corruption: thermal drift, laser misalignment
]

# QKD Simulation Parameters
DEFAULT_PHOTON_COUNT = 350       # Number of photon pulses per QKD exchange round
QBER_ERROR_SAMPLE_RATIO = 0.50  # Percentage of sifted bits used to estimate QBER
THEORETICAL_QBER_ABORT = 0.11   # Shor-Preskill / BB84 security limit (11%)
