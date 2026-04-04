"""TLE feature engineering for orbital learning and conjunction ranking."""

from __future__ import annotations

import numpy as np
import pandas as pd


EARTH_RADIUS_KM = 6371.0
EARTH_MU_KM3_S2 = 398600.4418


def _require_columns(df: pd.DataFrame, columns: set[str]) -> None:
    missing = sorted(columns.difference(df.columns))
    if missing:
        raise ValueError(f"missing required TLE columns: {', '.join(missing)}")


def _cyclic_pair(values: pd.Series) -> tuple[pd.Series, pd.Series]:
    radians = np.deg2rad(pd.to_numeric(values, errors="coerce"))
    return pd.Series(np.sin(radians), index=values.index), pd.Series(np.cos(radians), index=values.index)


def engineer_tle_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer physically meaningful features from parsed TLE records.

    The output keeps the original columns and adds orbit-shell, energy, drag,
    and cyclic encodings that are useful for both sequence models and tree
    baselines.
    """

    if df is None or df.empty:
        return df.copy() if df is not None else pd.DataFrame()

    required_columns = {
        "inclination_deg",
        "raan_deg",
        "eccentricity",
        "arg_perigee_deg",
        "mean_anomaly_deg",
        "mean_motion_rev_per_day",
    }
    _require_columns(df, required_columns)

    features = df.copy()

    inclination = pd.to_numeric(features["inclination_deg"], errors="coerce")
    raan = pd.to_numeric(features["raan_deg"], errors="coerce")
    eccentricity = pd.to_numeric(features["eccentricity"], errors="coerce").clip(lower=0.0, upper=0.999999)
    arg_perigee = pd.to_numeric(features["arg_perigee_deg"], errors="coerce")
    mean_anomaly = pd.to_numeric(features["mean_anomaly_deg"], errors="coerce")
    mean_motion = pd.to_numeric(features["mean_motion_rev_per_day"], errors="coerce").replace(0, np.nan)

    mean_motion_rad_s = mean_motion * 2.0 * np.pi / 86400.0
    semi_major_axis_km = np.power(EARTH_MU_KM3_S2 / np.square(mean_motion_rad_s), 1.0 / 3.0)
    altitude_km = semi_major_axis_km - EARTH_RADIUS_KM
    perigee_km = semi_major_axis_km * (1.0 - eccentricity) - EARTH_RADIUS_KM
    apogee_km = semi_major_axis_km * (1.0 + eccentricity) - EARTH_RADIUS_KM
    orbital_velocity_km_s = np.sqrt(EARTH_MU_KM3_S2 / semi_major_axis_km)
    orbital_period_hours = 24.0 / mean_motion
    specific_energy_km2_s2 = -EARTH_MU_KM3_S2 / (2.0 * semi_major_axis_km)

    inclination_rad = np.deg2rad(inclination)
    raan_sin, raan_cos = _cyclic_pair(raan)
    argp_sin, argp_cos = _cyclic_pair(arg_perigee)
    meananom_sin, meananom_cos = _cyclic_pair(mean_anomaly)

    leo_density = np.exp(-np.square((altitude_km - 800.0) / 400.0))
    geo_density = np.exp(-np.square((altitude_km - 35786.0) / 5000.0))
    collision_density = leo_density + 0.3 * geo_density
    inclination_risk = np.square(np.sin(inclination_rad))
    drag_risk = np.where(altitude_km < 1000.0, np.exp(-altitude_km / 150.0), 0.01)
    shell_distance_from_leo = np.abs(altitude_km - 800.0)
    shell_distance_from_geo = np.abs(altitude_km - 35786.0)
    finite_density = collision_density[np.isfinite(collision_density)]
    density_max = float(finite_density.max()) if finite_density.size else 1.0
    shell_density_score = np.clip(collision_density / max(density_max, 1e-6), 0.0, 1.0)
    orbit_phase_score = np.clip((meananom_sin + 1.0) * 0.5, 0.0, 1.0)

    features["inclination_rad"] = inclination_rad
    features["raan_rad"] = np.deg2rad(raan)
    features["arg_perigee_rad"] = np.deg2rad(arg_perigee)
    features["mean_anomaly_rad"] = np.deg2rad(mean_anomaly)
    features["semi_major_axis_km"] = semi_major_axis_km
    features["altitude_km"] = altitude_km
    features["perigee_km"] = perigee_km
    features["apogee_km"] = apogee_km
    features["orbital_velocity_km_s"] = orbital_velocity_km_s
    features["orbital_period_hours"] = orbital_period_hours
    features["specific_orbital_energy_km2_s2"] = specific_energy_km2_s2
    features["inclination_risk"] = inclination_risk
    features["eccentricity_risk"] = eccentricity
    features["drag_risk"] = drag_risk
    features["collision_density"] = collision_density
    features["shell_density_score"] = shell_density_score
    features["orbit_phase_score"] = orbit_phase_score
    features["shell_distance_from_leo_km"] = shell_distance_from_leo
    features["shell_distance_from_geo_km"] = shell_distance_from_geo
    features["raan_sin"] = raan_sin
    features["raan_cos"] = raan_cos
    features["arg_perigee_sin"] = argp_sin
    features["arg_perigee_cos"] = argp_cos
    features["mean_anomaly_sin"] = meananom_sin
    features["mean_anomaly_cos"] = meananom_cos
    features["leo_indicator"] = ((altitude_km >= 400.0) & (altitude_km <= 2000.0)).astype(float)
    features["meo_indicator"] = ((altitude_km > 2000.0) & (altitude_km < 35000.0)).astype(float)
    features["geo_indicator"] = ((altitude_km >= 35000.0) & (altitude_km <= 36000.0)).astype(float)
    features["threat_prior"] = np.clip(
        0.35 * features["collision_density"]
        + 0.25 * features["drag_risk"]
        + 0.2 * features["inclination_risk"]
        + 0.2 * features["eccentricity_risk"],
        0.0,
        1.0,
    )

    if "epoch" in features.columns:
        features["epoch"] = pd.to_datetime(features["epoch"], errors="coerce")

    if "norad_cat_id" in features.columns:
        features["norad_cat_id"] = pd.to_numeric(features["norad_cat_id"], errors="coerce").astype("Int64")

    return features
