# -*- coding: utf-8 -*-
"""
PHANTOM Grid - Visualization Demo
=================================
Demonstrates multi-resolution static nesting, hole cutting, and cell classification status.
Saves figure cleanly to generated/ without touching desktop.
"""
import os
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

from src.phantom_grid.base_grid import CellStatus
from src.phantom_grid.structured_block import StructuredBlock2D
from src.phantom_grid.coupler import OverlapCoupler


def run_visualization():
    # 1. Initialize background and component grids
    bg = StructuredBlock2D("Background_Coarse", (0.0, 1.0), (0.0, 1.0), (31, 31))
    comp = StructuredBlock2D("Component_Fine", (0.35, 0.75), (0.35, 0.75), (35, 35))

    # 2. Setup static overlap nesting
    coupler = OverlapCoupler(bg, [comp])
    coupler.setup_static_nesting(overlap_margin_ratio=0.20, fringe_width=1)

    # 3. Setup initial field: 2D Gaussian vortex
    bg.set_field("u", np.exp(-((bg.X - 0.5)**2 + (bg.Y - 0.5)**2) / 0.04))
    comp.set_field("u", np.exp(-((comp.X - 0.5)**2 + (comp.Y - 0.5)**2) / 0.04))

    # 4. Exchange boundary data
    coupler.transfer_boundary_data("u")

    # 5. Plot
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))

    # Color map for CellStatus: HOLE=black/gray, FIELD=blue, RECEIVER=red
    status_colors = {
        CellStatus.HOLE: ("#6c757d", "Hole (Blanked)", 10),
        CellStatus.FIELD: ("#0d6efd", "Field (Active)", 18),
        CellStatus.RECEIVER: ("#dc3545", "Receiver (Fringe)", 35),
    }

    # Left plot: Background grid classification
    ax = axes[0]
    for status, (color, label, size) in status_colors.items():
        mask = (bg.status_mask == status)
        if np.any(mask):
            ax.scatter(bg.X[mask], bg.Y[mask], c=color, s=size, label=f"BG {label}", alpha=0.85)

    # Plot component grid outline and nodes
    ax.scatter(comp.X, comp.Y, c="#198754", s=6, alpha=0.4, label="Component Fine Nodes")
    comp_rec = (comp.status_mask == CellStatus.RECEIVER)
    ax.scatter(comp.X[comp_rec], comp.Y[comp_rec], c="#ffc107", s=25, label="Comp Receiver Perimeter")

    ax.set_title("PHANTOM Overlapping Grid - Cell Classification Status", fontsize=12, fontweight="bold")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_aspect("equal")
    ax.grid(True, linestyle=":", alpha=0.5)

    # Right plot: Physical field contour across coupled domain
    ax2 = axes[1]
    # Background field (mask out HOLE cells)
    bg_u = bg.get_field("u").copy()
    bg_u[bg.status_mask == CellStatus.HOLE] = np.nan
    c1 = ax2.pcolormesh(bg.X, bg.Y, bg_u, shading="auto", cmap="viridis", alpha=0.7)

    # Component field
    comp_u = comp.get_field("u")
    c2 = ax2.pcolormesh(comp.X, comp.Y, comp_u, shading="auto", cmap="viridis", alpha=0.9)

    fig.colorbar(c2, ax=ax2, label="Scalar Field u(x, y)")
    ax2.set_title("Coupled Field Continuity Across Overlap", fontsize=12, fontweight="bold")
    ax2.set_xlabel("X")
    ax2.set_ylabel("Y")
    ax2.set_aspect("equal")

    plt.tight_layout()

    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "generated")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "phantom_grid_status.png")
    plt.savefig(out_path, dpi=180)
    plt.close()
    print(f"Figure saved successfully to: {out_path}")
    return out_path


if __name__ == "__main__":
    run_visualization()
