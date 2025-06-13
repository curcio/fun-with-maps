#!/usr/bin/env python3
"""
Simple test script to debug specific regions individually.
"""

from utils import debug_individual_region

if __name__ == "__main__":
    print("🔍 Testing individual regions...")

    # Test Formosa
    print("\n" + "=" * 60)
    debug_individual_region("Argentina", "Formosa")

    # Test Mendoza
    print("\n" + "=" * 60)
    debug_individual_region("Argentina", "Mendoza")
