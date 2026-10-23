# Dependency and Ubuntu compatibility audit

> Scope update: the primary target is now Ubuntu 22.04 / upstream OpenStack-Ansible Zed on branch `eom-zed`. See [the pinned Zed assessment](../eom-zed/README.md). The three-OS proposal below is historical exploratory work, not the current deployment target.

Audit date: 2026-10-23. Repository: zhmarvi/rpc-maas, branch `102026-updates`, baseline commit `d02a78c`. Origin and upstream (`rcbops/rpc-maas`) were fetched and identical at that commit. This change records an audit; it does not upgrade the deployed environment or certify Ubuntu support.

## Findings that determine the upgrade approach

The controller must run locally on **each** Ubuntu release, per the requested deployment model. A maintained additional Python interpreter is needed on Ubuntu 20.04 and 22.04 for current Ansible. Keep the OS Python intact. Package version changes alone cannot deliver the requested support: the existing playbooks fail a modern Ansible syntax check, Monitorstack needs compatibility work, and the vendor agent repository needs verification.

The baseline audit found **19 distinct CVEs across four dependency/version pairs**: ansible-core 2.11.6, the highest allowed Jinja2 version (2.11.3), docs-only ansible 2.10.5, and setuptools 81.0.0. The exploratory runtime resolution found **one additional CVE in DiskCache**, with no fixed version listed. Legacy test/bootstrap scripts introduce further findings, reported separately below. Findings describe affected declared or resolved versions; exploitation and deployment exposure were not established.

## Scope and evidence

- `inventory.json`: 168 declarations from root/test/docs requirements, package variables for all distro profiles, Rally constraints, collections, bindep, setup, tox, and bootstrap/test scripts. Entries include duplicates and source statements; this is not 168 unique installed packages.
- `baseline-input.txt` and `baseline-pip-audit.json`: eight exact-version checks. Jinja2 2.11.3 is inferred from `Jinja2<3.0`, not observed installed. No transitive dependencies were resolved for this baseline.
- `runtime-roots.txt`, `runtime-input.txt`, `runtime-resolution.json`, `runtime-pip-audit.json`: exploratory Python 3.12/macOS arm64 resolution of 150 packages, combining agent, Docker, and optional Rally roots with Monitorstack's declared dependencies. Production agent/Rally environments are separate; this union is not a production lockfile. VCS root packages are excluded from the pip audit.
- `test-input.txt`, `test-resolution.json`, `test-pip-audit.json`: 42 packages resolved from test-requirements.txt alone. No known CVEs returned. Remote tox Wallaby constraints and docs ansible 2.10.5 are excluded from this resolution; the latter is covered in the baseline.
- `legacy-*-input.txt` and `legacy-*-pip-audit.json`: historical test/bootstrap pins, separate from the deployed default runtime.
- `package-metadata.json`: queried PyPI latest-version/Python metadata and vendor repository probes.
- `ansible-2.19-syntax-check.txt`: actual syntax-check failure using Ansible 2.19.14, Python 3.12.14 and the five currently pinned collections.

Tool: pip-audit 2.10.1, PyPI vulnerability service. Audit exit code 1 means findings; the test dependency audit exited 0. The advisory responses contain repeated records, so raw counts printed by pip-audit are larger than the distinct CVE counts used here. `findings.json` deduplicates records by CVE within each package/version and preserves the original audit files.

## Security upgrades

| Source | Current requirement | Finding / proposed action |
|---|---|---|
| requirements.txt | ansible-core==2.11.6 | Seven distinct CVEs. Replace with a maintained core release alongside Python and playbook migration. Preferred long-term candidate: 2.21.5 with Python 3.12 controllers; target Python must also meet its support floor. |
| requirements.txt | Jinja2<3.0 | Highest permitted 2.11.3 has four CVEs: CVE-2024-22195, CVE-2024-34064, CVE-2024-56326, CVE-2025-27516. Candidate 3.1.6, updated together with Ansible. |
| requirements.txt | MarkupSafe==1.1.1 | No CVE returned for this exact version. Replace the obsolete pin with a version compatible with modern Jinja/Python, e.g. 3.0.4 on Python 3.12. |
| doc/maas-checks/source/requirements.txt | ansible==2.10.5 | Seven CVEs. Align docs with the maintained controller dependency set; confirm required collection plugins before replacing the old umbrella distribution with ansible-core. |
| maas-venv-create.yml | setuptools==81.0.0 | CVE-2026-59890; advisory lists 83.0.0 as fixed. Candidate latest 84.2.1 requires Python >=3.10. The Python-2 setuptools<45 branch cannot be part of a maintained Ubuntu/Python-3 baseline. |
| Rally template / Monitorstack | diskcache==4.1.0 / unbounded diskcache | CVE-2025-69872 affects releases through latest 5.6.3; no fixed release listed. Upgrading to 5.6.3 does not resolve it. Replace/patch pickle serialization and validate stored types, or remove affected functionality. Restrict cache-directory ownership and permissions as mitigation; do not mark the CVE fixed on that basis. |
| playbooks/vars/maas.yml | Monitorstack @master | Pin a reviewed commit or maintained fork after fixing Python/API compatibility. Current examined master: 38541c4014b5ce94c7d67f4c21efbe114cb5dbab. It imports distutils.util.strtobool (removed from Python 3.12 stdlib), depends on DiskCache, and restricts Elasticsearch to >=6,<7. Test independently of a setuptools distutils shim. |
| playbooks/vars/maas.yml | Waxeye @master | Pin a reviewed commit; examined master: 723da0475fc0c8e3dd43da46665ef7c62734857b. VCS code has no pip-audit coverage merely because its transitive dependencies are scanned. |
| root + agent | rackspace-monitoring | Latest queried 0.8.1 resolves apache-libcloud 1.5.0 through its <2 restriction. No known CVE returned for that resolution, but old API/dependency compatibility needs import and live monitoring tests. Do not force libcloud outside its declared range. |
| pip-constraints.txt | empty except comment | Add tested constraints per supported Python/profile and audit the fully resolved graph. Default `latest`, unbounded requirements and @master refs currently change deployments over time. |

All individual CVEs, aliases and reported fixed versions are in `findings.json`. A feed's empty fixed-version list does not mean a maintained replacement is necessarily vulnerable; it means that advisory did not supply a version fix. Conversely, no reported CVE does not establish that a package is maintained or secure.

## Other Python package candidates

These are queried latest releases, **not tested upgrade pins**. Python requirements below are PyPI metadata at audit time. Standardizing application venvs on a maintained Python 3.12 would simplify testing; it still requires a provisioning strategy on older hosts.

| Package(s) | Current | Candidate / compatibility concern |
|---|---|---|
| pyroute2 | 0.7.12 | 0.9.6, Python >=3.9; test network enumeration |
| netaddr | 0.10.1 | 1.3.0; test address parsing changes |
| mitogen | unbounded | 0.3.54; validate against selected Ansible or omit unused integration |
| ipaddr | unbounded | Latest 2.2.0; prefer migrating callers to stdlib ipaddress after compatibility review |
| python-memcached | unbounded | 1.62; test memcache checks |
| pyudev | unbounded | 0.24.5, Python >=3.10 |
| dnspython | unbounded | 2.9.0, Python >=3.11 |
| lxml / distro | unbounded | 6.1.3 / 1.9.0; test XML and distro checks |
| docker | unbounded, optional | 7.2.0; validate Docker API and socket access |
| PyMySQL | unbounded, Rally | 1.2.3; test database driver selection |
| rally / rally-openstack | unbounded, optional | 5.1.1 / 4.1.0, Python >=3.10; validate task syntax, plugin discovery and OpenStack authentication |
| numpy | unbounded, Rally | 2.5.4 requires >=3.12; test major-version behavior |
| influxdb | unbounded, Rally | 5.3.2; keep server/client API version aligned |
| python-senlinclient | unbounded, Rally | 3.1.0; validate against deployed OpenStack APIs |
| PyYAML / python-dateutil / pyasn1 | unbounded, Rally | 6.0.3 / 3.0.0 / 0.6.4; include in resolved lock and functional tests |
| pip | unbounded bootstrap | 26.2.2 requires >=3.10; use venv-local pip and tested bootstrap constraints |
| click and OpenStack SDK dependencies | unbounded/direct or transitive | Versions captured in runtime-resolution.json; validate together with the legacy Rackspace and Monitorstack consumers |

Rally's commented git constraint and maas_rally_git_version=3.1.0 do not pin the active PyPI Rally installation. RHOSP's system-site-packages mode can inherit additional distro/OpenStack dependencies not represented by a clean pip resolution.

## Ansible collections and porting blockers

The following existing refs installed successfully into an isolated directory. Successful installation is not a security audit or a compatibility certification:

| Collection | Existing ref | Next step |
|---|---|---|
| openstack.cloud | 2.2.0 | Select maintained release compatible with chosen core and deployed OpenStack SDK/cloud |
| ansible.posix | 1.5.4 | Upgrade with core; test mount/system integration |
| community.general | 7.5.9 | Upgrade with core; verify moved/removed modules and return values |
| community.rabbitmq | 1.4.0 | Upgrade with core; test RabbitMQ management endpoints |
| openstack.config_template | 2.1.0 | Verify maintained release and template rendering with selected core |

Collection-specific advisories were not comprehensively scanned by pip-audit. Git collection refs and VCS sources require their own review; no clean collection-CVE claim is made.

Concrete porting work:

1. `playbooks/maas-remove-old-templates.yml` declares play vars as a list. Ansible 2.19 rejects it with “Vars in a Play must be specified as a dictionary.” This is the first observed parse failure, not an exhaustive list.
2. Both `scripts/maas-ansible` and its `.rc` force `auto_legacy`, preventing a caller-selected Python interpreter. Move to supported discovery and preserve explicit overrides.
3. Replace obsolete `version_compare` tests/filters in pre-flight, container-storage and legacy AIO test generation with supported version tests.
4. Review templating/trust and boolean conditionals for core 2.19+; syntax alone cannot check rendered deployment paths.
5. `playbooks/library/_uri.py` imports `unicode` from ansible.module_utils.basic. Check whether this legacy module is used and retire or port it.
6. Replace global apt_key trust with per-repository keyrings and signed-by. Confirm key fingerprints, repo metadata and package dependencies per Ubuntu release.
7. Replace remote unpinned get-pip execution and shared /tmp constraints staging with controlled venv bootstrap and unique/restricted temporary paths. Preserve cleanup on failure.

## Ubuntu support plan: local controller on every release

| OS | Default Python | Controller plan | Target/application plan and limits |
|---|---|---|---|
| Ubuntu 20.04 | 3.8 | Provision a separately maintained Python 3.12 and isolated controller venv on 20.04 | Core 2.21 targets require >=3.9; provision and explicitly select a supported target interpreter too. Validate apt/python3-apt interactions. Ubuntu Pro/ESM is needed for continued Ubuntu security maintenance. |
| Ubuntu 22.04 | 3.10 | Provision maintained Python 3.12 and isolated controller venv on 22.04 | Native 3.10 meets core 2.21 target floor; some newest application packages require 3.11/3.12, so application venvs need their own interpreter decision. |
| Ubuntu 24.04 | 3.12 | Use native Python 3.12 in an isolated controller venv | Native Python fits proposed controller/application baseline; verify vendor agent and monitoring dependencies. |

Core 2.19.14 is a possible short-term bridge: controllers require Python 3.11–3.13 and targets support 3.8–3.13. Its published EOL is **November 2026**, so it should not be the long-term baseline. Core 2.21 supports controller Python 3.12–3.14 and target Python 3.9–3.14. Do not choose an already unsupported core solely to retain the old controller system Python.

`scripts/prepare.sh` currently hardcodes /usr/bin/python3 and a system-site-packages venv; that must become explicit interpreter selection with prerequisite validation, isolated dependencies, fail-fast behavior, and a documented maintained interpreter source. No third-party PPA or system-Python replacement has been assumed or installed.

The vendor agent Release URL probes for 20.04, 22.04 and 24.04 all returned HTTP 403 from this environment. That does **not** establish missing packages or a vendor support decision. Installation on all three versions remains unverified until repository access, signed metadata, binaries, architecture, libc/OpenSSL dependencies, service startup and agent heartbeats are tested.

Distro dependencies in maas-ubuntu.yml and bindep.txt are inventoried but no installed Ubuntu package database was available. Patch through the appropriate Ubuntu security/ESM channels and inspect package origin/version with Ubuntu-aware tooling. Do not compare Ubuntu backported packages to upstream version numbers alone or claim OS CVEs resolved from this source audit.

## Legacy test/CI dependencies

Historical branches of test scripts pin setuptools 30.1.0 (4 CVEs), setuptools 50.3.2 (same 4), pyOpenSSL 16.2.0 (3), virtualenv 20.2.1 (10), Jinja2 2.8 (7), Eventlet 0.19.0 (3), and Flask 0.12.2 (4). These are conditional old OpenStack test paths, not proof they are active in current deployments. Retire the unsupported scenarios or migrate their complete OpenStack dependency sets; forcing a new Flask/Eventlet into an ancient scenario is not a validated fix. Reno 2.5.1 had no returned CVE.

Tox imports remote Wallaby constraints and test dependencies, includes system packages, and invokes the obsolete setup.py build_sphinx route. CI/bootstrap also performs global pip installs and downloads get-pip. Modernize these into isolated test environments with reproducible constraints and use sphinx-build directly; Ubuntu 24.04 global pip behavior must respect externally managed Python environments. Add an explicit Ubuntu 20.04/22.04/24.04 matrix with a local controller on each OS.

## Implementation and acceptance order

1. Establish the maintained Python source for each OS and local controller/application interpreter paths. Test apt bindings and host package installation before pinning the final Ansible baseline.
2. Port Ansible syntax, discovery, conditionals, collections and repository key handling. Update controller and docs requirements together; rerun the complete syntax check after each first-error fix.
3. Patch/replace Monitorstack's DiskCache serialization and Python 3.12 incompatibilities; preserve functional check outputs. Verify Rackspace SDK compatibility and lock VCS commits.
4. Produce separate reproducible controller, agent, verification, Docker, Rally and test constraints; audit resolved graphs on the actual Linux/Python targets. Remove obsolete pins and unsupported historical CI paths.
5. On each Ubuntu version: run prepare, deploy agent/poller, confirm service/heartbeat, exercise representative host/infra/OpenStack checks, test optional profiles, and rerun deployment for idempotence. Audit installed pip packages and Ubuntu packages after deployment.

No source dependency pins, playbooks or deployment scripts were changed in this audit. Ubuntu execution, live OpenStack/Rackspace tests, OS-package CVE scans and complete remediation remain implementation work; the saved evidence identifies where to start without claiming support that was not tested.

## Reproduce and refresh

Use a disposable Python 3.12 venv with pip-audit==2.10.1 and PyYAML. From the repository root:

```sh
python security-audits/2026-10/inventory.py
python security-audits/2026-10/summarize.py
pip-audit -r security-audits/2026-10/baseline-input.txt --no-deps --disable-pip --format json
pip-audit -r security-audits/2026-10/runtime-input.txt --no-deps --disable-pip --format json
pip-audit -r security-audits/2026-10/test-input.txt --no-deps --disable-pip --format json
pip-audit -r security-audits/2026-10/legacy-test-input.txt --no-deps --disable-pip --format json
pip-audit -r security-audits/2026-10/legacy-bootstrap-input.txt --no-deps --disable-pip --format json
```

The exact-version inputs replay advisory queries only. For fresh resolution use `pip install --dry-run --ignore-installed --report ...` on each actual target Python/OS and extract exact versions before auditing. Include the reviewed VCS projects and separate optional profiles when generating deployable locks. These audit input files must not be used as deployment requirements.

## Primary references

- [Ansible lifecycle and Python support matrix](https://docs.ansible.com/projects/ansible/latest/reference_appendices/release_and_maintenance.html)
- [Ansible core 2.19 porting guide](https://docs.ansible.com/projects/ansible/latest/porting_guides/porting_guide_core_2.19.html)
- [Ubuntu release/security lifecycle](https://ubuntu.com/about/release-cycle)
- [Ubuntu 20.04 ESM announcement](https://lists.ubuntu.com/archives/ubuntu-announce/2025-April/000310.html)
- [Jinja sandbox advisory, fixed in 3.1.6](https://github.com/pallets/jinja/security/advisories/GHSA-cpwx-vrp4-4pq7)
- [DiskCache CVE-2025-69872 advisory](https://github.com/advisories/GHSA-w8v5-vhqr-4h9v)
- [Rackspace agent installation documentation](https://docs.rackspace.com/reference/install-and-configure-the-agent)
