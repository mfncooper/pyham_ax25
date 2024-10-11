# Change Log

## [Unreleased]

## [1.0.2] - 2024-10-11

### Changed

- Link to version commits from change log.

### Fixed

- Fixed Documentation link on PyPI.

## [1.0.1] - 2024-10-07

### Changed

- Renamed console example with a more meaningful name.
- Added change log.

### Fixed

- Set reserved bits when packing an address. Per the AX.25 spec, the reserved
  bits in the last octet of an address should be set rather than clear.
- Separate out build dependencies for Python 3.7. The pep8-naming extension
  to flake8 now needs to be pinned to an older version.

## [1.0.0] - 2024-04-03

- First public release.

[unreleased]: https://github.com/mfncooper/pyham_ax25/compare/v1.0.2...HEAD
[1.0.2]: https://github.com/mfncooper/pyham_ax25/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/mfncooper/pyham_ax25/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/mfncooper/pyham_ax25/releases/tag/v1.0.0
