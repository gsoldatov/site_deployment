# General
Tests are implemented using bats-core library.


# Setting Up Test Environment
```bash
# paths are relative to <project_root> directory
git submodule add https://github.com/bats-core/bats-core.git ansible/tests/bats
git submodule add https://github.com/bats-core/bats-support.git ansible/tests/test_helpers/bats-support
git submodule add https://github.com/bats-core/bats-assert.git ansible/tests/test_helpers/bats-assert
```


# Running Tests
```bash
# Run all tests
# (NOTE: paths are relative to <project_root>/ansible directory)
./tests/bats/bin/bats -r --setup-suite-file "tests/setup_suite.bash" tests/tests

# Run tests inside tests/scripts directory
./tests/bats/bin/bats -r --setup-suite-file "tests/setup_suite.bash" tests/scripts
```
