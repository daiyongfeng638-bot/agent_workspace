import src.config as config  # noqa: E402


def test_config_constants():
    assert config.SCREENSHOT_INTERVAL_MINUTES == 15
    assert config.POSITION_CHECK_INTERVAL_SECONDS == 180
    assert config.MAX_SINGLE_DIRECTION_LOTS == 30
    assert config.COOLDOWN_AFTER_EXIT_MINUTES == 15
    assert config.AUTO_FILL_ORDER is True
    assert config.AUTO_SUBMIT_ORDER is False
    assert config.CONFIDENCE_THRESHOLD == 75
    assert config.DEFAULT_LOT_SIZE == 5


def test_config_regions_exist():
    for region in [config.CHART_REGION, config.ORDER_PANEL_REGION, config.POSITION_REGION, config.PRICE_REGION]:
        assert {"left", "top", "width", "height"}.issubset(region.keys())
