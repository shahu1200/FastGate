# Componets - Feig Readers
This is python module/library supporting Feig UHF readers.

- For documentation check **docs/itekfeig/index.html** file.
- For examples/usage check **examples/** folder.


## Build module
---
```
python3 setup.py bdist_wheel sdist
```

## Install module
---
Install/re-install this module as well as its dependency.
```
python3 -m pip install --force-reinstall --no-cache itek_feig<version>.whl
```

Install/re-install this module/library only.
```
python3 -m pip install --force-reinstall --no-deps --no-cache itek_feig<version>.whl
```

## Run Tests
---
```
pytest tests
```

## Build documentation
---
```
pdoc --force --html --output-dir docs itekfeig
```
