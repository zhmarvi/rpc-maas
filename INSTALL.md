# rpc-maas Install docs

## Overview

RedHat OSP16, OSA changes for python3 are made into this branch.

Checkout the ***python2*** branch for all release below OSP16 or OpenStack Ussuri:
* Python3 support
* RHEL8 system dependencies
* Newer rally version
* OSP16 inventory layout changes
* OSA Ussuri and later changes

MTC is replaced with a shell script that sets up ***/root/ansible_venv*** used for the installation.
Apart from the removal of MTC the internal documentation can still be used for everything else.
* [internal monitoring docs](https://pages.github.rackspace.com/rpc-internal/docs-rpc/master/rpc-monitoring-internal/index.html)

## Dependency updates on `eom-zed`

The primary deployment target is Ubuntu 22.04 with Python 3.10 on the controller
and monitoring hosts, against upstream OpenStack-Ansible Zed. The Python
packages below belong to rpc-maas's own virtual environments. Do not install
them into OSA's `/opt/ansible-runtime` or apply OSA's full constraints file to
the monitoring environment.

| Component | Updated requirement |
|---|---|
| Controller Ansible | `ansible-core==2.13.13`, replacing 2.11.6; stays in Zed's 2.13 series, newer than upstream `zed-eom`'s 2.13.4 pin |
| Templates | `Jinja2==3.1.6`, `MarkupSafe==3.0.4`, replacing Jinja2<3 and MarkupSafe 1.1.1 |
| Venv tools | pip 26.2.2, setuptools 84.2.1 and wheel 0.48.0, shared through `playbooks/files/bootstrap-requirements.txt` |
| Monitoring API | `rackspace-monitoring==0.8.1`, now pinned for controller and agent |
| CLI compatibility | `click==7.1.2`; Monitorstack requires its `resultcallback` API, which Click 8 removed |
| Network helpers | pyroute2 0.9.6 and netaddr 1.3.0, replacing 0.7.12 and 0.10.1 |
| Other agent helpers | mitogen 0.3.54, ipaddr 2.2.0, python-memcached 1.62, pyudev 0.24.5, dnspython 2.8.0, lxml 6.1.3 and distro 1.9.0 |
| Shared dependency constraints | cryptography 50.0.2, pyOpenSSL 26.4.0, requests 2.34.2, urllib3 2.8.0, pyasn1 0.6.4 and PyYAML 6.0.3, when required |
| Check documentation | Reuses root `requirements.txt` instead of installing the separate Ansible 2.10.5 distribution |
| Tox dependency configuration | Uses local rpc-maas constraints and controller requirements, with the `zed-eom` tests ref instead of Wallaby; avoids Zed test-deps' separate Ansible 2.12.8 pin |

`requirements.txt` and the default agent install consume
`playbooks/files/pip-constraints.txt`. A constraint limits a package version;
it does not install that package by itself. These files constrain selected
dependencies, rather than locking the entire dependency graph. Monitorstack
and Waxeye still use their existing upstream `master` refs. Optional Rally
retains its separate constraints and needs separate validation.

Run `scripts/prepare.sh` to update the controller environment. It now installs
the shared venv tools before the controller requirements and stops on an
installation failure. Monitoring venv creation uses the same tool versions and
requires Python 3.10 or newer. Existing Python 2 / older Python environments
must be migrated before using these defaults. The Ansible 2.13 controller is
specifically tested here on Python 3.10. Run tox with a Python 3.10 interpreter;
its default Zed test harness and local constraints are selected independently
of OSA's deployed environment.

Validation used separate controller and agent venvs on Python 3.10.22/macOS:
package installation and `pip check`, Ansible/Jinja templating, Rackspace driver
imports, Monitorstack CLI/plugin imports, and Ansible 2.13 syntax checks for
the collection bootstrap and main site playbook passed. Linux-specific agent
operations and deployment against Ubuntu 22.04/Zed still require integration
testing. These updates do not establish a CVE-free deployment: Zed and Ansible
2.13 are no longer maintained, and the legacy Monitorstack dependency chain
still needs security maintenance.

## Download rpc-maas

```
git clone https://github.com/rcbops/rpc-maas /opt/rpc-maas
cd /opt/rpc-maas/
```

## Setting up the installer venv

Ran as root on the director vm.
```
cd /opt/rpc-maas/

scripts/prepare.sh
```

## Creating rackspace monitoring entities and agent tokens.

According to the docs the rackspace-monitoring-agent installation and entity creation is handled by the Rackspace cloud engineers.
It doesn't cover this in detail, so I'm assuiming our deployment guys have the steps down for that.
Before continuing on the following must be completed.

* Entity and agent token creation.
* Installation of the rackspace-monitoring-agent. (redhat 8 packages are available)
* Configuration of the rackspace-monitoring-agent with the entity and agent token.

See the docs for details on a [decoupled environment](https://pages.github.rackspace.com/rpc-internal/docs-rpc/rpc-monitoring-internal/monitoring-impl/monitoring-internal.html#id5) for more details.

## Generating an auth-token

This may already be obtained from pitchfork or whatever the Rackspace cloud enginners used to set up the entities.
If you have a pubcloud username and api key, you can use the following gating test script to pull the auth token.
The values for the url and auth token can be found in /root/maas-vars.rc after.

```
/root/ansible_venv/bin/python3 tests/maasutils.py --username <pubcloud_username> --api-key <pubcloud_api_key> get_token_url

Credentials file written to "/root/maas-vars.rc"
```

## Creating the rpc-maas config file

### RedHat OSP

This is the primary config file used for the rpc-maas install.  It will vary depending on the environment. Follow the docs to complete the config.
* [Configuring Overrides](https://pages.github.rackspace.com/rpc-internal/docs-rpc/rpc-monitoring-internal/monitoring-impl/monitoring-internal.html#step-2-configuring-overrides) 

```
vi /home/stack/user_maas_variables.yml
```

### OpenStack Ansible (OSA)

OSA typically deploys skeleton configuration at one of the following locations:

 - **/etc/openstack_deploy/user_local_variables.yml**
 - **/etc/openstack_deploy/user_maas_overrides.yml**
 - **/etc/openstack_deploy/user_maas_variables_overrides.yml**

Add or update existing keys in the first file found, of the above mentioned list.

Do not edit any file named with **variables_defaults.yml** or **user_global_xxx.yml**

### Minimum MAAS configuration

* Example:
```
# MaaS v2 overrides
maas_api_url: "https://monitoring.api.rackspacecloud.com/v1.0/hybrid:<tenant id>"
maas_auth_token: "<taken from the /root/maas-vars.rc if using the test script>"

# The entityLabel should based on the 'maas_fqdn_extension', as follows:
# entityLabel == 'controller1.cloud01.example.com
# Refer to the naming convention documentation section for additional details
#
maas_fqdn_extension: ".cloud01.example.com"

# Define a Unique Environment ID
# If multiple clouds exist on an account, each should have a different value
# This is also used to generate objects for private pollers if used.
#
maas_env_identifier: "cloud01"

# Enable this with  to install and configure private
# pollers for ping and lb checks.
# - 'maas_env_identifier' is also required for the private poller zone object
#maas_private_monitoring_enabled: true

# Identify data center requirements for PNM and hardware monitoring
#  true = Rackspace DC (RDC) or OpenStack Everywhere deployments
# false = Customer DC (CDC)
#
maas_raxdc: true

# Release-specific exclusions are now handled dynamically. These
# overrides will likely remain empty. These are included for
# compatibility to remove any remnant host_vars that may have
# existed in the inventory.
maas_excluded_checks: []
maas_excluded_alarms: []

```

RedHat OSP additionally requires passwords to be set in order for MAAS to
login into rabbitmq and swift (when present):

```
maas_rabbitmq_password: "<some random pass>"
maas_swift_accesscheck_password: "<some random pass>"
```

## Run the install

### OpenStack Ansible (OSA)

```
cd /opt/rpc-maas
scripts/prepare.sh

# When present add the Ceph inventory to update the maas checks on
# the ceph nodes
export ANSIBLE_INVENTORY="$ANSIBLE_INVENTORY,/tmp/inventory-ceph.ini"

scripts/maas-ansible playbooks/site.yml -f 75
```

### RedHat OSP

```
cd /opt/rpc-maas
scripts/prepare.sh

scripts/maas-ansible -i /opt/rpc-maas/inventory/rpcr_dynamic_inventory.py \
                     -e @/home/stack/user_maas_variables.yml \
                     -f 75 playbooks/site.yml

```

## Verify the install

### OpenStack Ansible (OSA)

This can be skipped, until further notice

```
cd /opt/rpc-maas

# When present add the Ceph inventory to update the maas checks on
# the ceph nodes
export ANSIBLE_INVENTORY="$ANSIBLE_INVENTORY,/tmp/inventory-ceph.ini"

scripts/maas-ansible playbooks/maas-verify.yml -f 75
```

### RedHat OSP

```
cd /opt/rpc-maas

scripts/maas-ansible -i /opt/rpc-maas/inventory/rpcr_dynamic_inventory.py \
                     -e @/home/stack/user_maas_variables.yml \
                     -f 75 playbooks/maas-verify.yml
```

### Rally performance checks(OSP only, if required by customer)

* Update the config to enable rally
```
vi /home/stack/user_maas_variables.yml
```
```
...
maas_rally_enabled: true
maas_rally_users_password: "<some random pass>"
maas_rally_galera_password: "<some random pass>"
maas_rally_check_overrides:
  cinder:
    enabled: false
  glance:
    enabled: true
  keystone:
    enabled: true
  neutron_ports:
    enabled: true
  neutron_secgroups:
    enabled: true
  nova:
    enabled: false
  nova_cinder:
    enabled: false
  swift:
    enabled: true
    extra_user_roles:
      - "swiftoperator"
```

* Run the rally install
```
cd /opt/rpc-maas
. /home/stack/overcloudrc

scripts/maas-ansible -i /opt/rpc-maas/inventory/rpcr_dynamic_inventory.py \
                     -e @/home/stack/user_maas_variables.yml  \
                     -e "keystone_auth_admin_password=${OS_PASSWORD}" \
                     -f 75 playbooks/maas-openstack-rally.yml 
```

