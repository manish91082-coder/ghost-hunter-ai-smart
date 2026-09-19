#!/usr/bin/env python3
import json,os,re,sys,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
API='https://api.github.com'
REPO=os.environ.get('GITHUB_REPOSITORY','manish91082-coder/ghost-hunter-ai-smart')
SHA=os.environ.get('EXPECTED_SHA','').lower().strip(); RUN=os.environ.get('RUN_ID','').strip(); WF=os.environ.get('WORKFLOW_NAME','data-plane-ci')
OUT=Path('repo-state.json')
def api(path):
 h={'Accept':'application/vnd.github+json','User-Agent':'ghost-hunter-repo-state-verifier'}
 if os.environ.get('GH_TOKEN'): h['Authorization']='Bearer '+os.environ['GH_TOKEN']
 try:
  with urllib.request.urlopen(urllib.request.Request(API+path,headers=h),timeout=20) as r:return json.load(r)
 except urllib.error.HTTPError as e: raise RuntimeError('GitHub API '+str(e.code)+': '+e.read().decode('utf-8','replace')[:500])
def task(msg):
 m=re.search(r'\\bGH-TASK-\\d{4}\\b',msg or ''); return m.group(0) if m else None
def main():
 if not SHA or not RUN: raise RuntimeError('EXPECTED_SHA and RUN_ID are required')
 run=api('/repos/'+REPO+'/actions/runs/'+RUN); jobs=api('/repos/'+REPO+'/actions/runs/'+RUN+'/jobs?per_page=100'); commit=api('/repos/'+REPO+'/commits/'+SHA)
 rows=[{'name':j.get('name'),'status':j.get('status'),'conclusion':j.get('conclusion')} for j in jobs.get('jobs',[])]
 actual=str(run.get('head_sha','')).lower()
 checks={'exact_head_sha':actual==SHA,'workflow_name':run.get('name')==WF,'main_branch':run.get('head_branch')=='main','push_event':run.get('event')=='push','terminal':run.get('status')=='completed','workflow_success':run.get('conclusion')=='success','jobs_present':bool(rows),'all_jobs_success':bool(rows) and all(j['status']=='completed' and j['conclusion']=='success' for j in rows)}
 verified=all(checks.values())
 report={'schema':'ghost-hunter.repo-state.v1','verified':verified,'verified_at':datetime.now(timezone.utc).isoformat(),'repository':REPO,'task_id':task(commit.get('commit',{}).get('message','')),'expected_sha':SHA,'tested_sha':actual,'workflow':run.get('name'),'run_id':int(RUN),'event':run.get('event'),'status':run.get('status'),'conclusion':run.get('conclusion'),'checks':checks,'jobs':rows,'commit_message':commit.get('commit',{}).get('message',''),'commit_url':commit.get('html_url')}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 s=os.environ.get('GITHUB_STEP_SUMMARY')
 if s:
  with open(s,'a',encoding='utf-8') as f:f.write('## Ghost Hunter exact-state verification\n- Task: **'+str(report['task_id'] or 'UNASSIGNED')+'**\n- SHA: `'+actual+'`\n- CI run: `'+RUN+'`\n- Result: **'+('VERIFIED' if verified else 'BLOCKED')+'**\n')
 print(json.dumps(report,indent=2)); return 0 if verified else 1
if __name__=='__main__':sys.exit(main())
