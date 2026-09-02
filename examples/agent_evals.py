#!/usr/bin/env python3
"""Run a Fabricate Agent Evals suite with a framework-agnostic agent."""

import os
from typing import List

from dotenv import load_dotenv

from tonic_fabricate import (
    AgentEvalsClient,
    CreateRunInput,
    OpenInferenceSpan,
)

load_dotenv()


def run_agent(task_input: str) -> List[OpenInferenceSpan]:
    """Replace this example span with spans captured from your agent."""
    return [
        {
            "name": "example-agent",
            "attributes": {
                "openinference.span.kind": "LLM",
                "llm.input_messages.0.message.role": "user",
                "llm.input_messages.0.message.content": task_input,
                "llm.output_messages.0.message.role": "assistant",
                "llm.output_messages.0.message.content": "Replace this with your agent's response.",
                "llm.token_count.prompt": 100,
                "llm.token_count.completion": 20,
                "llm.token_count.prompt_details.cache_read": 40,
                "llm.token_count.prompt_details.cache_write": 30,
                "llm.token_count.prompt_details.cache_write_5m": 10,
                "llm.token_count.prompt_details.cache_write_1h": 20,
            },
        }
    ]


def required_environment(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def main() -> None:
    project_id = required_environment("FABRICATE_PROJECT_ID")
    suite_name = os.environ.get("FABRICATE_SUITE_NAME", "Agent Eval Tasks")
    suite_id = os.environ.get("FABRICATE_SUITE_ID")
    suite_version = os.environ.get("FABRICATE_SUITE_VERSION")
    client = AgentEvalsClient()

    suite = client.find_suite(
        project_id,
        id=suite_id,
        name=None if suite_id else suite_name,
        version=int(suite_version) if suite_version else None,
    )
    if suite is None:
        version_hint = f" version {suite_version}" if suite_version else ""
        raise RuntimeError(f"Suite {suite_name!r}{version_hint} was not found")

    tasks = client.list_tasks(suite["id"])
    run_input: CreateRunInput = {
        "suite_id": suite["id"],
        "model": os.environ.get("AGENT_MODEL", "example-agent"),
    }
    if os.environ.get("GIT_BRANCH"):
        run_input["git_branch"] = os.environ["GIT_BRANCH"]
    if os.environ.get("GIT_SHA"):
        run_input["git_sha"] = os.environ["GIT_SHA"]

    run = client.create_run(project_id, run_input)
    try:
        for task in tasks:
            reported = client.report_trial(
                run["id"],
                {
                    "task_key": task["key"],
                    "transcript": {"messages": run_agent(task["input"])},
                    "grade": True,
                },
            )
            graded = client.wait_for_grading(reported["id"], timeout_seconds=300)
            result = "PASS" if graded["passed"] else "FAIL"
            print(f"{task['key']}: {result}")
    except Exception:
        client.update_run(run["id"], {"status": "failed"})
        raise
    else:
        client.update_run(run["id"], {"status": "completed"})


if __name__ == "__main__":
    main()
