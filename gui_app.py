"""
Hospital Quantum Security Operations Center (SOC) - CustomTkinter GUI Dashboard.
Provides a unified visual control panel for:
1. Live Quantum Key Distribution (QKD BB84) confidential patient data transmission.
2. Attack injection (Eavesdropping, Fiber Tampering, Hardware Fault) across hospital wings.
3. Real-time QBER, Photon Loss, SNR, and Secret Key metrics.
4. Classical Random Forest AI threat classification and physical conduit localization.
5. Network Topology inspection and dynamic rerouting maps.
6. Qiskit Dynamic Quantum Circuit visualization.
7. Machine Learning diagnostics (confusion matrix and Gini feature importances).
"""

import os
import sys
import threading
import time
from typing import Optional, Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import customtkinter as ctk
from PIL import Image

from config import HOSPITAL_NODES, NETWORK_LINKS, LINK_MAP, THREAT_TYPES
from network_topology import HospitalNetwork
from ml_detector import HospitalSecurityAI
from qkd_simulator import BB84Simulator

# Theme Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class HospitalQuantumGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🏥 Hospital Quantum Cryptography & AI Security SOC")
        self.geometry("1260x860")
        self.minsize(1100, 750)

        # Core Backend Engines
        self.network = HospitalNetwork()
        self.ai = HospitalSecurityAI()
        self.qkd_sim = BB84Simulator()

        # Build UI Layout
        self._setup_layout()
        self._populate_transmissions_tab()
        self._populate_topology_tab()
        self._populate_circuit_tab()
        self._populate_ml_tab()

    def _setup_layout(self):
        # Grid Configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        title_label = ctk.CTkLabel(
            self.sidebar,
            text="QUANTUM SOC\nDEFENSE SYSTEM",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#38bdf8"
        )
        title_label.grid(row=0, column=0, padx=20, pady=(25, 10))

        sub_label = ctk.CTkLabel(
            self.sidebar,
            text="QKD BB84 + Random Forest AI",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        )
        sub_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Status Badge
        self.sys_status_badge = ctk.CTkLabel(
            self.sidebar,
            text="● SYSTEM ONLINE",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#10b981",
            fg_color="#064e3b",
            corner_radius=8,
            padx=12,
            pady=4
        )
        self.sys_status_badge.grid(row=2, column=0, padx=20, pady=(0, 20))

        # Sidebar Quick Actions
        btn_audit = ctk.CTkButton(
            self.sidebar,
            text="▶ Run Quick Demo Audit",
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self._run_quick_audit
        )
        btn_audit.grid(row=3, column=0, padx=20, pady=8)

        btn_retrain = ctk.CTkButton(
            self.sidebar,
            text="⚙ Retrain AI Models",
            fg_color="#475569",
            hover_color="#334155",
            command=self._trigger_retrain
        )
        btn_retrain.grid(row=4, column=0, padx=20, pady=8)

        btn_map_refresh = ctk.CTkButton(
            self.sidebar,
            text="🗺 Refresh Topology Map",
            fg_color="#475569",
            hover_color="#334155",
            command=self._refresh_topology_images
        )
        btn_map_refresh.grid(row=5, column=0, padx=20, pady=8)

        # Footer info
        version_label = ctk.CTkLabel(
            self.sidebar,
            text="Qiskit 2.5 • Aer • Scikit-Learn\nHost: Windows Local SOC",
            font=ctk.CTkFont(size=11),
            text_color="#64748b"
        )
        version_label.grid(row=9, column=0, padx=20, pady=15)

        # --- Main Tabview ---
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

        self.tab_trans = self.tabview.add("⚡ Live Transmission & SOC")
        self.tab_topo = self.tabview.add("🗺 Hospital Network Topology")
        self.tab_circ = self.tabview.add("🔬 Qiskit BB84 Circuit")
        self.tab_ml = self.tabview.add("📊 Machine Learning Analytics")

    # =========================================================================
    # TAB 1: Live Transmission & SOC
    # =========================================================================
    def _populate_transmissions_tab(self):
        tab = self.tab_trans
        tab.grid_columnconfigure((0, 1), weight=1)
        tab.grid_rowconfigure(2, weight=1)

        # Left Column: Dispatch Configuration
        config_frame = ctk.CTkFrame(tab)
        config_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(
            config_frame,
            text="1. MEDICAL TRANSMISSION DISPATCH",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#38bdf8"
        ).pack(anchor="w", padx=15, pady=(12, 8))

        # Source Wing
        ctk.CTkLabel(config_frame, text="Source Wing / Clinic:").pack(anchor="w", padx=15, pady=(4, 2))
        self.src_combo = ctk.CTkComboBox(
            config_frame,
            values=["ICU", "Radiology", "Pharmacy", "Admin"],
            command=self._on_route_change
        )
        self.src_combo.set("ICU")
        self.src_combo.pack(fill="x", padx=15, pady=(0, 6))

        # Destination Wing
        ctk.CTkLabel(config_frame, text="Destination Center:").pack(anchor="w", padx=15, pady=(4, 2))
        self.dst_combo = ctk.CTkComboBox(config_frame, values=["ServerRoom"], state="readonly")
        self.dst_combo.set("ServerRoom")
        self.dst_combo.pack(fill="x", padx=15, pady=(0, 6))

        # Confidential Payload
        ctk.CTkLabel(config_frame, text="Confidential Medical Payload:").pack(anchor="w", padx=15, pady=(4, 2))
        self.payload_entry = ctk.CTkEntry(config_frame)
        self.payload_entry.insert(0, "PATIENT_ID: #40921 | VITALS: BP 120/80, HR 72, SpO2 99% | Status: STABLE")
        self.payload_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Threat Injection
        ctk.CTkLabel(
            config_frame,
            text="SIMULATED ATTACK INJECTION:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#f59e0b"
        ).pack(anchor="w", padx=15, pady=(8, 2))

        threat_options = [
            "NORMAL (Healthy Baseline)",
            "EAVESDROPPING (Data Theft / Eve Intercept-Resend)",
            "FIBER_TAMPER (Physical Tap / Photon Loss)",
            "HARDWARE_FAULT (Transceiver Noise / Laser Drift)"
        ]
        self.threat_combo = ctk.CTkComboBox(
            config_frame,
            values=threat_options,
            command=self._on_threat_change
        )
        self.threat_combo.set(threat_options[0])
        self.threat_combo.pack(fill="x", padx=15, pady=(0, 6))

        # Target Link selector
        ctk.CTkLabel(config_frame, text="Target Fiber Conduit to Attack:").pack(anchor="w", padx=15, pady=(4, 2))
        link_display = [f"{l.link_id} ({l.physical_location})" for l in NETWORK_LINKS]
        self.link_combo = ctk.CTkComboBox(config_frame, values=link_display)
        self.link_combo.set(link_display[0])
        self.link_combo.pack(fill="x", padx=15, pady=(0, 15))

        # Transmit Button
        self.btn_transmit = ctk.CTkButton(
            config_frame,
            text="🚀 TRANSMIT WITH QUANTUM SECURE KEY",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=38,
            command=self._trigger_transmission
        )
        self.btn_transmit.pack(fill="x", padx=15, pady=(5, 15))

        # Right Column: Live Quantum Metrics & AI Verdict
        results_frame = ctk.CTkFrame(tab)
        results_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(
            results_frame,
            text="2. REAL-TIME QUANTUM TELEMETRY & AI VERDICT",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#38bdf8"
        ).pack(anchor="w", padx=15, pady=(12, 10))

        # QBER Gauge Frame
        qber_card = ctk.CTkFrame(results_frame, fg_color="#1e293b")
        qber_card.pack(fill="x", padx=15, pady=5)

        self.qber_label = ctk.CTkLabel(
            qber_card,
            text="QBER (Quantum Bit Error Rate): 0.00%",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f8fafc"
        )
        self.qber_label.pack(anchor="w", padx=12, pady=(8, 2))

        self.qber_bar = ctk.CTkProgressBar(qber_card)
        self.qber_bar.set(0.0)
        self.qber_bar.configure(progress_color="#10b981")
        self.qber_bar.pack(fill="x", padx=12, pady=(0, 6))

        ctk.CTkLabel(
            qber_card,
            text="Theoretical BB84 Abort Threshold: 11.00%",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8"
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # Multi-metrics row
        metrics_row = ctk.CTkFrame(results_frame, fg_color="#1e293b")
        metrics_row.pack(fill="x", padx=15, pady=5)
        metrics_row.grid_columnconfigure((0, 1, 2), weight=1)

        self.metric_loss = ctk.CTkLabel(metrics_row, text="Photon Loss: --%", font=ctk.CTkFont(size=12))
        self.metric_loss.grid(row=0, column=0, padx=8, pady=8)

        self.metric_snr = ctk.CTkLabel(metrics_row, text="SNR: -- dB", font=ctk.CTkFont(size=12))
        self.metric_snr.grid(row=0, column=1, padx=8, pady=8)

        self.metric_key = ctk.CTkLabel(metrics_row, text="Key Bits: -- bits", font=ctk.CTkFont(size=12))
        self.metric_key.grid(row=0, column=2, padx=8, pady=8)

        # AI Verdict Box
        ai_card = ctk.CTkFrame(results_frame, fg_color="#1e293b")
        ai_card.pack(fill="x", padx=15, pady=8)

        self.ai_threat_badge = ctk.CTkLabel(
            ai_card,
            text="AI VERDICT: PENDING DISPATCH",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#94a3b8"
        )
        self.ai_threat_badge.pack(anchor="w", padx=12, pady=(10, 4))

        self.ai_location_label = ctk.CTkLabel(
            ai_card,
            text="Pinpointed Conduit: None",
            font=ctk.CTkFont(size=12),
            text_color="#f8fafc"
        )
        self.ai_location_label.pack(anchor="w", padx=12, pady=2)

        self.ai_action_box = ctk.CTkTextbox(ai_card, height=65, font=ctk.CTkFont(size=11))
        self.ai_action_box.insert("0.0", "System waiting for medical data transmission.")
        self.ai_action_box.configure(state="disabled")
        self.ai_action_box.pack(fill="x", padx=12, pady=(6, 10))

        # Bottom Frame: Live Execution Log
        log_frame = ctk.CTkFrame(tab)
        log_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(
            log_frame,
            text="3. LIVE QUANTUM SOC TELEMETRY LOGS",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#38bdf8"
        ).pack(anchor="w", padx=12, pady=(8, 4))

        self.log_text = ctk.CTkTextbox(log_frame, height=140, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_text.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        self._append_log("[INIT] Hospital Quantum Cryptography & AI Security SOC initialized.")
        self._append_log("[INFO] Ready to transmit confidential patient records.")

    def _on_route_change(self, choice):
        path = self.network.get_shortest_path(choice, "ServerRoom")
        self._append_log(f"[ROUTING] Updated default optical path: {' -> '.join(path)}")

    def _on_threat_change(self, choice):
        pass

    def _append_log(self, text: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _trigger_transmission(self):
        self.btn_transmit.configure(state="disabled", text="⚡ SIMULATING QUANTUM CHANNELS...")
        threading.Thread(target=self._run_transmission_thread, daemon=True).start()

    def _run_transmission_thread(self):
        try:
            source = self.src_combo.get()
            destination = self.dst_combo.get()
            payload = self.payload_entry.get()

            # Parse threat
            threat_str = self.threat_combo.get()
            if "EAVESDROPPING" in threat_str:
                threat_type = "EAVESDROPPING"
            elif "FIBER_TAMPER" in threat_str:
                threat_type = "FIBER_TAMPER"
            elif "HARDWARE_FAULT" in threat_str:
                threat_type = "HARDWARE_FAULT"
            else:
                threat_type = "NORMAL"

            # Parse link
            link_raw = self.link_combo.get()
            target_link = link_raw.split()[0] if threat_type != "NORMAL" else None

            self._append_log("-" * 65)
            self._append_log(f"[DISPATCH] Transmitting payload from [{source}] to [{destination}]")
            if target_link:
                loc = LINK_MAP[target_link].physical_location
                self._append_log(f"[ATTACK] Injected threat: '{threat_type}' on Link [{target_link}] ({loc})")
            else:
                self._append_log("[STATUS] Operating under normal ambient noise baseline.")

            # Run Qiskit BB84 simulation
            t_start = time.time()
            telemetry = self.network.scan_network_telemetry(
                attack_link_id=target_link,
                threat_type=threat_type,
                fast_mode=False
            )
            sim_time = time.time() - t_start

            # Run ML inference
            analysis = self.ai.analyze_network_telemetry(telemetry)

            # Determine focal link for UI
            path = self.network.get_shortest_path(source, destination)
            links_in_path = self.network.get_path_links(path)
            focus_link = target_link if target_link else links_in_path[0].link_id

            qber = telemetry[f"{focus_link}_qber"]
            loss = telemetry[f"{focus_link}_loss"]
            snr = telemetry[f"{focus_link}_snr"]
            key_len = telemetry[f"{focus_link}_key_len"]

            # Update UI on main thread
            self.after(0, self._update_ui_post_transmission, qber, loss, snr, key_len, analysis, focus_link, sim_time, threat_type)

        except Exception as e:
            self._append_log(f"[ERROR] Simulation error: {str(e)}")
            self.after(0, lambda: self.btn_transmit.configure(state="normal", text="🚀 TRANSMIT WITH QUANTUM SECURE KEY"))

    def _update_ui_post_transmission(self, qber, loss, snr, key_len, analysis, focus_link, sim_time, threat_type):
        # Update metrics
        self.qber_label.configure(text=f"QBER (Quantum Bit Error Rate): {qber:.2%}")
        self.qber_bar.set(min(1.0, qber * 2.5))  # scale for visual clarity
        if qber > 0.11:
            self.qber_bar.configure(progress_color="#ef4444")  # Red alert
            self.qber_label.configure(text_color="#ef4444")
        else:
            self.qber_bar.configure(progress_color="#10b981")  # Green safe
            self.qber_label.configure(text_color="#10b981")

        self.metric_loss.configure(text=f"Photon Loss: {loss:.1%}")
        self.metric_snr.configure(text=f"SNR: {snr:.1f} dB")
        self.metric_key.configure(text=f"Key Yield: {key_len} bits")

        # Update AI Verdict
        pred_threat = analysis["predicted_threat"]
        pred_link = analysis["predicted_link"]
        pred_loc = analysis["physical_location"]
        threat_conf = analysis["threat_confidence"]
        link_conf = analysis["link_confidence"]

        if pred_threat == "NORMAL":
            self.ai_threat_badge.configure(
                text=f"AI VERDICT: NORMAL (Confidence: {threat_conf:.1f}%)",
                text_color="#10b981"
            )
        elif pred_threat == "EAVESDROPPING":
            self.ai_threat_badge.configure(
                text=f"AI VERDICT: ⚠️ DATA THEFT / EAVESDROPPING ({threat_conf:.1f}%)",
                text_color="#ef4444"
            )
        elif pred_threat == "FIBER_TAMPER":
            self.ai_threat_badge.configure(
                text=f"AI VERDICT: ⚠️ PHYSICAL FIBER TAMPERING ({threat_conf:.1f}%)",
                text_color="#f59e0b"
            )
        else:
            self.ai_threat_badge.configure(
                text=f"AI VERDICT: ⚠️ HARDWARE ANOMALY ({threat_conf:.1f}%)",
                text_color="#eab308"
            )

        self.ai_location_label.configure(
            text=f"Pinpointed Location: [{pred_link}] {pred_loc} ({link_conf:.1f}%)"
        )

        self.ai_action_box.configure(state="normal")
        self.ai_action_box.delete("0.0", "end")
        self.ai_action_box.insert("0.0", analysis["recommended_action"])
        self.ai_action_box.configure(state="disabled")

        self._append_log(f"[VERDICT] Threat: {pred_threat} | Location: {pred_loc}")
        self._append_log(f"[ACTION] {analysis['recommended_action']}")
        self._append_log(f"[PERF] Qiskit Aer circuit simulation completed in {sim_time:.2f}s.")

        # Re-enable button
        self.btn_transmit.configure(state="normal", text="🚀 TRANSMIT WITH QUANTUM SECURE KEY")

        # Refresh map tab
        highlight = pred_link if pred_threat != "NORMAL" else None
        map_path = f"incident_{threat_type.lower()}_map.png"
        self.network.visualize_topology(save_path=map_path, highlight_link=highlight)
        self._load_topology_image(map_path)

    # =========================================================================
    # TAB 2: Network Topology
    # =========================================================================
    def _populate_topology_tab(self):
        tab = self.tab_topo
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        top_bar = ctk.CTkFrame(tab)
        top_bar.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(
            top_bar,
            text="HOSPITAL OPTICAL MESH TOPOLOGY & INCIDENT LOCALIZATION MAP",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#38bdf8"
        ).pack(side="left", padx=15, pady=8)

        btn_reload = ctk.CTkButton(
            top_bar,
            text="🔄 Reload Image",
            width=120,
            command=self._refresh_topology_images
        )
        btn_reload.pack(side="right", padx=15, pady=8)

        # Image Container
        self.topo_img_label = ctk.CTkLabel(tab, text="Loading Network Topology...")
        self.topo_img_label.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self._refresh_topology_images()

    def _load_topology_image(self, path: str):
        if not os.path.exists(path):
            path = "hospital_network_map.png"
        if os.path.exists(path):
            try:
                pil_img = Image.open(path)
                # Resize for display
                ctk_img = ctk.CTkImage(dark_image=pil_img, light_image=pil_img, size=(820, 480))
                self.topo_img_label.configure(image=ctk_img, text="")
            except Exception as e:
                self.topo_img_label.configure(text=f"Failed to display image: {e}")

    def _refresh_topology_images(self):
        map_path = "hospital_network_map.png"
        if not os.path.exists(map_path):
            self.network.visualize_topology(map_path)
        self._load_topology_image(map_path)

    # =========================================================================
    # TAB 3: Qiskit Circuit Inspector
    # =========================================================================
    def _populate_circuit_tab(self):
        tab = self.tab_circ
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(tab)
        header.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(
            header,
            text="QISKIT 2.5 DYNAMIC QUANTUM CIRCUIT (BB84 with Eve Intercept-Resend)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#38bdf8"
        ).pack(side="left", padx=15, pady=8)

        # Circuit ASCII text box
        self.circuit_text = ctk.CTkTextbox(tab, font=ctk.CTkFont(family="Consolas", size=12))
        self.circuit_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # Load Circuit
        sim = BB84Simulator()
        qc = sim.build_sample_circuit()
        circ_draw = qc.draw(output='text')
        self.circuit_text.insert("0.0", str(circ_draw))
        self.circuit_text.configure(state="disabled")

    # =========================================================================
    # TAB 4: ML Diagnostics
    # =========================================================================
    def _populate_ml_tab(self):
        tab = self.tab_ml
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(tab)
        header.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(
            header,
            text="RANDOM FOREST EVALUATION: CONFUSION MATRIX & GINI FEATURE IMPORTANCE",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#38bdf8"
        ).pack(side="left", padx=15, pady=8)

        self.ml_img_label = ctk.CTkLabel(tab, text="Loading ML Diagnostics...")
        self.ml_img_label.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self._load_ml_report_image()

    def _load_ml_report_image(self):
        path = "ml_evaluation_report.png"
        if os.path.exists(path):
            try:
                pil_img = Image.open(path)
                ctk_img = ctk.CTkImage(dark_image=pil_img, light_image=pil_img, size=(880, 420))
                self.ml_img_label.configure(image=ctk_img, text="")
            except Exception as e:
                self.ml_img_label.configure(text=f"Failed to load ML report: {e}")

    # =========================================================================
    # Sidebar Actions
    # =========================================================================
    def _run_quick_audit(self):
        self._append_log("\n[AUDIT] Starting automated 3-stage security test...")
        # Switch to Transmission tab
        self.tabview.set("⚡ Live Transmission & SOC")
        self.threat_combo.set("EAVESDROPPING (Data Theft / Eve Intercept-Resend)")
        self._trigger_transmission()

    def _trigger_retrain(self):
        self._append_log("\n[AI] Retraining Random Forest models in background thread...")
        threading.Thread(target=self._retrain_thread, daemon=True).start()

    def _retrain_thread(self):
        try:
            self.ai.train_and_evaluate()
            self._append_log("[AI] Retraining complete! Accuracy and feature importances updated.")
            self.after(0, self._load_ml_report_image)
        except Exception as e:
            self._append_log(f"[AI ERROR] Retraining failed: {e}")


def launch_gui():
    app = HospitalQuantumGUI()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
