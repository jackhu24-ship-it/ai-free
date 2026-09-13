# -*- coding: utf-8 -*-
"""
PHANTOM Grid - Bilinear Interpolator & Donor Cell Search
========================================================
Implements bilinear mapping and donor stencil weighting for inter-grid communication.
"""
from typing import Tuple
import numpy as np
from .base_grid import AbstractGrid, CellStatus
from .structured_block import StructuredBlock2D


class BilinearInterpolator:
    """
    Computes bilinear weights and interpolates physical fields from a donor grid
    to arbitrary target query coordinates (xq, yq).
    """

    @staticmethod
    def interpolate(
        donor: StructuredBlock2D,
        field_name: str,
        xq: np.ndarray,
        yq: np.ndarray,
        check_donor_status: bool = True
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Interpolates field_name from donor at points (xq, yq).

        Returns:
            values: 1D or ND numpy array with interpolated values
            valid_mask: boolean mask indicating if point is inside donor domain and donors are valid
        """
        xq = np.asarray(xq)
        yq = np.asarray(yq)
        out_shape = xq.shape

        xq_flat = xq.ravel()
        yq_flat = yq.ravel()
        n_pts = len(xq_flat)

        u = donor.get_field(field_name)
        status = donor.status_mask

        # 1. Bounds check
        in_bounds = (
            (xq_flat >= donor.x_min) & (xq_flat <= donor.x_max) &
            (yq_flat >= donor.y_min) & (yq_flat <= donor.y_max)
        )

        # 2. Local normalized coordinates
        # Clamp to avoid out-of-index on upper boundary
        xi_float = (xq_flat - donor.x_min) / donor.dx
        eta_float = (yq_flat - donor.y_min) / donor.dy

        i0 = np.clip(np.floor(xi_float).astype(int), 0, donor.nx - 2)
        j0 = np.clip(np.floor(eta_float).astype(int), 0, donor.ny - 2)
        i1 = i0 + 1
        j1 = j0 + 1

        xi = np.clip(xi_float - i0, 0.0, 1.0)
        eta = np.clip(eta_float - j0, 0.0, 1.0)

        # 3. Bilinear stencil weights (sum to 1)
        w00 = (1.0 - xi) * (1.0 - eta)
        w10 = xi * (1.0 - eta)
        w01 = (1.0 - xi) * eta
        w11 = xi * eta

        # 4. Donor validity check (cannot interpolate from HOLE cells)
        valid = in_bounds.copy()
        if check_donor_status and status is not None:
            no_holes = (
                (status[i0, j0] != CellStatus.HOLE) &
                (status[i1, j0] != CellStatus.HOLE) &
                (status[i0, j1] != CellStatus.HOLE) &
                (status[i1, j1] != CellStatus.HOLE)
            )
            valid = valid & no_holes

        # 5. Interpolate
        vals = (
            w00 * u[i0, j0] +
            w10 * u[i1, j0] +
            w01 * u[i0, j1] +
            w11 * u[i1, j1]
        )

        vals[~valid] = np.nan
        return vals.reshape(out_shape), valid.reshape(out_shape)
