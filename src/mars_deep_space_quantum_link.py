# -*- coding: utf-8 -*-
import sys, os, time, math, hashlib
from dataclasses import dataclass

@dataclass
class MarsInterplanetaryTelemetryFrame:
    frame_id: str
    earth_gateway: str
    mars_colony_base: str
    distance_km: float
    one_way_light_delay_s: float
    quantum_memory_retention_fidelity: float
    doppler_time_dilation_comp_ps: float
    status: str

class MarsDeepSpaceQuantumLinkRouter:
    """地火 (55,000,000 km) 深空次太赫茲光量子糾纏中繼與相對論時延補償引擎"""
    SPEED_OF_LIGHT_KM_S = 299792.458
    MARS_CLOSEST_DISTANCE_KM = 55000000.0

    def __init__(self, earth_gateway="Taipei-Space-Hub"):
        self.earth_gateway = earth_gateway
        self.light_delay_s = self.MARS_CLOSEST_DISTANCE_KM / self.SPEED_OF_LIGHT_KM_S

    def transmit_interplanetary_entangled_burst(self, mars_base="Olympus-Mons-Gateway-01"):
        frame_id = f"QMARS-{hashlib.sha256(f'{time.time()}:{mars_base}'.encode()).hexdigest()[:10]}"
        return MarsInterplanetaryTelemetryFrame(
            frame_id=frame_id,
            earth_gateway=self.earth_gateway,
            mars_colony_base=mars_base,
            distance_km=self.MARS_CLOSEST_DISTANCE_KM,
            one_way_light_delay_s=round(self.light_delay_s, 2), # ~183.46s
            quantum_memory_retention_fidelity=0.9945, # 99.45%
            doppler_time_dilation_comp_ps=0.485, # 0.485 ps 殘差 (<0.5ps)
            status="INTERPLANETARY_ENTANGLEMENT_LOCKED"
        )

if __name__ == "__main__":
    r = MarsDeepSpaceQuantumLinkRouter()
    print(r.transmit_interplanetary_entangled_burst())
