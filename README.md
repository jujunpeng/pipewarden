# pipewarden

A lightweight Python library for defining and monitoring ETL pipeline health checks with alerting hooks.

---

## Installation

```bash
pip install pipewarden
```

---

## Usage

```python
from pipewarden import Pipeline, HealthCheck, alert

# Define a pipeline with health checks
pipeline = Pipeline(name="daily_sales_etl")

@pipeline.check
def row_count_check(context):
    return context["row_count"] > 0

@pipeline.check
def null_threshold_check(context):
    return context["null_ratio"] < 0.05

# Register an alerting hook
@pipeline.on_failure
def notify_slack(check_name, context):
    alert.slack(webhook_url="https://hooks.slack.com/...", message=f"Check failed: {check_name}")

# Run all checks
results = pipeline.run(context={"row_count": 1500, "null_ratio": 0.02})
print(results.summary())
# => Pipeline 'daily_sales_etl': 2/2 checks passed ✓
```

---

## Features

- Define named health checks as plain Python functions
- Register alerting hooks for Slack, email, or custom callbacks
- Lightweight with no required dependencies beyond the standard library
- Easy integration into existing ETL workflows

---

## License

This project is licensed under the [MIT License](LICENSE).