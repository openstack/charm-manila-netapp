# Manila NetApp Backend Source Charm

## Overview

This charm provides NetApp Clustered Data ONTAP as a storage backend for
Manila, OpenStack's shared filesystem service. It is written using the Juju
[operator][operator-git-repo] framework.

## Usage

The charm relies on the principal Manila charm, and is a subordinate to it. It
provides configuration data to the `manila-share` service (which is provided by
the Manila charm with a role that includes 'share').

Prior to deploying this charm, a NetApp Data ONTAP cluster must be configured.
It also needs L3 connectivity between the storage cluster and the Manila
services. See the OpenStack [driver documentation][driver-doc] with details
about the NetApp Clustered Data ONTAP driver, and known restrictions.

If multiple, _different_, NetApp backend configurations are required, then the
`share-backend-name` config option should be used to differentiate between the
configuration sections.

_Note_: This subordinate charm requests that Manila principal charm configures
the Neutron conf file section, that the NetApp driver needs to allocate ports
for the storage vms when the `driver-handles-share-servers` config is enabled.
The principal charm provides the _main_ Manila service username/password to
this charm to enable it to provide this section.

When `driver-handles-share-servers` is enabled, the driver will launch
storage vms (SMVs) within the NetApp Data ONTAP cluster. With this mode enabled,
Manila requires a [share network][share-networks-doc] to be defined.

A Manila share network is bound to a Neutron network and subnet. During a
share creation, the NetApp driver will allocate a port in the Neutron subnet
attached to the share network, and use that as the static IP for the SVM
spawned into NetApp Data ONTAP cluster. The only limitation to this mode is
that the Neutron network bound to the share network, needs to be `flat` or
`vlan`, when using the NetApp driver.

When `driver-handles-share-servers` is disabled, an existing NetApp ONTAP
SVM must be pre-configured, and its name must be given as `vserver-name` in
the charm config.

## Building the charm

To build the charm run the following command in the root of the repository:

```bash
$ tox -e build
```

The resultant built charm will be `manila-netapp.charm`.

## Deployment

One way to deploy Manila NetApp is to use a bundle overlay when deploying
OpenStack via a bundle:

```bash
juju deploy ./base.yaml --overlay ./manila-netapp-overlay.yaml
```

The Manila NetApp bundle overlay might look like:

```yaml
applications:
  manila-netapp:
    options:
      driver-handles-share-servers: False
      vserver-name: svm0
      management-address: 10.1.1.10
      admin-name: admin
      admin-password: my-secret-admin-password
```

## Bugs

Please report bugs on [Launchpad][lp-bugs-charm-manila-netapp].

For general charm questions refer to the OpenStack [Charm Guide][cg].

<!-- LINKS -->

[cg]: https://docs.openstack.org/charm-guide
[driver-doc]: https://docs.openstack.org/manila/victoria/configuration/shared-file-systems/drivers/netapp-cluster-mode-driver.html
[share-networks-doc]: https://docs.openstack.org/manila/victoria/admin/shared-file-systems-share-networks.html
[lp-bugs-charm-manila-netapp]: https://bugs.launchpad.net/charm-manila-netapp/+filebug
[operator-git-repo]: https://github.com/canonical/operator
