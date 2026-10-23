# Ubuntu 22.04 / upstream OpenStack-Ansible Zed assessment

Assessed 2026-10-23 on branch `eom-zed`, rpc-maas baseline `d02a78c`. The user confirmed upstream OpenStack-Ansible, with no internal fork. Ubuntu 22.04 is the primary requested OS, including the local deployment controller. This assessment supersedes the earlier three-OS proposal in [the directory-wide audit](../2026-10/README.md).

**Result: the upstream compatibility baseline is pinned below, but it is not a CVE-remediated deployment configuration.** The 32 selected reference versions produce 55 distinct CVEs and four additional advisory IDs in 13 packages. Operational requirements and bootstrap scripts have not been changed to these vulnerable reference versions. No Ubuntu deployment or installed-host scan was performed.

## Exact upstream reference

| Component | Reference |
|---|---|
| Primary controller and targets | Ubuntu 22.04 LTS (Jammy), native Python 3.10 |
| OpenStack-Ansible | https://opendev.org/openstack/openstack-ansible, `zed-eom` / 26.5.3 |
| OSA commit | `6d4d953d645dbd0abbfff5cb19892810884c7edb` |
| Requirements repository | https://opendev.org/openstack/requirements |
| Requirements commit selected by OSA | `9c379d80fceba448eebe6c3121184435b49c48ec` |
| OSA bootstrap Ansible Core | `2.13.4` |
| OSA bootstrap build tools | pip `22.1.2`, wheel `0.37.1`, setuptools `67.8.0` |
| Upstream lifecycle | Zed unmaintained; Ansible Core 2.13 reached EOL on 2023-11-06 |

`baseline.json` records these references. `osa-upper-constraints.txt`, `osa-global-requirement-pins.txt`, and `osa-collection-requirements.yml` are copied reference material, not automatically applied deployment inputs. The requirements snapshot is from OSA's exact pinned commit, not the current tip of `unmaintained/zed`.

OSA's `scripts/bootstrap-ansible.sh` sets `ANSIBLE_PACKAGE` and obtains the constraints ref from `playbooks/defaults/repo_packages/openstack_services.yml`. `scripts/scripts-library.sh` builds `/opt/ansible-runtime`. Ansible Core 2.13 supports controller Python 3.8–3.10, which includes Jammy's native Python. This is historical compatibility, not current maintenance or verification of rpc-maas.

Official references: [Zed release status](https://releases.openstack.org/zed/), [Zed deployment host OS list](https://docs.openstack.org/project-deploy-guide/openstack-ansible/zed/deploymenthost.html), [Ansible maintenance and Python matrix](https://docs.ansible.com/projects/ansible/latest/reference_appendices/release_and_maintenance.html).

## Findings in the selected reference versions

The selection covers OSA's controller/build pins and overlapping rpc-maas, Monitorstack and optional Rally dependencies. It is not the entire OpenStack dependency graph or a resolved environment. `findings.json` contains individual CVEs, aliases, descriptions and advisory-reported fixes. Counts below deduplicate aliases and repeated feed records.

| Package | Zed reference | Distinct CVEs | Other advisories | Remediation constraint |
|---|---|---:|---:|---|
| ansible-core | 2.13.4 | 7 | 0 | Reported fixed versions are outside 2.13; no currently maintained 2.13 release. |
| lxml | 4.9.1 | 1 | 0 | Feed reports 6.1.0; validate XML checks and Python/platform wheels. |
| pyOpenSSL | 22.0.0 | 2 | 0 | Feed reports 26.0.0; update with compatible cryptography/OpenSSL. |
| urllib3 | 1.26.12 | 10 | 0 | Some fixes require 2.x; validate requests, OpenStack SDK and client bounds. |
| cryptography | 36.0.2 | 9 | 4 | Multiple independent fixes; reported fixes extend to 49.0.0. Validate Python 3.10 metadata and consumers before pinning. |
| requests | 2.28.1 | 4 | 0 | Reported fixes extend to 2.33.0; update with urllib3 constraints. |
| Jinja2 | 3.1.2 | 5 | 0 | Reported fixes extend to 3.1.6; rpc-maas currently excludes all Jinja 3 releases. |
| PyMySQL | 1.0.2 | 1 | 0 | Feed reports 1.1.1; validate Rally/database driver usage. |
| pyasn1 | 0.4.8 | 4 | 0 | Reported fixes extend to 0.6.4; validate authentication dependencies. |
| dnspython | 2.2.1 | 1 | 0 | Feed reports 2.6.1; resolve a Python 3.10-compatible release. |
| pip | 22.1.2 | 7 | 0 | Multiple fixes; reported fixes extend to 26.2.0. Overrides conflict with OSA build pins. |
| wheel | 0.37.1 | 1 | 0 | Feed reports 0.38.1; override conflicts with OSA build pins. |
| setuptools | 67.8.0 | 3 | 0 | Reported fixes extend to 83.0.0; override conflicts with OSA build pins. |

These version numbers are advisory fix references, **not a jointly resolved or tested upgrade lock**. A listed fix may address only one advisory. See all per-advisory fix lists, including empty lists, in `findings.json`. The absence of a finding for the other 19 selected packages does not establish security or maintenance. Previously identified rpc-maas issues such as DiskCache's CVE-2025-69872 remain relevant even though DiskCache is not in the selected OSA constraints overlap; see the earlier runtime audit.

## Conflicts that must be resolved before installation

| rpc-maas input | Published Zed reference | Consequence |
|---|---|---|
| Root `ansible-core==2.11.6` | 2.13.4 | Different controller baseline; neither is currently maintained. A version bump alone does not fix all recorded Ansible CVEs. |
| Root `Jinja2<3.0` / MarkupSafe 1.1.1 | Jinja2 3.1.2 / MarkupSafe 2.1.1 | Applying Zed constraints to the current root requirements fails resolution. Jinja 3.1.2 itself has five CVEs. |
| Agent pyroute2 0.7.12 / netaddr 0.10.1 | 0.7.2 / 0.8.0 | Exact pins disagree if resolved in one constrained environment. |
| Monitorstack Elasticsearch >=6,<7 | 2.4.1 | No version satisfies both. Do not apply the complete OSA constraints file to Monitorstack's environment. |
| rpc-maas setuptools 81.0.0 | OSA bootstrap 67.8.0 | Both have findings; they apply to different venvs. Neither is a security fix for the other. |
| Five rpc-maas collection pins | OSA's separate collection manifest | Preserve independent paths and resolve module/API usage; replacing the entire collection manifest is not a validated upgrade. |

rpc-maas currently uses `/root/ansible_venv`; OSA uses `/opt/ansible-runtime`. Preserve that separation when implementing changes. `--system-site-packages` in rpc-maas bootstrap can expose additional OS-installed Python packages, so the actual controller needs a second inventory after provisioning. Conflicting exact constraints cannot be corrected by appending another constraints file: regenerate a coherent set and test it.

With upstream Zed unchanged and no maintained fork, there is no demonstrated combination that both retains the published Zed pins and clears these CVEs. Remediation requires either maintaining and testing backports/overrides beyond the published Zed baseline or moving to a maintained OSA release. Changes to rpc-maas's independent runtime can still be evaluated against Zed APIs, but must not be described as upstream-supported Zed Ansible upgrades.

## Ubuntu-specific evidence still needed

This is a source/version audit using pip-audit 2.10.1 and the PyPI advisory service. It ran on macOS with Python 3.12 using exact-version, no-dependency audit mode. No claim is made that the selected set resolves on Python 3.10, or that it matches installed Jammy packages. The source selection targets Jammy; the audit host is not a Jammy compatibility test.

Python package advisories are not restricted to one Ubuntu release. For APT-installed packages, use Ubuntu's package revision and security status: distro backports can fix a CVE without adopting PyPI's fixed version. No installed `dpkg` inventory, Ubuntu USN assessment, agent repository verification, or live OpenStack/monitoring tests are available in this checkout. Ubuntu 20.04 and 24.04 are outside the primary target established here.

Before calling an implementation remediated: resolve each venv separately on Ubuntu 22.04/Python 3.10, scan its complete installed graph and OS package inventory, run Ansible syntax checks with the selected collections, and exercise entity creation, agent checks, Monitorstack and any enabled Rally workflows against Zed. The earlier modern-Ansible syntax failure remains evidence of migration work, not a test of Ansible 2.13.

## Reproduce the reference scan

These commands inspect reference versions only. Run from the repository root with a separately installed pip-audit 2.10.1:

```sh
pip-audit -r security-audits/eom-zed/zed-baseline-input.txt \
  --no-deps --disable-pip --format json \
  --output security-audits/eom-zed/zed-baseline-pip-audit.json
python3 security-audits/eom-zed/summarize.py
```

The saved scan exited 1 (findings), with 109 raw records; alias deduplication yields 59 package/advisory pairs. Re-running later may change feed results. Neither command installs the selected vulnerable versions. The full source dependency inventory and earlier scans remain under `security-audits/2026-10/`.
