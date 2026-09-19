#!/usr/bin/env python3
from __future__ import annotations
import json, os, re, sys, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.github.com"
REPO = os.environ.get("GITHUB_REPOSITORY", "manish91082-coder/ghost-hunter-ai-smart")
EXPECTED_SHA = os.environ.get("EXPECTED_SHA", "").strip().lower()
RUN_ID = os.environ.get("RUN_ID", "").strip()
CURRENT_RUN_ID = (os.environ.get("CURRENT_RUN_ID") or os.environ.get("GITHUB_RUN_ID") or "").strip()
WORKFLOW = "data-plane-ci"
OUT = Path("repo-state.json")
NONTERMINAL = {"queued","in_progress","requested","waiting","pending"}
BAD = {"failure","cancelled","timed_out","action_required","startup_failure","stale"}

def api(path):
    headers = {"Accept":"application/vnd.github+json","User-Agent":"ghost-hunter-state-inspector"}
    token = os.environ.get("GH_TOKEN", "").strip()
    if token: headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(API + path, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub API {e.code}: {e.read().decode('utf-8', 'replace')[:700]}") from e

def task_id(message):
    m = re.search(r"\bGH-TASK-\d{4}\b", message or "")
    return m.group(0) if m else None

def slim_run(r):
    return {k:r.get(k) for k in ("id","name","event","status","conclusion","head_branch","head_sha","created_at","updated_at","html_url")}

def main():
    if not EXPECTED_SHA: raise RuntimeError("EXPECTED_SHA is required")
    repo = api("/repos/" + REPO)
    branch = api("/repos/" + REPO + "/branches/main")
    commit = api("/repos/" + REPO + "/commits/" + EXPECTED_SHA)
    checks = api("/repos/" + REPO + "/commits/" + EXPECTED_SHA + "/check-runs?per_page=100")
    statuses = api("/repos/" + REPO + "/commits/" + EXPECTED_SHA + "/status")
    pulls_commit = api("/repos/" + REPO + "/commits/" + EXPECTED_SHA + "/pulls?per_page=100")
    pulls_open = api("/repos/" + REPO + "/pulls?state=open&per_page=100")
    issues_open = api("/repos/" + REPO + "/issues?state=open&per_page=100")
    runs = api("/repos/" + REPO + "/actions/runs?branch=main&event=push&per_page=100")
    target = None
    if RUN_ID:
        target = api("/repos/" + REPO + "/actions/runs/" + RUN_ID)
    else:
        matches = [r for r in runs.get("workflow_runs", []) if r.get("name") == WORKFLOW and str(r.get("head_sha","")).lower() == EXPECTED_SHA]
        if matches:
            matches.sort(key=lambda x: x.get('id', 0), reverse=True)
            target = matches[0]
    jobs=[]; artifacts=[]
    if target:
        rid = str(target["id"])
        jobs = api("/repos/" + REPO + "/actions/runs/" + rid + "/jobs?per_page=100").get("jobs", [])
        artifacts = api("/repos/" + REPO + "/actions/runs/" + rid + "/artifacts?per_page=100").get("artifacts", [])
    job_rows=[{"name":j.get("name"),"status":j.get("status"),"conclusion":j.get("conclusion"),"html_url":j.get("html_url")} for j in jobs]
    check_rows=[{"name":c.get("name"),"status":c.get("status"),"conclusion":c.get("conclusion"),"details_url":c.get("details_url")} for c in checks.get("check_runs",[])]
    status_rows=[{"context":s.get("context"),"state":s.get("state"),"description":s.get("description"),"target_url":s.get("target_url")} for s in statuses.get("statuses",[])]
    main_sha = branch.get("commit",{}).get("sha","").lower()
    target_ok = bool(target) and str(target.get("head_sha","")).lower() == EXPECTED_SHA and target.get("name") == WORKFLOW
    target_terminal = target_ok and target.get("status") == "completed"
    target_success = target_terminal and target.get("conclusion") == "success"
    jobs_ok = bool(job_rows) and all(j["status"]=="completed" and j["conclusion"]=="success" for j in job_rows)
    external_checks = [c for c in check_rows if not CURRENT_RUN_ID or str(CURRENT_RUN_ID) not in str(c.get("details_url") or "")]
    bad_checks = [c for c in external_checks if c["status"] in NONTERMINAL or c["conclusion"] in BAD]
    checks_ok = bool(external_checks) and not bad_checks and all(c["status"]=="completed" and c["conclusion"]=="success" for c in external_checks)
    gate = {"main_points_to_expected_sha":main_sha==EXPECTED_SHA,"exact_ci_run_found":target_ok,"ci_terminal":target_terminal,"ci_success":target_success,"all_ci_jobs_success":jobs_ok,"no_non_success_check_run":checks_ok}
    task = task_id(commit.get("commit",{}).get("message",""))
    pr_for_commit=[{"number":p.get("number"),"title":p.get("title"),"state":p.get("state"),"draft":p.get("draft"),"url":p.get("html_url")} for p in pulls_commit]
    open_prs=[{"number":p.get("number"),"title":p.get("title"),"draft":p.get("draft"),"head":p.get("head",{}).get("sha"),"base":p.get("base",{}).get("ref"),"mergeable":p.get("mergeable"),"url":p.get("html_url")} for p in pulls_open]
    open_issues=[{"number":i.get("number"),"title":i.get("title"),"labels":[x.get("name") for x in i.get("labels",[])],"is_pull_request":bool(i.get("pull_request")),"url":i.get("html_url")} for i in issues_open]
    latest={}
    for r in runs.get("workflow_runs",[]):
        if r.get("name") == "repo-state-verifier": continue
        latest.setdefault(r.get("name"), slim_run(r))
    verified=all(gate.values())
    report={"schema":"ghost-hunter.repo-state.v3","verified":verified,"verified_at":datetime.now(timezone.utc).isoformat(),"repository":{"full_name":REPO,"default_branch":repo.get("default_branch"),"visibility":repo.get("visibility"),"url":repo.get("html_url")},"main":{"sha":main_sha,"expected_sha":EXPECTED_SHA},"task":{"id":task,"commit_sha":EXPECTED_SHA,"message":commit.get("commit",{}).get("message",""),"url":commit.get("html_url")},"exact_ci_run":slim_run(target) if target else None,"jobs":job_rows,"artifacts":[{"name":a.get("name"),"expired":a.get("expired"),"size_in_bytes":a.get("size_in_bytes")} for a in artifacts],"check_runs":check_rows,"external_check_runs":external_checks,"commit_statuses":status_rows,"pull_requests_for_commit":pr_for_commit,"open_pull_requests":open_prs,"open_issues":open_issues,"latest_main_workflow_runs":latest,"gate":gate,"notes":["GitHub is ground truth for committed/pushed state; uncommitted local IDE state is invisible to GitHub.","Green CI validates the repository commit but never authorizes live capital deployment.","Issues and PRs are reported as context and are never silently treated as completed implementation."]}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    summary=os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary,"a",encoding="utf-8") as f:
            f.write("## Ghost Hunter repository state\n")
            f.write("- Task: **"+str(task or "UNASSIGNED")+"**\n")
            f.write("- Main SHA: `"+main_sha+"`\n")
            f.write("- Exact gate: **"+("VERIFIED" if verified else "BLOCKED")+"**\n")
            f.write("- Open PRs: **"+str(len(open_prs))+"** | Open issues: **"+str(len(open_issues))+"**\n")
            if not verified: f.write("- Failed gates: "+", ".join(k for k,v in gate.items() if not v)+"\n")
    print(json.dumps(report,indent=2))
    return 0 if verified else 1

if __name__ == "__main__": sys.exit(main())