"""Deduplicate saved upstream-reference advisories; no installed exposure implied."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
source = json.loads((ROOT / 'zed-baseline-pip-audit.json').read_text())
rows = []
for dependency in source['dependencies']:
    grouped = {}
    for advisory in dependency.get('vulns', []):
        aliases = set(advisory.get('aliases', [])) | {advisory['id']}
        cves = sorted(identifier for identifier in aliases if identifier.startswith('CVE-'))
        key = cves[0] if cves else advisory['id']
        row = grouped.setdefault(key, {
            'package': dependency['name'], 'version': dependency['version'],
            'cve_or_id': key, 'ids': set(), 'fix_versions': set(),
            'description': advisory.get('description', ''),
        })
        row['ids'].update(aliases)
        row['fix_versions'].update(advisory.get('fix_versions', []))
    for row in grouped.values():
        row['ids'] = sorted(row['ids'])
        row['fix_versions'] = sorted(row['fix_versions'])
        rows.append(row)
rows.sort(key=lambda row: (row['package'], row['cve_or_id']))
(ROOT / 'findings.json').write_text(json.dumps(rows, indent=2) + '\n')
identifiers = {row['cve_or_id'] for row in rows}
print(json.dumps({
    'selected_packages': len(source['dependencies']),
    'affected_packages': len({row['package'] for row in rows}),
    'unique_cves': sum(identifier.startswith('CVE-') for identifier in identifiers),
    'unique_other_advisories': sum(not identifier.startswith('CVE-') for identifier in identifiers),
    'package_advisory_pairs': len(rows),
}, indent=2))
