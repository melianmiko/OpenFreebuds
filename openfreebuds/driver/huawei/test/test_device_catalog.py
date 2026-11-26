import pytest

from openfreebuds.driver.huawei.device_catalog import MODELS, color_name, describe_model


def test_freeclip_display_name_uses_market_name():
    """00014B stores the internal codename in the generated catalog, but the UI must show the market name."""
    assert MODELS["00014B"]["internal_name"] == "Dove"
    assert MODELS["00014B"]["marketing_name"] == "Dove"
    assert describe_model("00014B") == "HUAWEI FreeClip (00014B)"


@pytest.mark.parametrize(
    ("model", "code", "expected"),
    [
        ("000027", "00", "Ceramic white"),
        ("000027", "01", "Carbon crystal black"),
        ("000027", "02", "Whisper red"),
        ("000039", "01", "Ceramic white"),
        ("000039", "02", "Carbon crystal black"),
        ("00003B", "02", "Obsidian black"),
        ("00003B", "0D", "Dawn gold"),
        ("00003C", "00", "Frost silver"),
        ("00003C", "01", "Ceramic white"),
        ("00003C", "02", "Carbon crystal black"),
        ("00003C", "0F", "Ink white"),
        ("000117", "01", "Cherry pink"),
        ("000117", "02", "Obsidian black"),
        ("000117", "04", "Spruce green"),
        ("000117", "06", "Dawn white"),
        ("000129", "00", "Ceramic white"),
        ("000129", "01", "Frost silver"),
        ("000129", "02", "Whisper red"),
        ("00012A", "03", "Whisper"),
        ("00012A", "04", "Frost"),
        ("00012F", "02", "Obsidian black"),
        ("00012F", "04", "Spruce green"),
        ("00012F", "05", "Mint blue"),
        ("00012F", "08", "Osmanthus yellow"),
        ("000135", "00", "Ceramic white"),
        ("000135", "01", "Frost silver"),
        ("000135", "02", "Whisper red"),
        ("000159", "00", "Ceramic white"),
        ("000159", "01", "Frost silver"),
        ("00014D", "02", "Yadan black"),
        ("00014D", "04", "Yachuan green"),
        ("00014D", "05", "Blue"),
        ("00013F", "01", "Feather white"),
        ("00013F", "11", "Feather white"),
    ],
)
def test_legacy_marketing_colors(model, code, expected):
    """Official marketing colour keys for the 2019-2024 models verified from Huawei pages."""
    assert color_name(model, code) == expected
