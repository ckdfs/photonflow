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

    def test_fiber_chain(self):
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
                {
                    "id": "fiber1",
                    "type": "OpticalFiber",
                    "params": {
                        "length_m": 1000.0,
                        "alpha_db_per_km": 0.2,
                        "beta2_s2_per_m": 2.2e-26,
                        "beta3_s3_per_m": 1e-40,
                    },
                },
                {"id": "pd1", "type": "PD", "params": {"responsivity": 1.0}},
            ],
            "edges": [
                {"src": "laser1", "src_port": "opt_out", "dst": "fiber1", "dst_port": "opt_in"},
                {"src": "fiber1", "src_port": "opt_out", "dst": "pd1", "dst_port": "opt_in"},
            ],
            "outputs": {
                "osa": {"node": "fiber1", "port": "opt_out", "kind": "osa"},
                "esa": {"node": "pd1", "port": "elec_out", "kind": "esa"},
            },
        }
        self._run_graph(data)

    def test_optical_filter_chain(self):
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
                {
                    "id": "filter1",
                    "type": "OpticalFilter",
                    "params": {
                        "kind": "bandpass",
                        "shape": "gaussian",
                        "bandwidth_hz": 5e9,
                        "phase_mode": "quadratic",
                        "group_delay_s": 5e-12,
                        "gdd_s2": 2e-24,
                    },
                },
                {"id": "pd1", "type": "PD", "params": {"responsivity": 1.0}},
            ],
            "edges": [
                {"src": "laser1", "src_port": "opt_out", "dst": "filter1", "dst_port": "opt_in"},
                {"src": "filter1", "src_port": "opt_out", "dst": "pd1", "dst_port": "opt_in"},
            ],
            "outputs": {
                "osa": {"node": "filter1", "port": "opt_out", "kind": "osa"},
                "esa": {"node": "pd1", "port": "elec_out", "kind": "esa"},
            },
        }
        self._run_graph(data)

    def test_polarization_chain(self):
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
                {"id": "pol1", "type": "PolarizationRotator", "params": {"angle_rad": 0.7}},
                {
                    "id": "wp1",
                    "type": "PolarizationWaveplate",
                    "params": {"retardance_rad": 1.57079632679},
                    "nonideal": {
                        "enable": True,
                        "time_vary": True,
                        "drift_update_samples": 256,
                        "axis_drift_std_rad": 0.05,
                        "retardance_drift_std_rad": 0.02,
                    },
                },
                {
                    "id": "pc1",
                    "type": "PolarizationController",
                    "params": {"preset": "QHQ", "angle1_rad": 0.1, "angle2_rad": 0.2, "angle3_rad": 0.3},
                    "nonideal": {"enable": True, "angle_noise_std_rad": 0.01, "retardance_noise_std_rad": 0.02},
                },
                {
                    "id": "fiber1",
                    "type": "OpticalFiber",
                    "params": {
                        "length_m": 500.0,
                        "alpha_db_per_km": 0.2,
                        "ssfm_steps": 4,
                        "ssfm_auto": True,
                        "ssfm_auto_mode": "fast",
                        "ssfm_max_phase_rad": 0.2,
                        "ssfm_max_steps": 16,
                    },
                    "nonideal": {
                        "enable": True,
                        "pmd_dgd_s": 5e-12,
                        "pmd_axis_angle_rad": 0.3,
                        "pmd_time_vary": True,
                        "pmd_update_samples": 512,
                        "pmd_dgd_std_s": 1e-12,
                        "pmd_axis_std_rad": 0.1,
                        "pmd_biref_std_rad": 0.2,
                        "nonlin_gamma_w_inv_m": 1.2,
                    },
                },
                {
                    "id": "pdl1",
                    "type": "PolarizationPDL",
                    "params": {"pdl_db": 1.5, "axis_angle_rad": 0.4},
                },
                {"id": "pd1", "type": "PD", "params": {"responsivity": 1.0}},
            ],
            "edges": [
                {"src": "laser1", "src_port": "opt_out", "dst": "pol1", "dst_port": "opt_in"},
                {"src": "pol1", "src_port": "opt_out", "dst": "wp1", "dst_port": "opt_in"},
                {"src": "wp1", "src_port": "opt_out", "dst": "pc1", "dst_port": "opt_in"},
                {"src": "pc1", "src_port": "opt_out", "dst": "fiber1", "dst_port": "opt_in"},
                {"src": "fiber1", "src_port": "opt_out", "dst": "pdl1", "dst_port": "opt_in"},
                {"src": "pdl1", "src_port": "opt_out", "dst": "pd1", "dst_port": "opt_in"},
            ],
            "outputs": {
                "osa": {"node": "pdl1", "port": "opt_out", "kind": "osa"},
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

    def test_sim_clamps(self):
        from photonflow.core import Graph, SimConfig

        data = {
            "version": "0.1",
            "sim": {
                "backend": "torch",
                "device": "cpu",
                "fs": "auto",
                "oversample": 4,
                "seed": 0,
                "window": "hann",
                "duration_s": 1e-3,
            },
            "nodes": [
                {"id": "rf1", "type": "RFSource", "params": {"freq_hz": 1e6, "amplitude": 1.0}},
            ],
            "edges": [],
            "outputs": {"esa": {"node": "rf1", "port": "elec_out", "kind": "esa"}, "osa": {"node": "rf1", "port": "elec_out"}},
        }
        graph = Graph.from_dict(data, validate=True)
        graph.compile()
        sim_cfg = SimConfig(fs="auto", duration_s=1e-3, max_samples=1024)
        outputs = graph.run(sim_cfg)
        signal = outputs[("rf1", "elec_out")]
        self.assertEqual(signal.data.numel(), 1024)
        self.assertAlmostEqual(sim_cfg.duration_s, 1024 / float(sim_cfg.fs), places=12)

    def test_chunk_execution(self):
        from photonflow.core import Graph, SimConfig

        data = {
            "version": "0.1",
            "sim": {
                "backend": "torch",
                "device": "cpu",
                "fs": 1e6,
                "oversample": 4,
                "seed": 0,
                "window": "hann",
                "duration_s": 1e-3,
            },
            "nodes": [
                {"id": "rf1", "type": "RFSource", "params": {"freq_hz": 1e5, "amplitude": 1.0}},
            ],
            "edges": [],
            "outputs": {"esa": {"node": "rf1", "port": "elec_out", "kind": "esa"}, "osa": {"node": "rf1", "port": "elec_out"}},
        }
        graph = Graph.from_dict(data, validate=True)
        graph.compile()
        sim_cfg = SimConfig(fs=1e6, duration_s=1e-3, chunk=128)
        outputs = graph.run(sim_cfg)
        signal = outputs[("rf1", "elec_out")]
        self.assertEqual(signal.data.numel(), 1000)


if __name__ == "__main__":
    unittest.main()
