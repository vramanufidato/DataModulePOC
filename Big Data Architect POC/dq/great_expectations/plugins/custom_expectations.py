"""Custom expectations for retail domain."""
from typing import Any, Dict, Optional

from great_expectations.core.expectation_configuration import ExpectationConfiguration
from great_expectations.execution_engine import ExecutionEngine
from great_expectations.expectations.expectation import ColumnMapExpectation
from great_expectations.expectations.metrics import ColumnMapMetricProvider
from great_expectations.expectations.metrics.import_manager import F, sa

class ColumnValuesAreValidOrderIds(ColumnMapMetricProvider):
    condition_metric_name = "column_values.valid_order_ids"

    @column_condition_partial(engine="sqlalchemy")
    def _sqlalchemy(cls, column, **kwargs):
        return column.op("~")(sa.text("'^ORD-[0-9]{6}$'"))

    @column_condition_partial(engine="spark")
    def _spark(cls, column, **kwargs):
        return column.rlike("^ORD-[0-9]{6}$")

class ExpectColumnValuesToBeValidOrderIds(ColumnMapExpectation):
    """Expect column values to be valid order IDs."""
    map_metric = "column_values.valid_order_ids"
    success_keys = ("mostly",)
    default_kwarg_values = {"mostly": 1.0}

    examples = [{
        "data": {"order_id": ["ORD-100001", "ORD-100002"]},
        "tests": [{"title": "basic", "exact_match_out": False,
                   "in": {"column": "order_id"}, "out": {"success": True}}]
    }]
