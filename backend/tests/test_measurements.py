import unittest


class MeasurementTest(unittest.TestCase):
    def test_spectrum_and_time_outputs(self):
        from photonflow.server.sim_runner import run_graph_job

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
                "osa": {
                    "node": "pm1",
                    "port": "opt_out",
                    "kind": "osa",
                    "params": {"include_power": True},
                },
                "esa": {"node": "pd1", "port": "elec_out", "kind": "time"},
            },
        }

        result = run_graph_job(data, validate=True, max_points=512)
        osa = result.get("osa", {})
        esa = result.get("esa", {})
        self.assertEqual(osa.get("kind"), "osa")
        self.assertIn("power_db", osa)
        self.assertIn("power", osa)
        self.assertGreater(len(osa.get("freq", [])), 0)
        self.assertEqual(esa.get("kind"), "time")
        self.assertIn("real", esa)
        self.assertIn("t", esa)

    def test_chunked_measurement_outputs(self):
        from photonflow.server.sim_runner import run_graph_job

        data = {
            "version": "0.1",
            "sim": {
                "backend": "torch",
                "device": "cpu",
                "fs": 1e9,
                "oversample": 4,
                "seed": 0,
                "window": "hann",
                "duration_s": 1e-6,
                "chunk": 256,
            },
            "nodes": [
                {"id": "rf1", "type": "RFSource", "params": {"freq_hz": 1e7, "amplitude": 1.0}},
            ],
            "edges": [],
            "outputs": {
                "esa": {"node": "rf1", "port": "elec_out", "kind": "esa"},
                "osa": {"node": "rf1", "port": "elec_out", "kind": "time"},
            },
        }

        result = run_graph_job(data, validate=True, max_points=256)
        esa = result.get("esa", {})
        time_out = result.get("osa", {})
        self.assertEqual(esa.get("kind"), "esa")
        self.assertGreater(len(esa.get("freq", [])), 0)
        self.assertEqual(time_out.get("kind"), "time")
        self.assertGreater(len(time_out.get("t", [])), 0)

    def test_composite_output_mapping(self):
        from photonflow.server.sim_runner import run_graph_job

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
            ],
            "edges": [
                {"src": "laser1", "src_port": "opt_out", "dst": "mzm1", "dst_port": "opt_in"},
                {"src": "rf1", "src_port": "elec_out", "dst": "mzm1", "dst_port": "elec_in"},
            ],
            "outputs": {
                "osa": {"node": "mzm1", "port": "opt_out", "kind": "osa"},
                "esa": {"node": "rf1", "port": "elec_out", "kind": "esa"},
            },
        }

        result = run_graph_job(data, validate=True, max_points=128)
        osa = result.get("osa", {})
        self.assertEqual(osa.get("kind"), "osa")
        self.assertGreater(len(osa.get("freq", [])), 0)


if __name__ == "__main__":
    unittest.main()
