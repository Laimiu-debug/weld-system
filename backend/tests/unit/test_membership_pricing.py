import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.membership_admin import validated_plan_data


def test_membership_price_validation_normalizes_money_and_quotas() -> None:
    result = validated_plan_data(
        {
            "id": "personal_team",
            "name": "个人团队版",
            "monthly_price": "19.999",
            "quarterly_price": 50,
            "yearly_price": 180,
            "max_wps_files": "100",
        },
        creating=True,
    )

    assert result["monthly_price"] == 20.0
    assert result["max_wps_files"] == 100


@pytest.mark.parametrize(
    "payload",
    [
        {"id": "INVALID-ID", "name": "x"},
        {"id": "valid_plan", "name": "x", "monthly_price": -1},
        {"id": "valid_plan", "name": "x", "max_wps_files": -1},
    ],
)
def test_membership_price_validation_rejects_invalid_values(payload) -> None:
    with pytest.raises(HTTPException) as exc_info:
        validated_plan_data(payload, creating=True)

    assert exc_info.value.status_code == 422
