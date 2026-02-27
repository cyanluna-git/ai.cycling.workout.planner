"""Tests for ZWO import parsing — parse_zwo_element SteadyState handling."""

import xml.etree.ElementTree as ET
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
from import_zwo import parse_zwo_element


def _make_elem(tag, **attrs):
    """Helper: build an XML element with the given tag and attributes."""
    elem = ET.Element(tag)
    for k, v in attrs.items():
        elem.set(k, str(v))
    return elem


class TestParseZwoElementSteadyState:
    """SteadyState parsing: Power vs PowerHigh/PowerLow fallback."""

    def test_steadystate_with_power_attribute(self):
        """When Power is present it should be used directly."""
        elem = _make_elem('SteadyState', Power='0.88', Duration='300')
        result = parse_zwo_element(elem)
        assert result['type'] == 'steady'
        assert result['power'] == 88
        assert result['duration_sec'] == 300

    def test_steadystate_powerhigh_powerlow_equal(self):
        """When Power absent and PowerHigh==PowerLow, use that value."""
        elem = _make_elem('SteadyState', PowerHigh='0.50', PowerLow='0.50', Duration='60')
        result = parse_zwo_element(elem)
        assert result['power'] == 50
        assert result['duration_sec'] == 60

    def test_steadystate_powerhigh_powerlow_different(self):
        """When Power absent and PowerHigh!=PowerLow, average them."""
        elem = _make_elem('SteadyState', PowerHigh='0.80', PowerLow='0.60', Duration='120')
        result = parse_zwo_element(elem)
        # (0.80 + 0.60) / 2 = 0.70 => 70
        assert result['power'] == 70

    def test_steadystate_no_power_defaults_to_100(self):
        """When no Power/PowerHigh/PowerLow attrs, defaults to 1.0 (100%)."""
        elem = _make_elem('SteadyState', Duration='180')
        result = parse_zwo_element(elem)
        assert result['power'] == 100
        assert result['duration_sec'] == 180

    def test_steadystate_sufferfest_style(self):
        """Sufferfest-style: PowerHigh=PowerLow=1.350, no Power attr (sprint)."""
        elem = _make_elem('SteadyState', PowerHigh='1.350', PowerLow='1.350', Duration='5')
        result = parse_zwo_element(elem)
        assert result['power'] == 135
        assert result['duration_sec'] == 5
