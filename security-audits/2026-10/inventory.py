import json,pathlib,yaml
root=pathlib.Path(__file__).resolve().parents[2]; rows=[]
for path in [root/'requirements.txt',root/'test-requirements.txt',root/'doc/maas-checks/source/requirements.txt',root/'playbooks/templates/rax-maas/rally-constraint.txt.j2']:
 for n,line in enumerate(path.read_text().splitlines(),1):
  value=line.strip()
  if value and not value.startswith('#'): rows.append({'file':str(path.relative_to(root)),'line':n,'kind':'pip','requirement':value})
for path in sorted((root/'playbooks/vars').glob('*.yml')):
 data=yaml.safe_load(path.read_text()) or {}
 for key,values in data.items():
  if 'packages' not in key or not isinstance(values,list): continue
  for value in values: rows.append({'file':str(path.relative_to(root)),'variable':key,'kind':'pip' if 'pip' in key else 'distro','requirement':value})
for item in yaml.safe_load((root/'ansible-collection-requirements.yml').read_text())['collections']:
 rows.append({'file':'ansible-collection-requirements.yml','kind':'ansible-collection',**item})
rows.append({'file':'playbooks/common-tasks/maas-venv-create.yml','kind':'bootstrap','requirement':'setuptools==81.0.0 (Python 3); setuptools<45 (Python 2); pip (unbounded)'})
for n,line in enumerate((root/'bindep.txt').read_text().splitlines(),1):
 if line.strip() and not line.lstrip().startswith('#'):
  rows.append({'file':'bindep.txt','line':n,'kind':'distro-ci','requirement':line.strip()})
for filename in ['setup.py','tox.ini','gating/check/run','gating/generate_release_notes/run','gating/github_action_scripts/linting_run.sh','tests/aio-create.sh','tests/test-ansible-functional.sh']:
 for n,line in enumerate((root/filename).read_text().splitlines(),1):
  if not line.lstrip().startswith('#') and any(token in line for token in ['pip install','pip3 install','setup_requires','==','requests[security]','UPPER_CONSTRAINTS_FILE=','OSA_TEST_DEPS=']):
   rows.append({'file':filename,'line':n,'kind':'build-test-source','declaration':line.strip()})
(root/'security-audits/2026-10/inventory.json').write_text(json.dumps(rows,indent=2)+'\n')
print(len(rows),'declarations inventoried')
