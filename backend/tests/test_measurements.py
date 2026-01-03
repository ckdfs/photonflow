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
                {"id": "osa1", "type": "OSAProbe"},
                {"id": "pd1", "type": "PD", "params": {"responsivity": 1.0}},
                {"id": "scope1", "type": "ScopeProbe"},
            ],
            "edges": [
                {"src": "laser1", "src_port": "opt_out", "dst": "pm1", "dst_port": "opt_in"},
                {"src": "rf1", "src_port": "elec_out", "dst": "pm1", "dst_port": "elec_in"},
                {"src": "pm1", "src_port": "opt_out", "dst": "pd1", "dst_port": "opt_in"},
                {"src": "pm1", "src_port": "opt_out", "dst": "osa1", "dst_port": "opt_in"},
                {"src": "pd1", "src_port": "elec_out", "dst": "scope1", "dst_port": "elec_in"},
            ],
            "outputs": {
                "extra": [
                    {
                        "node": "osa1",
                        "port": "opt_in",
                        "kind": "osa",
                        "params": {"include_power": True},
                    },
                    {"node": "scope1", "port": "elec_in", "kind": "time"},
                ]
            },
        }

        result = run_graph_job(data, validate=True, max_points=512)
        extra = result.get("extra", [])
        osa = extra[0] if len(extra) > 0 else {}
        esa = extra[1] if len(extra) > 1 else {}
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
                {"id": "esplit1", "type": "ElecSplitter"},
                {"id": "esa1", "type": "ESAProbe"},
                {"id": "scope1", "type": "ScopeProbe"},
            ],
            "edges": [],
            "outputs": {
                "extra": [
                    {"node": "esa1", "port": "elec_in", "kind": "esa"},
                    {"node": "scope1", "port": "elec_in", "kind": "time"},
                ]
            },
        }
        data["edges"] = [
            {"src": "rf1", "src_port": "elec_out", "dst": "esplit1", "dst_port": "elec_in"},
            {"src": "esplit1", "src_port": "elec_out1", "dst": "esa1", "dst_port": "elec_in"},
            {"src": "esplit1", "src_port": "elec_out2", "dst": "scope1", "dst_port": "elec_in"},
        ]

        result = run_graph_job(data, validate=True, max_points=256)
        extra = result.get("extra", [])
        esa = extra[0] if len(extra) > 0 else {}
        time_out = extra[1] if len(extra) > 1 else {}
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
                {"id": "osa1", "type": "OSAProbe"},
                {"id": "esa1", "type": "ESAProbe"},
            ],
            "edges": [
                {"src": "laser1", "src_port": "opt_out", "dst": "mzm1", "dst_port": "opt_in"},
                {"src": "rf1", "src_port": "elec_out", "dst": "mzm1", "dst_port": "elec_in"},
                {"src": "mzm1", "src_port": "opt_out", "dst": "osa1", "dst_port": "opt_in"},
                {"src": "rf1", "src_port": "elec_out", "dst": "esa1", "dst_port": "elec_in"},
            ],
            "outputs": {
                "extra": [
                    {"node": "osa1", "port": "opt_in", "kind": "osa"},
                    {"node": "esa1", "port": "elec_in", "kind": "esa"},
                ]
            },
        }

        result = run_graph_job(data, validate=True, max_points=128)
        extra = result.get("extra", [])
        osa = extra[0] if len(extra) > 0 else {}
        self.assertEqual(osa.get("kind"), "osa")
        self.assertGreater(len(osa.get("freq", [])), 0)


if __name__ == "__main__":
    unittest.main()
