# Change Log

## [1.0.1] - 2024-10-07

### Changed

- Renamed console example with a more meaningful name.

### Fixed

- Set reserved bits when packing an address. Per the AX.25 spec, the reserved
  bits in the last octet of an address should be set rather than clear.
- Separate out build dependencies for Python 3.7. The pep8-naming extension
  to flake8 now needs to be pinned to an older version.

## [1.0.0] - 2024-04-03

- First public release.
