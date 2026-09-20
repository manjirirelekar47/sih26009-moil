def evaluate_weather_impact(
    rainfall_48h_mm: float,
    soil_moisture_index: float,
    rainfall_7d_mm: float = 0.0,
    consecutive_dry_days: int = 0
) -> dict:
    """
    Evaluates rainfall, soil moisture, and dry spell data to generate mining risk alerts.
    
    Inputs:
        rainfall_48h_mm: float (Cumulative 48-hour rainfall from CHIRPS)
        soil_moisture_index: float (0.0 to 1.0 proxy index from Sentinel-1 SAR)
        rainfall_7d_mm: float (Cumulative 7-day rainfall from CHIRPS for slope analysis)
        consecutive_dry_days: int (Count of continuous zero-rain days for dust hazard analysis)
        
    Outputs:
        dict: Alert objects for waterlogging, road risk, haul road friction,
              slope instability risk, and haul road dust/visibility hazard.
    """
    # ---------------------------------------------------------
    # 1. Waterlogging Risk Assessment
    # ---------------------------------------------------------
    if rainfall_48h_mm >= 35.0:
        waterlogging = {
            "level": "HIGH",
            "message": "High waterlogging risk: Pit flooding probable."
        }
    elif rainfall_48h_mm >= 15.0:
        waterlogging = {
            "level": "MODERATE",
            "message": "Moderate waterlogging: Monitor low-lying benches."
        }
    else:
        waterlogging = {
            "level": "LOW",
            "message": "Low waterlogging risk: Pit conditions nominal."
        }

    # ---------------------------------------------------------
    # 2. Road Risk Assessment
    # ---------------------------------------------------------
    if soil_moisture_index >= 0.7:
        road_risk = {
            "level": "CRITICAL",
            "message": "Critical road risk: High unpaved track instability."
        }
    elif soil_moisture_index >= 0.4:
        road_risk = {
            "level": "MODERATE",
            "message": "Moderate road risk: Surface slickness detected."
        }
    else:
        road_risk = {
            "level": "LOW",
            "message": "Low road risk: Roads firm."
        }

    # ---------------------------------------------------------
    # 3. Haul Road Friction / Bottleneck Alert
    # ---------------------------------------------------------
    if rainfall_48h_mm > 25.0 and soil_moisture_index > 0.6:
        friction_alert = {
            "active": True,
            "level": "HIGH",
            "message": "Haul Road Friction Alert: Speed limits reduced, cycle times +25%."
        }
    else:
        friction_alert = {
            "active": False,
            "level": "NORMAL",
            "message": "Haul route friction within safe operating parameters."
        }

    # ---------------------------------------------------------
    # 4. High-Wall & Pit Bench Slope Instability Risk (NEW)
    # Triggered by deep water penetration: high 7-day rain + saturated ground
    # ---------------------------------------------------------
    if rainfall_7d_mm >= 80.0 and soil_moisture_index >= 0.75:
        slope_risk = {
            "level": "CRITICAL",
            "message": "Critical slope failure risk: Water saturation detected. Immediate bench inspection & clearance advised."
        }
    elif rainfall_7d_mm >= 50.0 and soil_moisture_index >= 0.6:
        slope_risk = {
            "level": "WARNING",
            "message": "Elevated slope instability: High pore pressure. Inspect high-wall face for tension cracks."
        }
    else:
        slope_risk = {
            "level": "STABLE",
            "message": "Pit high-walls and bench slopes within stable structural thresholds."
        }

    # ---------------------------------------------------------
    # 5. Haul Road Dust vs. Visibility Index (NEW)
    # Triggered by prolonged dry conditions: ground desiccated and loose
    # ---------------------------------------------------------
    if consecutive_dry_days >= 5 and soil_moisture_index <= 0.2:
        dust_risk = {
            "level": "HIGH_HAZARD",
            "message": "Severe haul road dust: Low visibility ahead. Dispatch water tankers at 2-hour intervals."
        }
    elif consecutive_dry_days >= 3 and soil_moisture_index <= 0.35:
        dust_risk = {
            "level": "MODERATE_HAZARD",
            "message": "Moderate dust build-up: Spray haul ramps prior to peak truck hauling cycles."
        }
    else:
        dust_risk = {
            "level": "NORMAL",
            "message": "Haul road surface moisture adequate; visibility within safe operating limits."
        }

    # Overall operational delay multiplier
    delay_factor = 0.25 if slope_risk["level"] == "CRITICAL" else (
        0.18 if waterlogging["level"] == "HIGH" else 0.05
    )

    return {
        "waterlogging": waterlogging,
        "road_risk": road_risk,
        "haul_friction": friction_alert,
        "slope_instability": slope_risk,
        "dust_visibility": dust_risk,
        "overall_delay_factor": delay_factor
    }


if __name__ == "__main__":
    print("--- Test Case 1: Monsoonal Downpour (Wet Extreme) ---")
    wet_test = evaluate_weather_impact(
        rainfall_48h_mm=42.0,
        soil_moisture_index=0.82,
        rainfall_7d_mm=95.0,
        consecutive_dry_days=0
    )
    for alert_name, details in wet_test.items():
        print(f"{alert_name}: {details}")

    print("\n--- Test Case 2: Prolonged Dry Spell (Dust Extreme) ---")
    dry_test = evaluate_weather_impact(
        rainfall_48h_mm=0.0,
        soil_moisture_index=0.15,
        rainfall_7d_mm=0.0,
        consecutive_dry_days=7
    )
    for alert_name, details in dry_test.items():
        print(f"{alert_name}: {details}")