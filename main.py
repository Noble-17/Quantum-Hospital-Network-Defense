"""
Main CLI Orchestrator for Hospital Quantum Cryptography & AI Security System.
Supports interactive demo, dataset generation, training, and custom incident injection.
"""

import sys
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from config import LINK_MAP, HOSPITAL_NODES, THREAT_TYPES
from qkd_simulator import BB84Simulator
from dataset_generator import generate_qkd_dataset
from ml_detector import HospitalSecurityAI
from demo_monitor import HospitalSOCMonitor


def main():
    parser = argparse.ArgumentParser(
        description="Hospital Quantum Cryptography (QKD BB84) & Random Forest AI Intrusion Localization System"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: gui
    subparsers.add_parser("gui", help="Launch Unified Visual Desktop GUI Dashboard")

    # Command: demo
    subparsers.add_parser("demo", help="Run end-to-end interactive Hospital SOC simulation")

    # Command: circuit
    subparsers.add_parser("circuit", help="Display Qiskit Dynamic Quantum Circuit for BB84")

    # Command: train
    subparsers.add_parser("train", help="Train Random Forest Threat Classifier & Localization Engine")

    # Command: generate-data
    p_gen = subparsers.add_parser("generate-data", help="Generate synthetic multi-link QKD telemetry dataset")
    p_gen.add_argument("--samples", type=int, default=2800, help="Number of telemetry events to generate")

    # Command: inject
    p_inject = subparsers.add_parser("inject", help="Inject custom attack scenario and inspect AI localization")
    p_inject.add_argument("--src", type=str, default="ICU", choices=HOSPITAL_NODES, help="Source hospital node")
    p_inject.add_argument("--dst", type=str, default="ServerRoom", choices=HOSPITAL_NODES, help="Destination hospital node")
    p_inject.add_argument("--link", type=str, default="L_ICU_SW1", choices=list(LINK_MAP.keys()), help="Target link to compromise")
    p_inject.add_argument("--type", type=str, default="EAVESDROPPING", choices=THREAT_TYPES, help="Threat type to inject")

    args = parser.parse_args()

    if args.command == "gui":
        from gui_app import launch_gui
        print("[*] Launching Hospital Quantum SOC Desktop GUI Dashboard...")
        launch_gui()

    elif args.command == "demo" or args.command is None:
        print("[*] Running End-to-End Hospital SOC Quantum Intrusion Detection Demo...\n")
        soc = HospitalSOCMonitor()
        soc.run_transmission_cycle("ICU", "ServerRoom", attack_link=None, threat_type="NORMAL")
        soc.run_transmission_cycle("ICU", "ServerRoom", attack_link="L_ICU_SW1", threat_type="EAVESDROPPING")
        soc.run_transmission_cycle("Radiology", "ServerRoom", attack_link="L_RAD_SW2", threat_type="FIBER_TAMPER")
        soc.run_transmission_cycle("Pharmacy", "ServerRoom", attack_link="L_PHARM_SW1", threat_type="HARDWARE_FAULT")

    elif args.command == "circuit":
        sim = BB84Simulator()
        qc = sim.build_sample_circuit()
        print("\n--- QISKIT DYNAMIC QUANTUM CIRCUIT (BB84 with Eve Intercept-Resend) ---")
        try:
            print(qc.draw(output='text'))
        except Exception:
            print(f"Circuit gates: {qc.count_ops()}")

    elif args.command == "train":
        ai = HospitalSecurityAI()
        ai.train_and_evaluate()

    elif args.command == "generate-data":
        generate_qkd_dataset(num_samples=args.samples)

    elif args.command == "inject":
        soc = HospitalSOCMonitor()
        soc.run_transmission_cycle(
            source=args.src,
            destination=args.dst,
            attack_link=args.link,
            threat_type=args.type
        )


if __name__ == "__main__":
    main()
