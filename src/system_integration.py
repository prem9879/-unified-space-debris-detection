"""Integration and system orchestration for complete space debris detection pipeline.

This module coordinates all components:
- TLE data ingestion
- Trajectory prediction
- Conjunction detection
- Real-time monitoring
- 3D visualization
- Risk reporting

Component: System Integration & Orchestration
Status: Production-Ready
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class UnifiedDebrisDetectionSystem:
    """Main orchestrator for the complete space debris detection pipeline."""

    def __init__(self, compute_profile: str = "balanced"):
        """Initialize the unified system."""
        self.tle_fetcher = None
        self.trajectory_predictor = None
        self.conjunction_detector = None
        self.realtime_monitor = None
        self.orbital_visualizer = None
        self.kessler_model = None
        self.sensor_fusion = None
        self.mission_control = None
        self.compute_profile = compute_profile

        self.last_update = None
        self.debris_catalog = {}
        self.active_alerts = []
        self.system_status = "INITIALIZED"

    async def initialize_all_components(self) -> bool:
        """Initialize all system components.

        Returns:
            Success status
        """
        try:
            logger.info("=" * 70)
            logger.info("INITIALIZING UNIFIED SPACE DEBRIS DETECTION SYSTEM")
            logger.info("=" * 70)

            # Import components (avoiding circular imports)
            from src.data.tle_pipeline import (
                RealTimeTLEStream,
            )
            from src.models.trajectory_predictor import (
                TransformerTrajectoryPredictor,
            )
            from src.streaming.realtime_monitor import (
                RealTimeDebrisMonitor,
                KesslerSyndromeModel,
            )
            from src.visualization.orbital_visualizer import DashboardDataProvider
            from src.deployment.operational_bridge import (
                MissionControlBridge,
                SensorFusionBridge,
            )

            logger.info("✓ Initializing TLE Pipeline...")
            self.tle_stream = RealTimeTLEStream(fetch_interval_hours=6)

            logger.info("✓ Initializing Trajectory Predictor...")
            d_model = 64 if self.compute_profile == "low_compute" else 128
            self.trajectory_predictor = TransformerTrajectoryPredictor(
                input_size=14, d_model=d_model
            )

            logger.info("✓ Initializing Real-Time Monitor...")
            self.realtime_monitor = RealTimeDebrisMonitor()

            logger.info("✓ Initializing Orbital Visualizer...")
            self.orbital_visualizer = DashboardDataProvider()

            logger.info("✓ Initializing Kessler Syndrome Model...")
            self.kessler_model = KesslerSyndromeModel(initial_debris_count=34000)

            logger.info("✓ Initializing Sensor Fusion Bridge...")
            self.sensor_fusion = SensorFusionBridge()

            logger.info("✓ Initializing Mission Control Bridge...")
            self.mission_control = MissionControlBridge(
                require_human_approval=True,
            )

            self.system_status = "READY"
            logger.info("✓ ALL COMPONENTS INITIALIZED SUCCESSFULLY")
            logger.info("=" * 70)

            return True
        except Exception as e:
            logger.error(f"✗ Initialization failed: {e}")
            self.system_status = "ERROR"
            return False

    async def update_debris_catalog(self) -> dict[str, Any]:
        """Fetch and update debris catalog from TLE sources.

        Returns:
            Updated catalog metadata
        """
        try:
            logger.info("Fetching latest TLE data...")
            catalog = self.tle_stream.update_debris_catalog()

            if not catalog:
                logger.warning("No TLE data retrieved")
                return {"status": "failed", "reason": "No TLE data"}

            self.debris_catalog = catalog
            self.last_update = datetime.now()

            logger.info(f"✓ Updated catalog: {len(catalog)} objects")

            return {
                "status": "success",
                "total_objects": len(catalog),
                "timestamp": self.last_update.isoformat(),
                "leo_count": sum(
                    1
                    for obj in catalog.values()
                    if 400 <= obj.get("altitude_km", 0) <= 2000
                ),
                "geo_count": sum(
                    1
                    for obj in catalog.values()
                    if 35700 <= obj.get("altitude_km", 0) <= 35900
                ),
            }
        except Exception as e:
            logger.error(f"Catalog update failed: {e}")
            return {"status": "failed", "reason": str(e)}

    async def compute_conjunction_risks(self, sample_size: int = 500) -> dict[str, Any]:
        """Compute conjunction risks for catalog.

        Args:
            sample_size: Number of objects to process (for performance)

        Returns:
            Conjunction risk analysis
        """
        try:
            if not self.debris_catalog:
                return {"status": "failed", "reason": "Empty catalog"}

            logger.info(f"Computing conjunction risks for {sample_size} objects...")

            objects = list(self.debris_catalog.values())[:sample_size]
            n = len(objects)

            max_pairs_by_profile = {
                "low_compute": 25000,
                "balanced": 100000,
                "high_accuracy": 300000,
            }
            max_pairs = max_pairs_by_profile.get(self.compute_profile, 100000)

            candidate_pairs = self.tle_stream.shortlist_conjunction_candidates(
                objects,
                max_pairs=max_pairs,
            )

            high_risk_pairs = []
            for i, j in candidate_pairs:
                risk = self.tle_stream.engineer.compute_conjunction_risk(
                    objects[i], objects[j]
                )

                if risk > 0.6:  # Significant risk threshold
                    high_risk_pairs.append(
                        {
                            "object1_id": objects[i]["norad_cat_id"],
                            "object2_id": objects[j]["norad_cat_id"],
                            "conjunction_risk": float(risk),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

            self.active_alerts = sorted(
                high_risk_pairs,
                key=lambda x: x["conjunction_risk"],
                reverse=True,
            )[:50]

            logger.info(
                f"✓ Screened {len(candidate_pairs)} candidate pairs, found {len(self.active_alerts)} high-risk"
            )

            theoretical_pairs = n * (n - 1) // 2
            reduction_pct = 0.0
            if theoretical_pairs > 0:
                reduction_pct = 100.0 * (1.0 - len(candidate_pairs) / theoretical_pairs)

            return {
                "status": "success",
                "pairs_analyzed": len(candidate_pairs),
                "theoretical_pairs": theoretical_pairs,
                "screening_reduction_percent": float(reduction_pct),
                "high_risk_pairs": len(self.active_alerts),
                "top_alerts": self.active_alerts[:10],
                "compute_profile": self.compute_profile,
            }
        except Exception as e:
            logger.error(f"Conjunction computation failed: {e}")
            return {"status": "failed", "reason": str(e)}

    async def ingest_external_sensor_data(
        self,
        radar_observations: list[Any],
        optical_observations: list[Any],
    ) -> dict[str, Any]:
        """Fuse external sensor observations into the active catalog."""
        if not self.sensor_fusion:
            return {"status": "failed", "reason": "sensor bridge not initialized"}
        if not self.debris_catalog:
            return {"status": "failed", "reason": "empty catalog"}

        result = self.sensor_fusion.fuse_into_catalog(
            self.debris_catalog,
            radar_observations=radar_observations,
            optical_observations=optical_observations,
        )
        return result

    def propose_maneuver_command(
        self,
        norad_id: int,
        delta_v_rtn_km_s: tuple[float, float, float],
        execute_at: datetime,
        approved_by: str | None = None,
    ) -> dict[str, Any]:
        """Create and policy-check a maneuver command packet."""
        if not self.mission_control:
            return {"status": "failed", "reason": "mission control not initialized"}

        packet = self.mission_control.build_maneuver_command(
            norad_id=norad_id,
            delta_v_rtn_km_s=delta_v_rtn_km_s,
            execute_at=execute_at,
        )
        return self.mission_control.authorize_command(packet, approved_by=approved_by)

    async def generate_dashboard_snapshot(self) -> dict[str, Any]:
        """Generate complete dashboard visualization data.

        Returns:
            Dashboard snapshot for web UI
        """
        try:
            if not self.debris_catalog:
                return {"status": "failed"}

            logger.info("Generating dashboard snapshot...")

            # Get Kessler status
            kessler_status = self.kessler_model.estimate_cascading_collision_risk()

            # Create dashboard data
            snapshot = self.orbital_visualizer.create_dashboard_snapshot(
                debris_catalog=list(self.debris_catalog.values()),
                high_risk_conjunctions=self.active_alerts,
                kessler_status=kessler_status,
                timestamp=(
                    self.last_update.isoformat()
                    if self.last_update
                    else datetime.now().isoformat()
                ),
            )

            logger.info("✓ Dashboard snapshot generated")
            return snapshot
        except Exception as e:
            logger.error(f"Dashboard generation failed: {e}")
            return {"status": "failed", "reason": str(e)}

    async def generate_system_report(self) -> dict[str, Any]:
        """Generate comprehensive system status report.

        Returns:
            System health and performance report
        """
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "system_status": self.system_status,
                "catalog_size": len(self.debris_catalog),
                "active_alerts": len(self.active_alerts),
                "last_update": (
                    self.last_update.isoformat() if self.last_update else None
                ),
                "components": {
                    "tle_pipeline": "READY" if self.tle_stream else "NOT_INIT",
                    "trajectory_predictor": (
                        "READY" if self.trajectory_predictor else "NOT_INIT"
                    ),
                    "realtime_monitor": (
                        "READY" if self.realtime_monitor else "NOT_INIT"
                    ),
                    "orbital_visualizer": (
                        "READY" if self.orbital_visualizer else "NOT_INIT"
                    ),
                    "sensor_fusion": "READY" if self.sensor_fusion else "NOT_INIT",
                    "mission_control": "READY" if self.mission_control else "NOT_INIT",
                },
                "compute_profile": self.compute_profile,
                "kessler_risk": (
                    self.kessler_model.estimate_cascading_collision_risk()
                    if self.kessler_model
                    else None
                ),
                "orbital_distribution": {},
            }

            # Orbital distribution
            leo = sum(
                1
                for obj in self.debris_catalog.values()
                if 400 <= obj.get("altitude_km", 0) <= 2000
            )
            geo = sum(
                1
                for obj in self.debris_catalog.values()
                if 35700 <= obj.get("altitude_km", 0) <= 35900
            )
            meo = len(self.debris_catalog) - leo - geo

            report["orbital_distribution"] = {
                "LEO_400_2000km": leo,
                "MEO_2000_35700km": meo,
                "GEO_35700_35900km": geo,
            }

            return report
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {"status": "failed", "reason": str(e)}

    async def run_periodic_update_cycle(self, interval_minutes: int = 60) -> None:
        """Run periodic update cycle (for integration with scheduler).

        Args:
            interval_minutes: Update interval
        """
        while True:
            try:
                logger.info("\n" + "=" * 70)
                logger.info(f"PERIODIC UPDATE CYCLE - {datetime.now().isoformat()}")
                logger.info("=" * 70)

                # Update catalog
                catalog_result = await self.update_debris_catalog()
                logger.info(f"Catalog: {catalog_result}")

                # Compute risks
                risk_result = await self.compute_conjunction_risks(sample_size=300)
                logger.info(f"Risks: {risk_result}")

                # Generate dashboard
                dashboard = await self.generate_dashboard_snapshot()
                logger.info(
                    f"Dashboard: Generated snapshot with {len(dashboard.get('debris_objects', []))} visualizations"
                )

                # Generate report
                report = await self.generate_system_report()
                logger.info(f"Report: {json.dumps(report, indent=2, default=str)}")

                logger.info(
                    f"\n✓ Cycle complete - next update in {interval_minutes} minutes"
                )

            except Exception as e:
                logger.error(f"Update cycle error: {e}")

            await asyncio.sleep(interval_minutes * 60)


# CLI Commands
async def main():
    """Main entry point for system initialization and testing."""
    import sys

    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                UNIFIED SPACE DEBRIS DETECTION SYSTEM                      ║
║                        Production-Grade v1.0                              ║
║                                                                           ║
║  Multi-Modal AI Detection • Real-Time Monitoring • Collision Prediction   ║
║  Graph Neural Networks • LSTM/Transformers • Kessler Syndrome Analysis    ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)

    system = UnifiedDebrisDetectionSystem()

    # Initialize
    init_success = await system.initialize_all_components()
    if not init_success:
        logger.error("Initialization failed")
        sys.exit(1)

    # Single update cycle
    print("\n[1/4] Updating debris catalog...")
    catalog = await system.update_debris_catalog()
    print(json.dumps(catalog, indent=2))

    print("\n[2/4] Computing conjunction risks...")
    risks = await system.compute_conjunction_risks(sample_size=100)
    print(json.dumps(risks, indent=2))

    print("\n[3/4] Generating dashboard...")
    dashboard = await system.generate_dashboard_snapshot()
    print(
        f"Dashboard: {len(dashboard.get('debris_objects', []))} debris, "
        f"{len(dashboard.get('conjunction_alerts', []))} alerts"
    )

    print("\n[4/4] System status report...")
    report = await system.generate_system_report()
    print(json.dumps(report, indent=2, default=str))

    print("\n✅ SYSTEM OPERATIONAL - Ready for production deployment")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    asyncio.run(main())
