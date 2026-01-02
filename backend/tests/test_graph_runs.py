import unittest


class GraphRunTest(unittest.TestCase):
    def _run_graph(self, data):
        from photonflow.core import Graph, SimConfig

        graph = Graph.from_dict(data, validate=True)
        graph.compile()
        outputs = graph.run(SimConfig(fs=1e10, duration_s=1e-8, device="cpu"))
        self.assertTrue(outputs)

    def test_pm_chain(self):
        data = {
            "version": "0.1",
            "sim": {
                "backend": "torch",
                "device": "cpu",
                "fs": 1e10,
                "oversample": 4,
                "seed": 0,
                "window": "hann",
                "duration_s": 1e-8,
            },
            "nodes": [
                {"id": "laser1", "type": "Laser", "params": {"power_dbm": 0.0}},
                {"id": "rf1", "type": "RFSource", "params": {"freq_hz": 1e9, "amplitude": 1.0}},
                {"id": "pm1", "type": "PM", "params": {"Vpi": 4.0}},
                {"id": "pd1", "type": "PD", "params": {"responsivity": 1.0}},
            ],
            "edges": [
                {"src": "laser1", "src_port": "opt_out", "dst": "pm1", "dst_port": "opt_in"},
                {"src": "rf1", "src_port": "elec_out", "dst": "pm1", "dst_port": "elec_in"},
                {"src": "pm1", "src_port": "opt_out", "dst": "pd1", "dst_port": "opt_in"},
            ],
            "outputs": {
                "osa": {"node": "pm1", "port": "opt_out", "kind": "osa"},
                "esa": {"node": "pd1", "port": "elec_out", "kind": "esa"},
            },
        }
        self._run_graph(data)

    def test_mzm_composite_chain(self):
        data = {
            "version": "0.1",
            "sim": {
                "backend": "torch",
                "device": "cpu",
                "fs": 1e10,
                "oversample": 4,
                "seed": 0,
                "window": "hann",
                "duration_s": 1e-8,
            },
            "nodes": [
                {"id": "laser1", "type": "Laser", "params": {"power_dbm": 0.0}},
                {"id": "rf1", "type": "RFSource", "params": {"freq_hz": 1e9, "amplitude": 1.0}},
                {"id": "mzm1", "type": "MZMComposite", "params": {"Vpi": 4.0}},
                {"id": "pd1", "type": "PD", "params": {"responsivity": 1.0}},
            ],
            "edges": [
                {"src": "laser1", "src_port": "opt_out", "dst": "mzm1", "dst_port": "opt_in"},
                {"src": "rf1", "src_port": "elec_out", "dst": "mzm1", "dst_port": "elec_in"},
                {"src": "mzm1", "src_port": "opt_out", "dst": "pd1", "dst_port": "opt_in"},
            ],
            "outputs": {
                "osa": {"node": "mzm1", "port": "opt_out", "kind": "osa"},
                "esa": {"node": "pd1", "port": "elec_out", "kind": "esa"},
            },
        }
        self._run_graph(data)

    def test_dpmzm_composite_chain(self):
        data = {
            "version": "0.1",
            "sim": {
                "backend": "torch",
                "device": "cpu",
                "fs": 1e10,
                "oversample": 4,
                "seed": 0,
                "window": "hann",
                "duration_s": 1e-8,
            },
            "nodes": [
                {"id": "laser1", "type": "Laser", "params": {"power_dbm": 0.0}},
                {"id": "rf1", "type": "RFSource", "params": {"freq_hz": 1e9, "amplitude": 1.0}},
                {"id": "rf2", "type": "RFSource", "params": {"freq_hz": 1e9, "amplitude": 1.0, "phase": 1.57079632679}},
                {"id": "dpmzm1", "type": "DPMZMComposite", "params": {"Vpi": 4.0}},
                {"id": "pd1", "type": "PD", "params": {"responsivity": 1.0}},
            ],
            "edges": [
                {"src": "laser1", "src_port": "opt_out", "dst": "dpmzm1", "dst_port": "opt_in"},
                {"src": "rf1", "src_port": "elec_out", "dst": "dpmzm1", "dst_port": "elec_i"},
                {"src": "rf2", "src_port": "elec_out", "dst": "dpmzm1", "dst_port": "elec_q"},
                {"src": "dpmzm1", "src_port": "opt_out", "dst": "pd1", "dst_port": "opt_in"},
            ],
            "outputs": {
                "osa": {"node": "dpmzm1", "port": "opt_out", "kind": "osa"},
                "esa": {"node": "pd1", "port": "elec_out", "kind": "esa"},
            },
        }
        self._run_graph(data)


if __name__ == "__main__":
    unittest.main()
