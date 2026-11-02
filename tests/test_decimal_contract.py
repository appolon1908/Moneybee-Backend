import json
from decimal import Decimal
from pathlib import Path
from typing import Annotated
import uuid

import pytest
from pydantic import Field, TypeAdapter, ValidationError

from app.decimal_contract import ContractDecimal
from app.financial_schemas import PostingInput
from app.schemas import ApplicationRead, ApplicationUpdate


def test_application_decimal_schema_retains_the_published_contract():
    baseline = json.loads((Path(__file__).parents[1] / "openapi.json").read_text())
    published = baseline["components"]["schemas"]["ApplicationRead"]["properties"]
    generated = ApplicationRead.model_json_schema(mode="serialization")["properties"]
    for field in ("requested_amount", "monthly_revenue"):
        assert generated[field] == published[field]


def test_decimal_request_schema_preserves_numeric_constraints_and_string_pattern():
    generated = ApplicationUpdate.model_json_schema()["properties"]["requested_amount"]
    branches = generated["anyOf"]
    assert next(branch for branch in branches if branch.get("type") == "number")["minimum"] == 1000
    assert "pattern" in next(branch for branch in branches if branch.get("type") == "string")
    with pytest.raises(ValidationError):
        ApplicationUpdate(requested_amount="999.99", version=1)
    with pytest.raises(ValidationError):
        ApplicationUpdate(requested_amount="not-money", version=1)


def test_decimal_response_keeps_exact_strings_and_precision():
    value = ApplicationRead(
        id=uuid.uuid4(), lead_id=uuid.uuid4(), borrower_subject=None,
        borrower_organization_id=None, requested_amount=Decimal("123456789.0123456789"),
        monthly_revenue=Decimal("1000.50"), time_in_business_months=12,
        industry=None, state=None, status="DRAFT", completion_percentage=0, version=1,
    )
    result = json.loads(value.model_dump_json())
    assert result["requested_amount"] == "123456789.0123456789"
    assert result["monthly_revenue"] == "1000.50"


def test_posting_decimal_precision_and_positive_amount_checks_remain_enforced():
    schema = PostingInput.model_json_schema()["properties"]["amount"]
    assert "pattern" in next(branch for branch in schema["anyOf"] if branch["type"] == "string")
    for amount in ("1.001", "0", "1000000000000000000.00"):
        with pytest.raises(ValidationError):
            PostingInput(account_id=uuid.uuid4(), side="DEBIT", amount=amount)
    assert PostingInput(account_id=uuid.uuid4(), side="DEBIT", amount="1.50").amount == Decimal("1.50")


def test_schema_annotation_does_not_change_native_decimal_validation():
    native, contract = TypeAdapter(Decimal), TypeAdapter(ContractDecimal)
    for amount in ("1e2", "-0.005", "+001.50", "123456789.0123456789"):
        assert contract.validate_python(amount) == native.validate_python(amount)
    with pytest.raises(ValidationError):
        contract.validate_python("not-money")


def test_new_decimal_precision_shape_requires_contract_review():
    adapter = TypeAdapter(Annotated[ContractDecimal, Field(max_digits=7, decimal_places=3)])
    with pytest.raises(ValueError, match="Unreviewed Decimal precision contract"):
        adapter.json_schema()
