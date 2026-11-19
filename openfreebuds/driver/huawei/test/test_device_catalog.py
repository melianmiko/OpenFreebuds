from openfreebuds.driver.huawei.device_catalog import MODELS, describe_model


def test_freeclip_display_name_uses_market_name():
    """00014B stores the internal codename in the generated catalog, but the UI must show the market name."""
    assert MODELS["00014B"]["internal_name"] == "Dove"
    assert MODELS["00014B"]["marketing_name"] == "Dove"
    assert describe_model("00014B") == "HUAWEI FreeClip (00014B)"
