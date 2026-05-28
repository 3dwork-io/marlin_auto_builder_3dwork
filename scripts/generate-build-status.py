#!/usr/bin/env python3
"""Generate BUILD_STATUS.md from workflow run results.

Called by CI after all builds complete.
Environment: GITHUB_TOKEN, RUN_ID, GITHUB_API_URL, GITHUB_REPOSITORY
"""
import json, os, sys, urllib.request, urllib.error
from collections import OrderedDict

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", os.environ.get("COMMIT_TOKEN", ""))
RUN_ID = os.environ.get("RUN_ID", "")
REPO = os.environ.get("GITHUB_REPOSITORY", "3dwork-io/marlin_auto_builder_3dwork")
API_BASE = os.environ.get("GITHUB_API_URL", "https://api.github.com")

MARLIN_CONFIG_REPO = "MarlinFirmware/Configurations"

def api_get(path):
    url = f"{API_BASE}/repos/{REPO}/{path}"
    req = urllib.request.Request(url)
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": str(e), "status": e.code}
    except urllib.error.URLError as e:
        return {"error": str(e)}

def gh_anchor(text):
    """Match GitHub's heading anchor generation."""
    slug = text.lower()
    slug = ''.join(c for c in slug if c.isalnum() or c in ' -')
    slug = '-'.join(slug.split())
    return slug

def get_fw_filename(build_path, lang):
    """Return 'firmware.bin' or 'firmware.hex' based on what exists."""
    for fname in ["firmware.bin", "firmware.hex"]:
        if os.path.isfile(os.path.join(build_path, lang, fname)):
            return fname
    return "firmware.bin"

def get_config_source_link(official_path, version):
    if official_path:
        branch = f"release-{version}" if version else "master"
        return f"https://github.com/{MARLIN_CONFIG_REPO}/tree/{branch}/{official_path}"
    return ""

def get_error_cause(job):
    """Determine error cause from job steps."""
    cause_parts = []
    for step in job.get("steps", []):
        if step.get("conclusion") == "failure":
            name = step["name"]
            if "Prepare configs" in name:
                cause_parts.append("No official config at tag")
            elif "Compile firmware" in name:
                cause_parts.append("Compilation error")
            elif "Push" in name:
                cause_parts.append("Git push failed")
            else:
                cause_parts.append(name)
    return "; ".join(cause_parts) if cause_parts else "Unknown error"

def main():
    if not RUN_ID:
        print("ERROR: RUN_ID not set", file=sys.stderr)
        sys.exit(1)

    try:
        with open("board-matrix.json") as f:
            matrix = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR: Cannot read board-matrix.json: {e}", file=sys.stderr)
        sys.exit(1)

    version = ""
    try:
        with open("VERSION") as f:
            version = f.read().strip()
    except FileNotFoundError:
        pass

    # Fetch all jobs from current workflow run
    jobs_data = []
    page = 1
    while True:
        result = api_get(f"actions/runs/{RUN_ID}/jobs?per_page=100&page={page}")
        if "error" in result:
            print(f"WARNING: API error at page {page}: {result['error']}", file=sys.stderr)
            break
        jobs = result.get("jobs", [])
        if not jobs:
            break
        jobs_data.extend(jobs)
        if len(jobs) < 100:
            break
        page += 1

    if not jobs_data:
        print("ERROR: No jobs data fetched", file=sys.stderr)
        sys.exit(1)

    # Build job status lookup
    job_map = {}
    for job in jobs_data:
        name = job["name"]
        if name in ("Detect Marlin Version", "Update VERSION file", "Generate Build Status"):
            continue
        for prefix in ["Creality ", "delta+Geeetech ", "Wanhao+Anet+Tronxy ",
                        "BIQU+Sovol+AnyCubic ", "Artillery+Tevo+Kingroon ", "Other "]:
            if name.startswith(prefix):
                label = name[len(prefix):]
                job_map[label] = {
                    "conclusion": job.get("conclusion", "unknown"),
                    "html_url": job.get("html_url", ""),
                    "steps": job.get("steps", []),
                }
                break

    # Count unknown boards (boards not in the run data)
    total_unknown = 0

    # Group by vendor
    vendors = OrderedDict()
    for entry in matrix:
        bp = entry["board_path"]
        parts = bp.split("/")
        vendor = parts[0]
        printer = "/".join(parts[1:])
        board_env = entry.get("board", "?")
        build_path = entry.get("build_path", "")
        official_path = entry.get("official_path", "")

        label = " - ".join(parts).replace("_", " ")
        label2 = " - ".join(parts)
        job_info = job_map.get(label) or job_map.get(label2)

        status = "unknown"
        job_url = ""
        error_cause = ""
        if job_info:
            status = job_info["conclusion"]
            job_url = job_info["html_url"]
            if status == "failure":
                error_cause = get_error_cause(job_info)

        if vendor not in vendors:
            vendors[vendor] = {"count": 0, "success": 0, "fail": 0, "unknown": 0, "boards": []}

        vendors[vendor]["count"] += 1
        if status == "success":
            vendors[vendor]["success"] += 1
        elif status == "failure":
            vendors[vendor]["fail"] += 1
        else:
            vendors[vendor]["unknown"] += 1
            total_unknown += 1

        dl_link_en = ""
        dl_link_es = ""
        if status == "success" and build_path:
            fw_en = get_fw_filename(build_path, "en")
            fw_es = get_fw_filename(build_path, "es")
            dl_link_en = f"https://github.com/{REPO}/raw/master/{build_path}/en/{fw_en}"
            dl_link_es = f"https://github.com/{REPO}/raw/master/{build_path}/es/{fw_es}"

        config_link = get_config_source_link(official_path, version)

        vendors[vendor]["boards"].append({
            "printer": printer.replace("_", " "),
            "board_env": board_env,
            "status": status,
            "dl_link_en": dl_link_en,
            "dl_link_es": dl_link_es,
            "config_link": config_link,
            "board_link": job_url,
            "error_cause": error_cause,
        })

    total_s = sum(v["success"] for v in vendors.values())
    total_f = sum(v["fail"] for v in vendors.values())
    total_u = sum(v["unknown"] for v in vendors.values())
    total = total_s + total_f + total_u
    rate = (total_s / (total_s + total_f) * 100) if (total_s + total_f) > 0 else 0

    badge_url = f"https://github.com/{REPO}/actions/workflows/auto-update.yml/badge.svg"
    actions_url = f"https://github.com/{REPO}/actions/workflows/auto-update.yml"

    lines = []
    lines.append("# Marlin Auto Builder 3Dwork — Build Status")
    lines.append("")
    lines.append(f"**{total} boards** — {total_s} ✅ / {total_f} ❌ = **{rate:.1f}%**")
    if version:
        lines.append(f"**Marlin version:** `{version}`")
    lines.append("")
    lines.append(f"[![Auto Build]({badge_url})]({actions_url})")
    lines.append("")
    lines.append("| Range | Vendors |")
    lines.append("|-------|---------|")
    lines.append(f"| ✅ All passed | {sum(1 for v in vendors.values() if v['fail']==0 and v['unknown']==0)} |")
    lines.append(f"| ⚠️ Partial | {sum(1 for v in vendors.values() if v['fail']>0 and v['success']>0)} |")
    lines.append(f"| ❌ All failed | {sum(1 for v in vendors.values() if v['success']==0 and v['fail']>0)} |")
    lines.append(f"| ⏳ Unknown | {sum(1 for v in vendors.values() if v['unknown']>0)} |")
    lines.append("")

    # Vendor index inline
    lines.append("## Vendor Index")
    lines.append("")
    parts = []
    for vendor in sorted(vendors.keys()):
        v = vendors[vendor]
        if v["unknown"] > 0: icon = "⏳"
        elif v["fail"] == 0: icon = "✅"
        elif v["success"] > 0: icon = "⚠️"
        else: icon = "❌"
        slug = gh_anchor(vendor)
        parts.append(f"{icon} [{vendor}](#{slug}) ({v['count']})")
    lines.append(" · ".join(parts))
    lines.append("")

    # Per-vendor tables
    for vendor in sorted(vendors.keys()):
        v = vendors[vendor]
        if v["unknown"] > 0: e = "⏳"
        elif v["fail"] == 0: e = "✅"
        elif v["success"] > 0: e = "⚠️"
        else: e = "❌"

        summary = f"{v['success']} ✅ / {v['fail']} ❌"
        if v["unknown"] > 0:
            summary += f" / {v['unknown']} ⏳"

        lines.append("---")
        lines.append("")
        lines.append(f"## {e} {vendor}")
        lines.append(f"*{v['count']} boards — {summary}*")
        lines.append("")
        lines.append("| Printer | Board Env | Status | EN | ES | Config Source |")
        lines.append("|---------|-----------|--------|----|----|---------------|")
        for b in v["boards"]:
            if b["status"] == "success":
                badge = "✅"
                fw_en = f"[⬇ EN]({b['dl_link_en']})" if b["dl_link_en"] else "—"
                fw_es = f"[⬇ ES]({b['dl_link_es']})" if b["dl_link_es"] else "—"
            elif b["status"] == "failure":
                badge = "❌"
                fw_en = "—"
                fw_es = "—"
            else:
                badge = "⏳"
                fw_en = "—"
                fw_es = "—"

            cf = f"[Marlin Configs]({b['config_link']})" if b["config_link"] else "—"
            lines.append(f"| {b['printer']} | `{b['board_env']}` | {badge} | {fw_en} | {fw_es} | {cf} |")

        # Failure details sub-table
        failures = [b for b in v["boards"] if b["status"] == "failure"]
        if failures:
            lines.append("")
            lines.append("**Failed boards:**")
            for b in failures:
                err = b["error_cause"] or "Unknown"
                link = f" [[job]({b['board_link']})]" if b["board_link"] else ""
                lines.append(f"- `{b['printer']}`: {err}{link}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Legend")
    lines.append("")
    lines.append("| Badge | Meaning |")
    lines.append("|-------|---------|")
    lines.append("| ✅ | Firmware compiled successfully |")
    lines.append("| ❌ | Firmware failed to compile |")
    lines.append("| ⏳ | Status unknown (not in latest run) |")
    lines.append("")
    lines.append("- **EN / ES**: Direct links to compiled firmware in English (`en/firmware.bin`) and Spanish (`es/firmware.bin`)")
    lines.append("- **Config Source**: Official Marlin Configuration files used")
    lines.append("- **[Marlin Configurations](https://github.com/MarlinFirmware/Configurations)** — official reference configs")
    lines.append("")
    lines.append(f"> Auto-generated from [workflow run #{RUN_ID}](https://github.com/{REPO}/actions/runs/{RUN_ID})")

    with open("BUILD_STATUS.md", "w") as f:
        f.write("\n".join(lines))

    print(f"Generated BUILD_STATUS.md: {len(vendors)} vendors, {total} boards")
    print(f"Success: {total_s}, Failed: {total_f}, Unknown: {total_u}, Rate: {rate:.1f}%")

if __name__ == "__main__":
    main()
