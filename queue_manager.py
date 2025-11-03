import asyncio
import logging

# Global async queue
queue = asyncio.Queue()

async def handle_prompt(prompt: str, conversation_id: str):
    """Simulate AI processing for a prompt."""
    logging.info(f"🧠 Processing prompt for {conversation_id}: {prompt}")
    await asyncio.sleep(1)  # Simulated delay
    return f"Response to: {prompt}"

async def worker():
    """Worker task that processes queued prompts asynchronously."""
    while True:
        prompt, conversation_id, future = await queue.get()
        try:
            result = await handle_prompt(prompt, conversation_id)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        finally:
            queue.task_done()

async def enqueue_prompt(prompt: str, conversation_id: str):
    """Add a prompt to the queue and wait for the response."""
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    await queue.put((prompt, conversation_id, future))
    return await future

def start_workers(loop=None, num_workers=2):
    """Start background async workers."""
    loop = loop or asyncio.get_event_loop()
    for _ in range(num_workers):
        loop.create_task(worker())
    logging.info(f"🚀 Started {num_workers} async workers.")
