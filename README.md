# Quantum Hospital Network Defense: QKD (BB84) & Classical Machine Learning Intrusion Localization

A hybrid cybersecurity system combining **Quantum Key Distribution (QKD via Qiskit 2.x)** with **Classical Machine Learning (Random Forest)** to monitor a hospital optical fiber network transporting confidential medical records (EHR, vitals, MRI scans). 

The system leverages **Quantum Bit Error Rate (QBER)** and optical telemetry to detect data theft, physical fiber tapping, and hardware corruption, while using a classical Random Forest ensemble to **pinpoint the exact physical hospital conduit/location** where the incident occurs.

---

## 🏛️ System Architecture

```
                    ┌────────────────────────┐
                    │  Hospital Optical Mesh │
                    │ (ICU, Radiology, EHR)  │
                    └───────────┬────────────┘
                                │
                 Optical Fiber Pulse Transmissions
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
┌───────────────────────────────┐       ┌───────────────────────────────┐
│     Quantum Physical Layer    │       │     Classical Network Layer   │
│  - Qiskit BB84 Protocol       │       │  - Packet Routing (NetworkX)  │
│  - Basis Sifting (Z vs X)     │       │  - Optical Switching & Bypasses│
│  - Quantum State Collapse     │       │  - Medical Record OTP Cipher  │
│  - Real-time QBER & Loss Yield│       └───────────────┬───────────────┘
└───────────────┬───────────────┘                       │
                │                                       │
                └───────────────┬───────────────────────┘
                                │ Live Telemetry Vector
                                ▼
            ┌───────────────────────────────────────────────┐
            │   Classical Random Forest ML Engine           │
            │   - Threat Classifier: 93.39% Accuracy        │
            │   - Exact Physical Localization: 97.86% Acc   │
            │   - Gini Feature Importance Diagnostics       │
            └───────────────────┬───────────────────────────┘
                                │
                                ▼
            ┌───────────────────────────────────────────────┐
            │   Hospital Security Operations Center (SOC)   │
            │   - Pinpoints Exact Physical Conduit/Wing     │
            │   - Aborts Compromised QKD Key Generation     │
            │   - Dynamically Reroutes Optical Data Flow    │
            │   - Dispatches Physical Security to Conduit   │
            └───────────────────────────────────────────────┘
```

---

## 🔬 Core Quantum Concepts

### 1. BB84 Quantum Key Distribution Protocol
* **Alice Preparation**: Encodes random classical bits $b \in \{0, 1\}$ into photon polarization states across two mutually unbiased bases:
  * **Computational ($Z$) Basis**: $|0\rangle$, $|1\rangle$
  * **Hadamard ($X$) Basis**: $|+\rangle = \frac{|0\rangle + |1\rangle}{\sqrt{2}}$, $|-\rangle = \frac{|0\rangle - |1\rangle}{\sqrt{2}}$
* **Eve Eavesdropping (Intercept-Resend Attack)**:
  * By the **No-Cloning Theorem**, Eve cannot copy unknown quantum states.
  * When Eve intercepts a qubit and measures in basis $B_E$, she collapses the wavefunction.
  * If $B_E \ne B_A$ (50% probability), Bob receives an eigenstate of $B_E$. When Bob measures in matching basis $B_B = B_A$, he gets an error with 50% probability.
  * **Theoretical error introduced by Eve**: $50\% \times 50\% = \mathbf{25\%}$ error rate.
* **QBER (Quantum Bit Error Rate)**:
  $$\text{QBER} = \frac{\text{Number of Erroneous Sifted Bits}}{\text{Total Compared Sifted Bits}}$$
  * **Baseline Channel Noise**: $\text{QBER} \approx 0\% - 3\%$
  * **Shor-Preskill Security Threshold**: $\mathbf{11.00\%}$
  * If $\text{QBER} > 11\%$, the key exchange is aborted immediately—Eve obtains 0 bits of information.

### 2. Optical Fiber Telemetry Metrics
Each physical link $(u, v)$ is monitored with:
* `qber`: Quantum Bit Error Rate
* `loss_rate`: Photon loss / absorption due to attenuation or fiber tapping
* `snr_db`: Detector Signal-to-Noise Ratio (dB)
* `key_len`: Yield of sifted secret key bits
* `latency_ms`: Propagation delay across fiber distance

---

## 🏥 Hospital Network Topology & Monitored Links

| Link ID | Source | Target | Physical Conduit Location | Length |
| :--- | :--- | :--- | :--- | :--- |
| `L_ICU_SW1` | ICU | CoreSwitch_1 | **Conduit Wing A - Basement** | 0.4 km |
| `L_PHARM_SW1`| Pharmacy | CoreSwitch_1 | **Service Tunnel - South** | 0.3 km |
| `L_RAD_SW2` | Radiology | CoreSwitch_2 | **Ceiling Plenum - Floor 2** | 0.6 km |
| `L_ADM_SW2` | Admin | CoreSwitch_2 | **Riser Shaft - East Wing** | 0.5 km |
| `L_SW1_SW2` | CoreSwitch_1 | CoreSwitch_2 | **Inter-Building Fiber Backbone** | 1.2 km |
| `L_SW1_SRV` | CoreSwitch_1 | ServerRoom | **Secure Data Center Duct A** | 0.2 km |
| `L_SW2_SRV` | CoreSwitch_2 | ServerRoom | **Secure Data Center Duct B** | 0.2 km |

---

## 🤖 Classical Machine Learning Engine (Random Forest)

The system deploys a high-performance **Random Forest Ensemble** with:
1. **Threat Classifier** (Detects `NORMAL`, `EAVESDROPPING`, `FIBER_TAMPER`, `HARDWARE_FAULT`):
   * **Accuracy: 93.39%**
2. **Physical Localization Engine** (Pinpoints the exact link and physical conduit):
   * **Accuracy: 97.86%**

### Top Telemetry Predictors (Gini Importance):
1. `<link>_qber`: Primary trigger for Eavesdropping / Intercept-Resend detection.
2. `<link>_loss`: Primary indicator for Physical Fiber Taps & Bends.
3. `<link>_snr` & `<link>_key_len`: Differentiators for hardware transceiver degradation.

---

## 🚀 Quickstart & Usage

### 1. Launch the Unified Visual Desktop GUI Dashboard
Launch the unified CustomTkinter visual dashboard (or double-click `launch_soc_gui.bat`):
```bash
python main.py gui
```
Or directly:
```bash
python gui_app.py
```

### 2. Run the Terminal SOC Simulation
Runs all 4 scenarios in the terminal:
```bash
python main.py demo
```

### 2. Inspect the Qiskit Quantum Circuit
Displays the dynamic Qiskit circuit with mid-circuit measurement, quantum reset, and conditional gates:
```bash
python main.py circuit
```

### 3. Inject a Custom Attack Scenario
Simulate Eve intercepting patient data on a specific hospital link:
```bash
python main.py inject --src ICU --dst ServerRoom --link L_ICU_SW1 --type EAVESDROPPING
```
Simulate a physical fiber tap at Radiology:
```bash
python main.py inject --src Radiology --dst ServerRoom --link L_RAD_SW2 --type FIBER_TAMPER
```

### 4. Retrain Models or Regenerate Dataset
```bash
python main.py generate-data --samples 2800
python main.py train
```

---

## 📁 Repository Structure

```

├── config.py                 # Hospital nodes, physical fiber links, QKD parameters
├── qkd_simulator.py          # Qiskit 2.x dynamic circuits for BB84, Aer simulator, QBER
├── network_topology.py       # NetworkX hospital graph, routing, link telemetry scanner
├── dataset_generator.py      # Generates balanced multi-link telemetry dataset
├── ml_detector.py            # Pure Random Forest implementation (Threat + Localization)
├── demo_monitor.py           # Real-time Hospital SOC incident response simulation
├── main.py                   # Unified CLI orchestrator
├── ml_evaluation_report.png  # Confusion matrices & Gini feature importance charts
├── hospital_network_map.png  # Visual hospital fiber network topology
└── README.md                 # Project documentation
```
