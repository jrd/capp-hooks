#!/usr/bin/env python3
import stat
from argparse import ArgumentParser
from functools import cached_property
from json import loads
from os import environ
from pathlib import Path
from subprocess import run
from sys import argv, exit, stderr

from yaml import safe_load


class BackupVolumes:
    VOLUME_ROOT = Path(loads(run(['docker', 'info', '-f', 'json'], capture_output=True).stdout)['DockerRootDir']) / 'volumes'
    BORG_PASSPHRASE_PATH = Path('/root/.borg-passphrase')
    BORGMATIC_ROOT = Path('/etc/borgmatic.d')
    BORGMATIC_HOOKS = BORGMATIC_ROOT / 'common' / 'hooks.yaml'
    REMOTE_REPO_ROOT = 'qetoBackup:/backups'

    def __init__(self):
        parser = ArgumentParser()
        parser.add_argument("app", help="application name (Example: itsim)")
        parser.add_argument("environment", help="environment (Example: prod)")
        parser.add_argument("version", type=float, help="version number")
        parser.add_argument("compose_file", type=Path, help="path to docker compose file (application context)")
        parser.add_argument("target_dir", type=Path, help="path to target dir (/etc/compose/<app_name>/<env>)")
        parser.add_argument("remain", nargs='*')
        args = parser.parse_args()
        self.app = args.app
        self.env = args.environment
        self.compose_file = args.compose_file
        self.compose_config = self.parse_compose_file()

    def parse_compose_file(self):
        try:
            with self.compose_file.open() as f:
                config = safe_load(f)
                if not config:
                    raise ValueError
                return config
        except Exception:
            exit(2)

    @cached_property
    def is_config_ok(self):
        return 'volumes' in self.compose_config and 'x-backups' in self.compose_config

    @cached_property
    def repo_name_prefix(self):
        return f'{self.app}-{self.env}'

    @cached_property
    def repos(self):
        if not self.is_config_ok:
            return {}  # no volume
        volumes = self.compose_config['volumes']
        backups = self.compose_config['x-backups']
        for volume, config in self.compose_config.get(f'x-{self.env}-backups', {}).items():
            backups[volume] = config
        # Build repo names & volume paths
        # Only keep backups that define an existing volume and have `retention_days` defined
        return {
            self.VOLUME_ROOT / f'{self.repo_name_prefix}_{volume}': config['retention_days']
            for volume, config in backups.items()
            if volume in volumes and config and 'retention_days' in config
        }

    def backup(self):
        self.BORGMATIC_ROOT.mkdir(parents=True, exist_ok=True)
        for repo, days in self.repos.items():
            self.create_remote_repo(repo)
            self.create_borgmatic_config(repo, days)

    def create_remote_repo(self, repo):
        print(f"Creating repository {repo.name}...")
        # Init borg repository
        res = run(
            ['borg', 'init', '-e', 'repokey', f'{self.REMOTE_REPO_ROOT}/{repo.name}'],
            capture_output=True,
            encoding='utf-8',
            env=dict(BORG_PASSCOMMAND=f'cat {self.BORG_PASSPHRASE_PATH}'),
        )
        if environ.get('DEBUG', '') and res.returncode != 0:
            print(f"An error occured while initializing {repo.name}: error code {res.returncode}")
            print(res.stdout)
            print(res.stderr)

    def create_borgmatic_config(self, repo, days):
        config_file_path = self.BORGMATIC_ROOT / f'{repo.name}.yaml'
        print(f"Creating {config_file_path} borgmatic config")
        config = f"""
location:
    source_directories:
        - {repo}

    repositories:
        - {self.REMOTE_REPO_ROOT}/{repo.name}

storage:
    encryption_passcommand: "cat {self.BORG_PASSPHRASE_PATH}"
    compression: zstd

hooks:
    !include {self.BORGMATIC_HOOKS}

retention:
    keep_within: {days}d

consistency:
    checks:
        - repository
        - archives
    check_last: {days}
"""
        config_file_path.write_text(config, encoding='utf-8')
        config_file_path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def remove_borgmatic_config(self):
        for repo in self.repos:
            config_file_path = self.BORGMATIC_ROOT / f'{repo.name}.yaml'
            if config_file_path.exists():
                config_file_path.unlink()


if __name__ == "__main__":
    backup_volumes = BackupVolumes()
    arg0 = Path(argv[0]).name
    if arg0 == 'backup_deploy':
        backup_volumes.backup()
    elif arg0 == 'backup_undeploy':
        backup_volumes.remove_borgmatic_config()
    else:
        print(f"{arg0} is not a recognized name", file=stderr)
        exit(1)
