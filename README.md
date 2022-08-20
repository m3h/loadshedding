# loadshedding
Automatic hibernate during loadshedding

## Virtual Environment
`loadshedding` has been tested using a virtual environment.
The instructions below show how to setup such an environment.

Create the Python3 virtual environment using
```
python3 -m venv .env
```

and activate
```
source .env/bin/activate
```

Upgrade pip and install some dependencies
```
pip  install --upgrade pip wheel setuptools
```

Install `wheel` before installing the dependencies in `requirements.txt`
prevents some non-fatal errors when installing the dependences in
`requirements.txt`.

Install the remaining dependencies from the `requirements.txt`
```
pip install -r requirements.txt
```

**Alternatively, you may use the install script provided at the root of this project.**
