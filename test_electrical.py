# electrical.py


import unittest


# --- ฟังก์ชันคำนวณวงจร DC ---
def analyze_dc(voltage: float, resistance: float) -> dict:
    """คำนวณกระแสไฟฟ้า (A) และกำลังไฟฟ้า (W) ในวงจร DC

    :param voltage: แรงดันไฟฟ้า (V)
    :param resistance: ความต้านทานไฟฟ้า (Ω)
    :return: dict ที่มีค่า 'current_a' และ 'power_w'
    """
    if resistance <= 0:
        raise ValueError("Resistance must be greater than zero.")

    current = voltage / resistance
    power = voltage * current

    return {"current_a": current, "power_w": power}


# --- ชุดทดสอบ 3 Tests ---
class TestDCAnalyzer(unittest.TestCase):
    def test_known_values(self):
        """Test 1: คำนวณค่าตามปกติ (V=12V, R=6Ω -> I=2A, P=24W)"""
        result = analyze_dc(12, 6)
        self.assertAlmostEqual(result["current_a"], 2.0)
        self.assertAlmostEqual(result["power_w"], 24.0)

    def test_zero_voltage(self):
        """Test 2: แรงดันเป็น 0V (V=0V, R=10Ω -> I=0A, P=0W)"""
        result = analyze_dc(0, 10)
        self.assertAlmostEqual(result["current_a"], 0.0)
        self.assertAlmostEqual(result["power_w"], 0.0)

    def test_invalid_resistance(self):
        """Test 3: ความต้านทานเป็น 0 หรือติดลบ (ต้อง raise ValueError)"""
        with self.assertRaises(ValueError):
            analyze_dc(12, 0)
        with self.assertRaises(ValueError):
            analyze_dc(12, -5)


if __name__ == "__main__":
    unittest.main()