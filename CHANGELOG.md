# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## 1.1.1
### Fixed
- Fix CPU dashboards

## 1.1.0
### Fixed
- Fix incorrect newline that slipped into borgmatic backup files
### Changed
- Modern grafana dashboards (QE-710)

## 1.0.0
### Fixed
- Python 3.7 and old docker compatibility for Backup hooks (QE-589)
### Changed
- Backup bash script refactored into python script
### Added
- Per-environment configuration backup (QE-589)

