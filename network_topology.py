"""
Hospital Network Topology Model using NetworkX.
Simulates optical links, multi-hop patient data transport, 
link-by-link QKD telemetry aggregation, and anomaly injection.
"""

from typing import Dict, List, Optional, Tuple, Any
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from config import HOSPITAL_NODES, NETWORK_LINKS, LINK_MAP, NetworkLink, THREAT_TYPES
from qkd_simulator import BB84Simulator, QKDTelemetry


class HospitalNetwork:
    def __init__(self):
        self.graph = nx.Graph()
        self.qkd_sim = BB84Simulator()
        self._build_topology()

    def _build_topology(self):
        for node in HOSPITAL_NODES:
            self.graph.add_node(node)

        for link in NETWORK_LINKS:
            self.graph.add_edge(
                link.source,
                link.target,
                link_id=link.link_id,
                location=link.physical_location,
                length_km=link.fiber_length_km,
                weight=link.fiber_length_km
            )

    def get_shortest_path(self, source: str, destination: str) -> List[str]:
        """Calculates shortest optical routing path between hospital wings."""
        return nx.shortest_path(self.graph, source=source, target=destination, weight="weight")

    def get_path_links(self, path: List[str]) -> List[NetworkLink]:
        """Retrieves ordered list of physical links along a path."""
        links = []
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge_data = self.graph.get_edge_data(u, v)
            link_id = edge_data["link_id"]
            links.append(LINK_MAP[link_id])
        return links

    def find_alternative_path(self, source: str, destination: str, compromised_link_id: str) -> Optional[List[str]]:
        """
        Dynamically finds an alternative optical route bypassing a compromised link.
        """
        bad_link = LINK_MAP.get(compromised_link_id)
        if not bad_link:
            return self.get_shortest_path(source, destination)

        # Create temporary subgraph without the compromised edge
        sub_g = self.graph.copy()
        if sub_g.has_edge(bad_link.source, bad_link.target):
            sub_g.remove_edge(bad_link.source, bad_link.target)

        try:
            return nx.shortest_path(sub_g, source=source, target=destination, weight="weight")
        except nx.NetworkXNoPath:
            return None

    def scan_network_telemetry(
        self,
        attack_link_id: Optional[str] = None,
        threat_type: str = "NORMAL",
        fast_mode: bool = True
    ) -> Dict[str, Any]:
        """
        Simulates network-wide QKD heartbeat across all fiber optic links.
        If attack_link_id is specified, injects the requested threat on that link.
        
        Returns a flat dictionary containing all telemetry features plus ground-truth labels.
        """
        telemetry_record: Dict[str, Any] = {}

        for link in NETWORK_LINKS:
            is_attacked = (attack_link_id == link.link_id)

            eve_prob = 0.0
            tamper_loss = 0.0
            noise_prob = 0.015  # baseline physical noise

            if is_attacked:
                if threat_type == "EAVESDROPPING":
                    eve_prob = 0.85
                elif threat_type == "FIBER_TAMPER":
                    tamper_loss = 0.65
                elif threat_type == "HARDWARE_FAULT":
                    noise_prob = 0.16

            t = self.qkd_sim.simulate_link_transmission(
                num_photons=250,
                fiber_length_km=link.fiber_length_km,
                eve_attack_prob=eve_prob,
                tamper_loss_prob=tamper_loss,
                channel_noise_prob=noise_prob,
                use_aer=not fast_mode
            )

            # Store per-link telemetry
            prefix = link.link_id
            telemetry_record[f"{prefix}_qber"] = t.qber
            telemetry_record[f"{prefix}_loss"] = t.loss_rate
            telemetry_record[f"{prefix}_key_len"] = t.secret_key_len
            telemetry_record[f"{prefix}_snr"] = t.snr_db
            telemetry_record[f"{prefix}_latency"] = t.latency_ms
            telemetry_record[f"{prefix}_secure"] = 1 if t.is_secure else 0

        # Global Network Summary Indicators (Enables high-confidence Normal classification)
        all_qbers = [telemetry_record[f"{l.link_id}_qber"] for l in NETWORK_LINKS]
        all_losses = [telemetry_record[f"{l.link_id}_loss"] for l in NETWORK_LINKS]
        all_snrs = [telemetry_record[f"{l.link_id}_snr"] for l in NETWORK_LINKS]

        telemetry_record["net_max_qber"] = round(float(max(all_qbers)), 4)
        telemetry_record["net_mean_qber"] = round(float(sum(all_qbers) / len(all_qbers)), 4)
        telemetry_record["net_max_loss"] = round(float(max(all_losses)), 4)
        telemetry_record["net_min_snr"] = round(float(min(all_snrs)), 2)
        telemetry_record["net_alarm_count"] = int(
            sum(q > 0.11 for q in all_qbers) + sum(loss > 0.45 for loss in all_losses)
        )

        # Ground-truth targets
        telemetry_record["target_threat"] = threat_type if attack_link_id else "NORMAL"
        telemetry_record["target_link"] = attack_link_id if (attack_link_id and threat_type != "NORMAL") else "NONE"
        telemetry_record["target_location"] = (
            LINK_MAP[attack_link_id].physical_location 
            if (attack_link_id and attack_link_id in LINK_MAP and threat_type != "NORMAL") 
            else "NONE"
        )

        return telemetry_record

    def visualize_topology(self, save_path: str = "hospital_network_map.png", highlight_link: Optional[str] = None):
        """
        Renders hospital topology with node positions and link details.
        """
        pos = {
            "ICU": (-2.0, 1.5),
            "Pharmacy": (-2.0, -1.5),
            "CoreSwitch_1": (-0.8, 0.0),
            "ServerRoom": (0.0, 0.0),
            "CoreSwitch_2": (0.8, 0.0),
            "Radiology": (2.0, 1.5),
            "Admin": (2.0, -1.5),
        }

        fig, ax = plt.subplots(figsize=(12, 7))
        fig.patch.set_facecolor('#0f172a')
        ax.set_facecolor('#0f172a')

        # Node colors
        node_colors = []
        for n in self.graph.nodes():
            if "Server" in n:
                node_colors.append('#38bdf8')   # Cyan for Server
            elif "Switch" in n:
                node_colors.append('#fbbf24')   # Amber for Switches
            else:
                node_colors.append('#34d399')   # Green for Departments

        # Draw nodes
        nx.draw_networkx_nodes(
            self.graph, pos, ax=ax,
            node_color=node_colors,
            node_size=2800,
            edgecolors='#f8fafc',
            linewidths=2.0
        )

        # Draw edges
        edge_colors = []
        edge_widths = []
        for u, v in self.graph.edges():
            edge_id = self.graph[u][v]["link_id"]
            if highlight_link and edge_id == highlight_link:
                edge_colors.append('#ef4444')  # Red alert
                edge_widths.append(4.5)
            else:
                edge_colors.append('#94a3b8')  # Neutral slate
                edge_widths.append(2.0)

        nx.draw_networkx_edges(
            self.graph, pos, ax=ax,
            edge_color=edge_colors,
            width=edge_widths,
            style='solid'
        )

        # Node labels
        labels = {n: n for n in self.graph.nodes()}
        nx.draw_networkx_labels(
            self.graph, pos, labels=labels, ax=ax,
            font_size=10, font_weight='bold', font_color='#0f172a'
        )

        # Edge labels: Link IDs & Lengths
        edge_labels = {
            (u, v): f"{d['link_id']}\n({d['length_km']} km)"
            for u, v, d in self.graph.edges(data=True)
        }
        nx.draw_networkx_edge_labels(
            self.graph, pos, edge_labels=edge_labels, ax=ax,
            font_color='#cbd5e1', font_size=8,
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#1e293b', edgecolor='#475569')
        )

        ax.set_title(
            "HOSPITAL QUANTUM CRYPTOGRAPHY NETWORK TOPOLOGY",
            color='#f8fafc', fontsize=14, fontweight='bold', pad=20
        )
        ax.axis('off')
        plt.tight_layout()
        plt.savefig(save_path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close(fig)
        return save_path


if __name__ == "__main__":
    net = HospitalNetwork()
    print("Hospital Network Graph Initialized!")
    print(f"Nodes: {list(net.graph.nodes)}")
    print(f"Edges: {list(net.graph.edges)}")

    # Test routing
    path = net.get_shortest_path("ICU", "ServerRoom")
    print(f"\nDefault Patient Data Path (ICU -> ServerRoom): {' -> '.join(path)}")
    links = net.get_path_links(path)
    print("Links traversed:")
    for l in links:
        print(f" - [{l.link_id}] {l.source} -> {l.target} | Location: '{l.physical_location}'")

    # Test rerouting
    alt_path = net.find_alternative_path("ICU", "ServerRoom", compromised_link_id="L_SW1_SRV")
    print(f"\nRerouted Path when L_SW1_SRV is severed: {' -> '.join(alt_path)}")

    # Generate Topology Map
    map_file = net.visualize_topology()
    print(f"\nTopology map saved to {map_file}")
