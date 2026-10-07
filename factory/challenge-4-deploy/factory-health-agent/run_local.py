"""Run the factory health check in your terminal. You approve or reject each work order."""

import asyncio
import logging

from factory_orchestration import build_workflow

# Hide framework warnings about approval bookkeeping. They are informational for this lab.
logging.getLogger("agent_framework").setLevel(logging.ERROR)

PROMPT = "Run a full health check on all five machines and open work orders where needed."


def show_outputs(result) -> None:
    for event in result:
        if event.type == "output":
            print(f"\n=== {event.executor_id} ===\n{getattr(event.data, 'text', event.data)}")


async def main() -> None:
    workflow = build_workflow()
    print(f"USER: {PROMPT}")
    result = await workflow.run(PROMPT)

    while True:
        show_outputs(result)
        requests = result.get_request_info_events()
        if not requests:
            break

        responses = {}
        for event in requests:
            call = event.data.function_call
            answer = input(f"\n[APPROVAL NEEDED] {call.name} {call.arguments}\nApprove? [y/N] ")
            responses[event.request_id] = event.data.to_function_approval_response(approved=answer.strip().lower() == "y")
        result = await workflow.run(responses=responses)


if __name__ == "__main__":
    asyncio.run(main())
