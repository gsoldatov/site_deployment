# General
Tests are implemented using bats-core library.


# Setting Up Test Environment
Bats & its utilities are added as submodules & require initialization before tests can be run:

```bash
# Either a repository can be cloned with --recurse-submodules option
git clone --recurse-submodules <repository_URL>

# or submodules can be initialized from inside the <project_root> directory of an existing repository
git submodule update --init --recursive
```


# Running Tests
```bash
# Run all tests
# (NOTE: paths are relative to <project_root>/ansible directory)
./tests/bats/bin/bats -r --setup-suite-file "tests/setup_suite.bash" tests/tests

# Run tests inside tests/scripts directory
./tests/bats/bin/bats -r --setup-suite-file "tests/setup_suite.bash" tests/scripts

# Filter test cases by description (run a test, which compares variable names in production.env & production.env.example)
./tests/bats/bin/bats -r --setup-suite-file "tests/setup_suite.bash" --filter "compare production.env and production.env.example" tests/tests
```
