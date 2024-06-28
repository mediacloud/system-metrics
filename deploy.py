from prefect import flow

if __name__ == "__main__":
    flow.from_source(
        source="https://github.com/mediacloud/system-metrics.git",
        entrypoint="main.py:RunMetrics",
    ).deploy(
        name="daily-metrics",
        work_pool_name="Guerin",
        cron="0 0 * * *",
    )