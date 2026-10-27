from demo import tool_diagnose_listing, SAMPLE_PRODUCT

def test_flags_high_quality_and_dup():
    issues = tool_diagnose_listing(SAMPLE_PRODUCT)
    assert any("high quality" in x for x in issues)
    assert any("重复" in x for x in issues)
