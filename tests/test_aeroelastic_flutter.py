# -*- coding: utf-8 -*-
"""
tests/test_aeroelastic_flutter.py - 二自由度氣動彈性顫振與動態網格 FSI 耦合驗證
=============================================================================
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import unittest
import numpy as np
from geometry.airfoil import NACA4Airfoil
from solver.fluid_force_integrator import FluidForceIntegrator
from solver.aeroelastic_flutter import AeroelasticFlutterSolver
from grids.component_grid import ComponentGrid
from grids.structured_cartesian import StructuredCartesianGrid
from geometry.hole_cutter import HoleCutter


class TestAeroelasticFlutter(unittest.TestCase):

    def test_fluid_force_integrator(self):
        """測試翼面壓力積分求解 CL, CD, CM"""
        # 生成 NACA 0012 翼面座標
        x, y = NACA4Airfoil.generate_contour(n_points=51, thickness=0.12, chord=1.0)
        integrator = FluidForceIntegrator(chord=1.0, rho_inf=1.0, u_inf=10.0)

        # 1. 均勻壓力場 (全對稱無升力)
        uniform_p = np.full_like(x, 101325.0)
        res_sym = integrator.integrate_forces(x, y, uniform_p)
        self.assertAlmostEqual(res_sym["CL"], 0.0, places=4)
        self.assertAlmostEqual(res_sym["CD"], 0.0, places=4)

        # 2. 差壓場 (下翼面壓力大於上翼面，產生正升力)
        # 上翼面 y >= 0, 下翼面 y < 0
        diff_p = np.where(y >= 0, 100.0, 300.0)
        res_lift = integrator.integrate_forces(x, y, diff_p)
        self.assertGreater(res_lift["CL"], 0.0)
        self.assertGreater(res_lift["Fy"], 0.0)

    def test_free_vibration_damping_decay(self):
        """測試無外力下結構阻尼自由衰減震盪"""
        solver = AeroelasticFlutterSolver(
            chord=1.0,
            mass=5.0,
            I_alpha=0.5,
            omega_h=10.0,
            omega_alpha=20.0,
            zeta_h=0.05,
            zeta_alpha=0.05
        )
        solver.set_initial_conditions(h0=0.05, alpha0_rad=np.radians(5.0))

        initial_energy = 0.5 * solver.k_h * (solver.h ** 2) + 0.5 * solver.k_alpha * (solver.alpha ** 2)

        dt = 0.005
        for _ in range(100):
            solver.step_rk4(dt=dt, Lift=0.0, Moment_ea=0.0)

        final_energy = 0.5 * solver.k_h * (solver.h ** 2) + 0.5 * solver.k_alpha * (solver.alpha ** 2)
        # 能量必須因結構阻尼單調耗散衰減
        self.assertLess(final_energy, initial_energy)

    def test_fsi_grid_pose_coupling(self):
        """測試氣彈 FSI 與前景網格 SE(2) 姿態即時同步及孔洞重新切割"""
        solver = AeroelasticFlutterSolver(chord=1.0)
        solver.set_initial_conditions(h0=0.02, alpha0_rad=np.radians(3.0))

        bg = StructuredCartesianGrid("bg", bounds=(-2.0, 2.0, -2.0, 2.0), shape=(51, 51), priority=0)
        fg = ComponentGrid("fg", local_bounds=(-0.6, 0.6, -0.4, 0.4), shape=(31, 21),
                           origin=(0.0, 0.0), angle_rad=0.0, priority=10)

        dt = 0.01
        for step_idx in range(20):
            # 模擬空氣動力：Lift 隨攻角線性增加 L = 0.5*rho*U^2*c*(2*pi*alpha)
            lift = 0.5 * 1.225 * (20.0 ** 2) * 1.0 * (2.0 * np.pi * solver.alpha)
            moment = 0.1 * lift  # 氣動焦點與彈性軸力矩

            solver.step_rk4(dt=dt, Lift=lift, Moment_ea=moment)
            # 同步姿勢至網格
            solver.update_grid_pose(fg)

            # 動態孔洞切割驗證
            HoleCutter.cut_holes_and_mark_fringe(bg, fg, shrink_margin=0.1, fringe_layers=1)

        # 驗證結構姿態已非初始值且數值有界穩定
        self.assertFalse(np.isnan(solver.h))
        self.assertFalse(np.isnan(solver.alpha))
        self.assertNotEqual(fg.transform.theta, 0.0)


if __name__ == "__main__":
    unittest.main()
