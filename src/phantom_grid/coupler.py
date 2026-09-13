# -*- coding: utf-8 -*-
"""
PHANTOM Grid - Overlap Coupler
==============================
Orchestrates hole cutting, receiver identification, and two-way boundary exchange.
"""
from typing import List, Dict, Any, Optional
import numpy as np
from .base_grid import CellStatus
from .structured_block import StructuredBlock2D
from .hole_cutter import HoleCutter
from .interpolator import BilinearInterpolator


class OverlapCoupler:
    """
    Coordinates multi-resolution overlapping grid systems.
    Manages one background grid and one or more component grids.
    """

    def __init__(
        self,
        background_grid: StructuredBlock2D,
        component_grids: Optional[List[StructuredBlock2D]] = None
    ):
        self.bg = background_grid
        self.components = component_grids if component_grids is not None else []

    def add_component_grid(self, grid: StructuredBlock2D) -> None:
        """Register an embedded component grid."""
        self.components.append(grid)

    def setup_static_nesting(
        self,
        overlap_margin_ratio: float = 0.20,
        fringe_width: int = 1
    ) -> None:
        """
        Executes standard static patch configuration:
        1. Cuts hole in background grid beneath each component grid.
        2. Dilates hole to create RECEIVER cells on background grid.
        3. Marks outer boundary of each component grid as RECEIVER cells.
        """
        for comp in self.components:
            # 1 & 2: Hole cutting and background receiver fringe
            HoleCutter.cut_for_component_grid(
                background_grid=self.bg,
                component_grid=comp,
                overlap_margin_ratio=overlap_margin_ratio,
                fringe_width=fringe_width
            )

            # 3: Component perimeter becomes receivers from background
            comp.mark_perimeter_as_receiver(width=fringe_width)

    def transfer_boundary_data(self, field_name: str) -> Dict[str, int]:
        """
        Two-way data exchange between background and component grids.
        Returns count of transferred receiver nodes.
        """
        stats = {"bg_to_comp": 0, "comp_to_bg": 0}

        # 1. Background -> Component Grids
        for comp in self.components:
            comp_rec_mask = (comp.status_mask == CellStatus.RECEIVER)
            if np.any(comp_rec_mask):
                xq = comp.X[comp_rec_mask]
                yq = comp.Y[comp_rec_mask]

                interp_vals, valid = BilinearInterpolator.interpolate(
                    donor=self.bg,
                    field_name=field_name,
                    xq=xq,
                    yq=yq,
                    check_donor_status=True
                )

                field = comp.get_field(field_name)
                # Assign only valid donor points
                target_idx = np.where(comp_rec_mask)
                field[target_idx[0][valid], target_idx[1][valid]] = interp_vals[valid]
                comp.set_field(field_name, field)
                stats["bg_to_comp"] += int(np.sum(valid))

        # 2. Component Grids -> Background Grid
        bg_rec_mask = (self.bg.status_mask == CellStatus.RECEIVER)
        if np.any(bg_rec_mask):
            bg_field = self.bg.get_field(field_name)
            xq = self.bg.X[bg_rec_mask]
            yq = self.bg.Y[bg_rec_mask]
            rec_indices = np.where(bg_rec_mask)

            # Try interpolating from each component grid
            for comp in self.components:
                interp_vals, valid = BilinearInterpolator.interpolate(
                    donor=comp,
                    field_name=field_name,
                    xq=xq,
                    yq=yq,
                    check_donor_status=True
                )

                if np.any(valid):
                    bg_field[rec_indices[0][valid], rec_indices[1][valid]] = interp_vals[valid]
                    stats["comp_to_bg"] += int(np.sum(valid))

            self.bg.set_field(field_name, bg_field)

        return stats

    def step_system(self, dt: float, field_name: str = "u", alpha: float = 0.1) -> Dict[str, Any]:
        """
        Advance one coupled time step:
        1. Local PDE update on active FIELD cells for each block.
        2. Two-way boundary transfer across overlapping interfaces.
        """
        # Step PDE locally
        self.bg.step_pde(dt=dt, field_name=field_name, alpha=alpha)
        for comp in self.components:
            comp.step_pde(dt=dt, field_name=field_name, alpha=alpha)

        # Couple boundaries
        transfer_stats = self.transfer_boundary_data(field_name)
        return transfer_stats
