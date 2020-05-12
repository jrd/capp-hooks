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
