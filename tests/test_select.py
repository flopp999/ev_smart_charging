"""Test ev_smart_charging select."""
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ev_smart_charging import (
    async_setup_entry,
    async_unload_entry,
)
from custom_components.ev_smart_charging.const import (
    CONF_READY_HOUR,
    CONF_START_HOUR,
    DOMAIN,
    READY_HOUR_NONE,
    SELECT,
    START_HOUR_NONE,
)
from custom_components.ev_smart_charging.coordinator import (
    EVSmartChargingCoordinator,
)
from custom_components.ev_smart_charging.select import (
    EVSmartChargingSelectReadyHour,
    EVSmartChargingSelectStartHour,
)

from .const import MOCK_CONFIG_MIN_SOC

# We can pass fixtures as defined in conftest.py to tell pytest to use the fixture
# for a given test. We can also leverage fixtures and mocks that are available in
# Home Assistant using the pytest_homeassistant_custom_component plugin.
# Assertions allow you to verify that the return value of whatever is on the left
# side of the assertion matches with the right side.

# pylint: disable=unused-argument
async def test_select(hass, bypass_validate_input_sensors):
    """Test sensor properties."""
    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_MIN_SOC, entry_id="test"
    )

    # Set up the entry and assert that the values set during setup are where we expect
    # them to be. Because we have patched the BlueprintDataUpdateCoordinator.async_get_data
    # call, no code from custom_components/integration_blueprint/api.py actually runs.
    assert await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()

    assert DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]
    assert isinstance(
        hass.data[DOMAIN][config_entry.entry_id], EVSmartChargingCoordinator
    )
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Get the selects
    select_start_hour: EVSmartChargingSelectStartHour = hass.data["entity_components"][
        SELECT
    ].get_entity("select.none_charge_start_time")
    select_ready_hour: EVSmartChargingSelectReadyHour = hass.data["entity_components"][
        SELECT
    ].get_entity("select.none_charge_completion_time")
    assert select_start_hour
    assert select_ready_hour
    assert isinstance(select_start_hour, EVSmartChargingSelectStartHour)
    assert isinstance(select_ready_hour, EVSmartChargingSelectReadyHour)

    # Test the selects

    assert select_start_hour.state == MOCK_CONFIG_MIN_SOC[CONF_START_HOUR]
    assert select_ready_hour.state == MOCK_CONFIG_MIN_SOC[CONF_READY_HOUR]

    await select_start_hour.async_select_option("00:00")
    assert coordinator.start_hour_local == 0
    await select_start_hour.async_select_option("13:00")
    assert coordinator.start_hour_local == 13
    await select_start_hour.async_select_option("None")
    assert coordinator.start_hour_local == START_HOUR_NONE

    await select_ready_hour.async_select_option("00:00")
    assert coordinator.ready_hour_local == 24
    await select_ready_hour.async_select_option("13:00")
    assert coordinator.ready_hour_local == 13
    await select_ready_hour.async_select_option("None")
    assert coordinator.ready_hour_local == READY_HOUR_NONE

    # Unload the entry and verify that the data has been removed
    assert await async_unload_entry(hass, config_entry)
    assert config_entry.entry_id not in hass.data[DOMAIN]