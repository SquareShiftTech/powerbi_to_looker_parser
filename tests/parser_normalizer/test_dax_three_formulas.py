"""Quick test that the 3 previously failing real-world formulas now parse."""

import pytest
from powerbi_to_looker.dax import parse_formula

FORMULA1 = "DIVIDE( [Total Conversions],sum(marketing_campaign_data[Impressions]),0)"
FORMULA2 = "TOTALYTD([Total Revenue],marketing_campaign_data[Date].[Date])"
FORMULA3 = "CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(DATESYTD(marketing_campaign_data[Date].[Date])))"


def test_lowercase_sum_parses():
    ast, err = parse_formula(FORMULA1)
    assert ast is not None, err
    assert err is None


def test_hierarchy_date_date_parses():
    ast, err = parse_formula(FORMULA2)
    assert ast is not None, err
    assert err is None


def test_calculate_hierarchy_parses():
    ast, err = parse_formula(FORMULA3)
    assert ast is not None, err
    assert err is None
