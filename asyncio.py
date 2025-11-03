# queue_manager.py
"""
Queue Manager for Blood API
Maintains an asyncio queue for processing prompts asynchronously.
Routes all /ask requests to the Mind agent safely, even under heavy load.
"""

import asyncio
import httpx
import logging
import os
from typing import Any, Dict

# ---------------------------
# Configuration
# ---------------------------
logging.basicConfig(level=logging.INFO)

# Number of concurrent workers (configurable via env)
NUM_WORKERS: int = int(os.getenv("BLOOD_NUM_WORKERS", 2))

# URL for the Mind agent
MIND_AGENT_URL: str = os.getenv("MIND_AGENT_URL", "http://mind:8000/generate")

# Global asyncio queue
queue: asyncio.Queue = asyncio.Queue()

# ---------------------------
# Worker function
# ---------------------------
async def worker(name: str) -> None:
    """
    Worker that continuously processes items from the queue.
    Each item is a dict:
      {
          "prompt": str,
          "conversation_id": str,
          "future": asyncio.Future
      }
    """
    logging.info(f"🧠 Worker {name} started.")
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        while True:
            item: Dict[str, Any] = await queue.get()
            prompt = item.get("prompt")
            conversation_id = item.get("conversation_id", "default")
            future: asyncio.Future = item.get("future")

            try:
                # Send prompt to the Mind agent
                response = await client.post(
                    MIND_AGENT_URL,
                    json={"prompt": prompt, "conversation_id": conversation_id},
                )
                response.raise_for_status()
                output = response.json().get("output", "No response received.")

                # Set the result back to the waiting coroutine
                if not future.done():
                    future.set_result(output)

                logging.info(f"[{name}] ✅ Processed prompt ({len(prompt)} chars)")
            except Exception as e:
                logging.error(f"[{name}] ❌ Error processing prompt: {e}")
                if not future.done():
                    future.set_exception(e)
            finally:
                queue.task_done()

# ---------------------------
# Queue initialization
# ---------------------------
def start_workers(loop: asyncio.AbstractEventLoop = None) -> None:
    """
    Start background worker tasks in the event loop.
    """
    loop = loop or asyncio.get_event_loop()
    for i in range(NUM_WORKERS):
        loop.create_task(worker(f"worker-{i+1}"))
    logging.info(f"🩸 Started {NUM_WORKERS} async queue workers for Blood API.")

# ---------------------------
# Enqueue helper
# ---------------------------
async def enqueue_prompt(prompt: str, conversation_id: str = "default") -> str:
    """
    Enqueue a prompt and asynchronously wait for the Mind agent's result.
    """
    if not prompt:
        raise ValueError("Prompt cannot be empty")

    loop = asyncio.get_event_loop()
    future: asyncio.Future = loop.create_future()

    # Add the task to the queue
    await queue.put({
        "prompt": prompt,
        "conversation_id": conversation_id,
        "future": future,
    })

    logging.info(f"🧾 Enqueued prompt for conversation '{conversation_id}'")

    # Wait for the result from the worker
    return await future
