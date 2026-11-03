import math


def analyze_dc(voltage_v: float, resistance_ohm: float) -> dict[str, float]:
    """Calculate current and power for a DC source and resistor."""
    if isinstance(voltage_v, bool) or not isinstance(voltage_v, (int, float)):
        raise ValueError("Voltage must be a number.")
    if isinstance(resistance_ohm, bool) or not isinstance(resistance_ohm, (int, float)):
        raise ValueError("Resistance must be a number.")
    if not math.isfinite(voltage_v):
        raise ValueError("Voltage must be finite.")
    if not math.isfinite(resistance_ohm) or resistance_ohm <= 0:
        raise ValueError("Resistance must be finite and greater than zero.")

    current_a = voltage_v / resistance_ohm
    power_w = voltage_v * current_a
    return {"current_a": current_a, "power_w": power_w}


def main() -> int:
    try:
        voltage_v = float(input("Voltage (V): "))
        resistance_ohm = float(input("Resistance (ohm): "))
        result = analyze_dc(voltage_v, resistance_ohm)
    except ValueError as error:
        print(f"Error: {error}")
        return 1

    print(f"Current: {result['current_a']:.3f} A")
    print(f"Power: {result['power_w']:.3f} W")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
