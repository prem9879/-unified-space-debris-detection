#!/usr/bin/env python
"""
Space Debris Command Center - System Status Dashboard
Shows all running services and their endpoints
"""

import requests
import json
from datetime import datetime

def check_endpoint(url: str, timeout: float = 2) -> tuple[bool, str]:
    """Check if endpoint is accessible and return status"""
    try:
        resp = requests.get(url, timeout=timeout)
        return resp.status_code == 200, str(resp.status_code)
    except Exception as e:
        return False, str(e)[:30]

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("\n" + "="*80)
    print("SPACE DEBRIS COMMAND CENTER - SYSTEM STATUS")
    print(f"Generated: {now}")
    print("="*80 + "\n")
    
    services = {
        "FastAPI Backend": {
            "url": "http://127.0.0.1:8000",
            "health_endpoint": "/healthz",
            "endpoints": {
                "Health Check": "/healthz",
                "Readiness": "/readyz",
                "Metrics": "/metrics",
                "API Documentation": "/docs",
            }
        },
        "React Frontend": {
            "url": "http://localhost:5173",
            "health_endpoint": "/",
            "endpoints": {
                "Dashboard": "/",
            }
        },
    }
    
    print("SERVICES STATUS")
    print("-"*80)
    
    all_healthy = True
    
    for service_name, service_config in services.items():
        base_url = service_config["url"]
        health_ep = service_config.get("health_endpoint", "/")
        healthy, status = check_endpoint(base_url + health_ep)
        
        status_icon = "✓ UP" if healthy else "✗ DOWN"
        print(f"\n{status_icon:8} {service_name}")
        print(f"{'':8} Base URL: {base_url}")
        
        if healthy:
            for endpoint_name, endpoint_path in service_config.get("endpoints", {}).items():
                full_url = base_url + endpoint_path
                ep_healthy, ep_status = check_endpoint(full_url)
                ep_icon = "✓" if ep_healthy else "✗"
                print(f"{'':8} {ep_icon} {endpoint_name:30} {full_url}")
        else:
            all_healthy = False
            print(f"{'':8} ✗ Service is not responding")
            all_healthy = False
    
    # Test API authentication
    print("\n" + "-"*80)
    print("API AUTHENTICATION TEST")
    print("-"*80)
    
    try:
        resp = requests.post(
            "http://127.0.0.1:8000/api/v1/auth/token",
            json={"username": "analyst", "password": "analyst123"},
            timeout=2
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ Authentication successful")
            print(f"  - Role: {data.get('role', 'unknown')}")
            print(f"  - Token Type: {data.get('token_type', 'unknown')}")
            
            # Check protected endpoints
            token = data.get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            protected_endpoints = {
                "Models Registry": "/api/v1/models/",
                "SLO Monitoring": "/api/v1/monitoring/slo",
                "Alerts History": "/api/v1/alerts/history",
            }
            
            print(f"\nProtected Endpoints:")
            for name, path in protected_endpoints.items():
                r = requests.get(f"http://127.0.0.1:8000{path}", headers=headers, timeout=2)
                icon = "✓" if r.status_code == 200 else "✗"
                print(f"  {icon} {name:30} {r.status_code}")
        else:
            print(f"✗ Authentication failed: {resp.status_code}")
            all_healthy = False
    except Exception as e:
        print(f"✗ Authentication test error: {str(e)[:60]}")
        all_healthy = False
    
    # Summary
    print("\n" + "="*80)
    if all_healthy:
        print("STATUS: ✓ ALL SYSTEMS OPERATIONAL")
    else:
        print("STATUS: ✗ SOME SERVICES MAY BE DOWN")
    print("="*80 + "\n")
    
    # Quick links
    print("QUICK LINKS")
    print("-"*80)
    print("Frontend Dashboard:   http://localhost:5173")
    print("API Documentation:    http://127.0.0.1:8000/docs")
    print("Health Check:         http://127.0.0.1:8000/healthz")
    print("Metrics:              http://127.0.0.1:8000/metrics")
    print("\nDEMO CREDENTIALS")
    print("-"*80)
    print("Username: analyst")
    print("Password: analyst123")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
