"""
Site rebuild endpoint — triggers frontend build + prerender from the admin panel.
"""
from fastapi import APIRouter, Depends
from auth import get_current_admin
import asyncio
import subprocess
import os
import time
from datetime import datetime, timezone

router = APIRouter()

# Build state (in-process singleton)
_build_state = {
    "status": "idle",       # idle | building | done | error
    "started_at": None,
    "finished_at": None,
    "duration_s": None,
    "pages": None,
    "error": None,
    "log_tail": "",
}


@router.post("/api/admin/rebuild")
async def trigger_rebuild(admin=Depends(get_current_admin)):
    """Trigger a frontend rebuild + prerender in the background."""
    if _build_state["status"] == "building":
        return {"status": "building", "message": "Build already in progress"}

    _build_state["status"] = "building"
    _build_state["started_at"] = datetime.now(timezone.utc).isoformat()
    _build_state["finished_at"] = None
    _build_state["error"] = None
    _build_state["pages"] = None
    _build_state["log_tail"] = ""

    asyncio.create_task(_run_build())
    return {"status": "building", "message": "Build started"}


@router.get("/api/admin/rebuild/status")
async def rebuild_status(admin=Depends(get_current_admin)):
    """Get current build status."""
    return _build_state


async def _run_build():
    """Run the build in a subprocess."""
    start = time.monotonic()
    frontend_dir = "/app/frontend"

    try:
        # Step 1: Export seed data
        _build_state["log_tail"] = "Exporting seed data..."
        seed_proc = await asyncio.create_subprocess_exec(
            "python3", "-c", _SEED_EXPORT_SCRIPT,
            cwd="/app/backend",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await seed_proc.wait()

        # Step 2: Run yarn build (includes postbuild-prerender.js)
        _build_state["log_tail"] = "Building frontend..."
        env = {**os.environ, "GENERATE_SOURCEMAP": "false", "ESLINT_NO_DEV_ERRORS": "true"}
        proc = await asyncio.create_subprocess_exec(
            "yarn", "build",
            cwd=frontend_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode("utf-8", errors="replace")

        if proc.returncode != 0:
            _build_state["status"] = "error"
            _build_state["error"] = output[-500:]
            _build_state["log_tail"] = output[-500:]
            return

        # Parse page count from output
        pages = None
        for line in output.split("\n"):
            if "Pre-rendered:" in line:
                try:
                    pages = int(line.split("Pre-rendered:")[1].split("pages")[0].strip())
                except (ValueError, IndexError):
                    pass
                break

        elapsed = round(time.monotonic() - start, 1)
        _build_state["status"] = "done"
        _build_state["finished_at"] = datetime.now(timezone.utc).isoformat()
        _build_state["duration_s"] = elapsed
        _build_state["pages"] = pages
        _build_state["log_tail"] = f"Build complete: {pages} pages in {elapsed}s"

    except Exception as e:
        _build_state["status"] = "error"
        _build_state["error"] = str(e)
        _build_state["log_tail"] = str(e)


_SEED_EXPORT_SCRIPT = '''
import asyncio, os, json
from motor.motor_asyncio import AsyncIOMotorClient

async def export_seed():
    from dotenv import load_dotenv
    load_dotenv()
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
    db = client[os.environ.get("DB_NAME", "brightluxx")]
    skip = {"performance_metrics", "analytics_events", "upload_chunks", "upload_sessions",
            "chat_sessions", "leads", "contact_submissions", "support_tickets",
            "supplier_registrations", "seo_bulk_jobs", "reviews"}
    seed = {}
    for col_name in sorted(await db.list_collection_names()):
        if col_name.startswith("system.") or col_name in skip:
            continue
        docs = []
        async for doc in db[col_name].find({}):
            doc["_id"] = str(doc["_id"])
            for k, v in doc.items():
                if hasattr(v, "isoformat"):
                    doc[k] = v.isoformat()
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            for ik, iv in item.items():
                                if hasattr(iv, "isoformat"):
                                    item[ik] = iv.isoformat()
            docs.append(doc)
        if docs:
            seed[col_name] = docs
    with open("seed_data_full.json", "w") as f:
        json.dump(seed, f, default=str)
    client.close()

asyncio.run(export_seed())
'''
