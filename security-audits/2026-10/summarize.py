"""Deduplicate saved pip-audit records; do not infer installed exposure."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
rows = []
for audit in sorted(ROOT.glob('*-pip-audit.json')):
    data = json.loads(audit.read_text())
    for dependency in data['dependencies']:
        grouped = {}
        for vulnerability in dependency.get('vulns', []):
            aliases = set(vulnerability.get('aliases', []))
            identifiers = sorted(a for a in aliases if a.startswith('CVE-'))
            key = identifiers[0] if identifiers else vulnerability['id']
            finding = grouped.setdefault(key, {
                'audit': audit.name,
                'package': dependency['name'],
                'version': dependency['version'],
                'cve_or_id': key,
                'ids': set(),
                'fix_versions': set(),
                'description': vulnerability.get('description', ''),
            })
            finding['ids'].update(aliases | {vulnerability['id']})
            finding['fix_versions'].update(vulnerability.get('fix_versions', []))
        for finding in grouped.values():
            finding['ids'] = sorted(finding['ids'])
            finding['fix_versions'] = sorted(finding['fix_versions'])
            rows.append(finding)
(ROOT / 'findings.json').write_text(json.dumps(rows, indent=2) + '\n')
print(f'{len(rows)} distinct advisory/package/version rows across all audit profiles')
print(f"{len({r['cve_or_id'] for r in rows})} distinct advisory identifiers across profiles")
