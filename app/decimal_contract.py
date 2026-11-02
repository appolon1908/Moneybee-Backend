"""Keep the reviewed Decimal JSON-schema contract explicit across Pydantic updates."""

from decimal import Decimal
from typing import Annotated

from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema


# These are the two reviewed Decimal shapes used by this repository. New shapes
# require a contract review rather than inheriting a dependency's schema default.
PUBLISHED_PATTERNS = {
    (None, None): r"^(?!^[-+.]*$)[+-]?0*\d*\.?\d*$",
    (20, 2): r"^(?!^[-+.]*$)[+-]?0*(?:\d{0,18}|(?=[\d.]{1,21}0*$)\d{0,18}\.\d{0,2}0*$)",
}


class PublishedDecimalPattern:
    def __get_pydantic_json_schema__(
        self, schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Only schema metadata changes: Decimal validators and serializers stay native.
        if schema["type"] != "decimal":
            raise ValueError("Published Decimal contract requires a Decimal core schema")
        result = handler(schema)
        shape = (schema.get("max_digits"), schema.get("decimal_places"))
        if shape not in PUBLISHED_PATTERNS:
            raise ValueError("Unreviewed Decimal precision contract")
        pattern = PUBLISHED_PATTERNS[shape]
        branches = result.get("anyOf", [result])
        strings = [branch for branch in branches if branch.get("type") == "string"]
        if len(strings) != 1:
            raise ValueError("Published Decimal contract requires one string schema")
        strings[0]["pattern"] = pattern
        return result


ContractDecimal = Annotated[Decimal, PublishedDecimalPattern()]
