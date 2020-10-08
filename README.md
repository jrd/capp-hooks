CAPP-HOOKS
==========

Goal
----

These scripts will be executed while deploying/undeploying an application on Qeto infrastructure.

Structure
---------

Script files should be put in any of the following directories:
- `pre_deploy`
- `post_deploy`
- `pre_undeploy`
- `post_undeploy`

Script files should have the executive bit set.


Backup format
-------------

Backup configurations are described in a `x-backups` section in the `docker-compose.yml` file.

In this `x-backups` section, describe each named volume that needs a backup
and indicates a number of `rentention_days` for the backup repository.

Example:
```yaml
volumes:
    pgdata:
x-backups:
    pgdata:
        retention_days: 3
```


Monitoring
----------

The monitoring hooks allows an automatic configuration of Qeto's monitoring dashboards.

Three hooks are used :
* `pre_deploy/monitoring` for labelling the containers (the labels are later needed by the monitoring solution),
* `post_deploy/monitoring` for setting up the monitoring dashboards,
* `post_undeploy/monitoring` for tearing down the monitoring dashboards.

These hooks need the configuration elements located in `confs/monitoring`. This directory contains :
* `templates` directory: json templates for the dahboards, that will be adapted to the service and environment and injected in Grafana, used by Qeto's monitoring solution,
* `blacklist`: a blacklist of services that do not need monitoring panels,
* `locking.py`: a helper module that provides functions for locking files and avoid race conditions,
* `post_deploy`: a python script executed for setting up the dashboards,
* `post_undeploy`: a python script used for tearing down the dashboards.

These hooks rely on the fact that Grafana's dashboard configuration is located in a docker volume. The monitoring hook will read and write configurations on this volume in order to update Grafana's dashboards.

Hub
---

The hub hooks are maintaining a json file up to date with currently deployed application and their frontend urls.

Two hooks are used:
* `post_deploy/hub` for adding the app/env and its url to the json,
* `pre_undeploy/hub` for removing the app/env from the json.

The json file is kept in a `hub_data` docker volume at `/data/apps.json` location.

The hub application should be deployed to read that volume/file.
