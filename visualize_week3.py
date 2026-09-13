# -*- coding: utf-8 -*-
"""
PHANTOM Grid - Week 3 Visualization
====================================
Generates clear 3-color visual demonstration of FIELD, HOLE, and FRINGE/RECEIVER nodes.
Saves figure cleanly to generated/ without touching desktop.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from core.types import CellStatus
from grids.structured_cartesian import StructuredCartesianGrid
from grids.component_grid import ComponentGrid
from cutting.hole_cutter import HoleCutter


def run_week3_visualization():
    bg = StructuredCartesianGrid("Background", (0.0, 1.0), (0.0, 1.0), (35, 35))
    comp = ComponentGrid(
        grid_id="RotatedFineGrid",
        local_x_range=(-0.15, 0.15),
        local_y_range=(-0.15, 0.15),
        dims=(29, 29),
        origin=(0.52, 0.52),
        angle_rad=np.radians(25.0)
    )

    # Cut hole
    HoleCutter.cut_by_component_grid(bg, comp, margin_ratio=0.18, fringe_layers=1)

    fig, ax = plt.subplots(figsize=(8, 8))

    # Color code
    status_styles = {
        CellStatus.FIELD: ("#0d6efd", "Active FIELD Cells", 20, 0.8),
        CellStatus.HOLE: ("#6c757d", "Blanked HOLE Cells", 25, 0.9),
        CellStatus.RECEIVER: ("#dc3545", "RECEIVER / Fringe Boundary", 45, 1.0),
    }

    # Plot Background nodes
    for status, (color, label, size, alpha) in status_styles.items():
        mask = (bg.status_mask == status)
        if np.any(mask):
            ax.scatter(bg.X[mask], bg.Y[mask], c=color, s=size, alpha=alpha, label=label)

    # Plot Component grid nodes & perimeter
    comp_rec = (comp.status_mask == CellStatus.RECEIVER)
    comp_field = (comp.status_mask == CellStatus.FIELD)
    ax.scatter(comp.X[comp_field], comp.Y[comp_field], c="#198754", s=10, alpha=0.5, label="Component Fine Nodes")
    ax.scatter(comp.X[comp_rec], comp.Y[comp_rec], c="#ffc107", s=30, alpha=0.9, label="Comp Receiver Perimeter")

    ax.set_title("Week 3: PHANTOM Overlapping Grid - Hole Cutting & Fringe Layer", fontsize=12, fontweight="bold")
    ax.set_xlabel("X (Global)")
    ax.set_ylabel("Y (Global)")
    ax.set_aspect("equal")
    ax.legend(loc="upper right", framealpha=0.9)
    ax.grid(True, linestyle=":", alpha=0.6)

    out_dir = os.path.join(os.path.dirname(__file__), "generated")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "phantom_grid_week3.png")
    plt.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close()
    print(f"Week 3 figure saved cleanly to: {out_path}")
    return out_path


if __name__ == "__main__":
    run_week3_visualization()
