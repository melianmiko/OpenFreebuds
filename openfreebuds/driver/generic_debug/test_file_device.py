import asyncio

from openfreebuds.driver.generic_debug.file_device import OfbFileDeviceDriver

FEATURE_FLAGS = [
    ("anc", "mode"),
    ("sound", "equalizer_rows"),
    ("sound", "adaptive_volume_supported"),
    ("sound", "spatial_audio_supported"),
    ("config", "box_tone_supported"),
    ("config", "head_control_supported"),
    ("config", "drop_reminder_supported"),
    ("config", "find_earbud_supported"),
    ("dual_connect", "devices"),
    ("service", "language_options"),
]


def test_full_feature_profile_exposes_every_module():
    async def run():
        driver = OfbFileDeviceDriver("full_feature")
        await driver.start()
        try:
            for group, prop in FEATURE_FLAGS:
                assert await driver.get_property(group, prop) is not None

            assert await driver.get_property("state", "headset_in_box") == "true"
            assert await driver.get_property("battery", "left") is not None

            await driver.set_property("config", "find_earbud", "ring:both")
            assert await driver.get_property("state", "find_earbud_ringing") == "left,right"

            await driver.set_property("config", "find_earbud", "stop:left")
            assert await driver.get_property("state", "find_earbud_ringing") == "right"

            await driver.set_property("config", "find_earbud", "stop:both")
            assert await driver.get_property("state", "find_earbud_ringing") == ""
        finally:
            await driver.stop()

    asyncio.run(run())
