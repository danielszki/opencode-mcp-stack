# Example: a short question in a temporary chat

Input, run on 2026-11-24 (the web app showed 9 credits used by this call):

```bash
python3 scripts/gemini_web.py --model hydrogen --effort medium \
  --prompt "In three short bullets, say when a mutex is the right tool and when a semaphore is."
```

Exit code: 0. Output, unedited (stderr first, then stdout):

```text
gemini_web: session from edge
gemini_web: answered by '4 Hydrogen Medium', 24.5s, 5h credits 636->627

* **Mutex (Mutual Exclusion):** Use when **only one thread** should access a shared resource at a time, and the **same thread** that locks the resource must be the one to unlock it (ownership).
* **Counting Semaphore:** Use when you need to limit concurrent access to a pool of **multiple identical resources** (e.g., allowing up to $N$ threads to use $N$ database connections simultaneously).
* **Binary Semaphore:** Use for **signaling between threads**, where one thread waits for an event (`wait`) and a *different* thread notifies it when the work is done (`post`), since semaphores have no concept of thread ownership.
```
