from tools import lookup, calculate

def test_lookup_finds_correct_number():
    result = lookup("Ossbridge", "population")
    assert "NR-01" in result
    assert "52,904" in result # 2025 population

def test_lookup_handles_misspelled_and_similar_names():
    result = lookup("Ossbrige", "population")
    assert "did you mean Ossbridge or Ossford?" in result
    assert "error" in result

def test_lookup_ignores_archived_profile():
    result = lookup("Tarnvale", "population")
    assert "NR-03" in result # New
    assert "NR-13" not in result # Achieve

def test_lookup_applies_correction_for_brightwater():
    result = lookup("Brightwater", "area")
    assert "NR-05" in result
    assert "NR-16" in result

def test_lookup_handles_unknown_district():
    result = lookup("Neverland", "population")
    assert "error" in result
    assert "no district named Neverland found" in result



def test_calculate_basic_math():
    result = calculate("48317 * 1.0947")
    assert "52892" in result[:5] # 52892.6209

def test_calculate_refuses_import_os():
    result = calculate("__import__('os').system('echo hi')")
    assert "error" in result
    assert "Unsupported syntax" in result

def test_calculate_refuses_class_access():
    result = calculate("(1).__class__")
    assert "error" in result
    assert "Unsupported syntax" in result

def test_calculate_refuses_huge_exponents():
    result = calculate("9**9**9")
    assert "error" in result
    assert "too large" in result

def test_calculate_handles_division_by_zero():
    result = calculate("10 / 0")
    assert "error" in result
    assert "division by zero" in result