# Salt Extension Module to manage Cloudflare Access Tunnels

This extension manages [Cloudflare Zero Trust Tunnels](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/).

Currently only supports creating remotely configured tunnels

## Requirements

- The [python wrapper](https://github.com/cloudflare/python-cloudflare) for the Cloudflare API

## Docs

Check out the [docs](https://mfedec.github.io/salt-ext-cloudflare-tunnel) to get started using this
module

## Bugs

Bugs can be reported using [Github Issues](https://github.com/mfedec/salt-ext-cloudflare-tunnel/issues)

## Contributing

All contributions are welcome and very much appreciated. Contributing guide coming soon.
Contributing can take many forms, including:

- Reporting bugs
- Feature requests
- Code submissions (bug fixes/new features/improve code quality)
- Writing tests
- Writing documentation

## License

This project is licensed under the Apache Software License. See `LICENSE` for the licence text.


## Setting up Dev Env

```
# Clone the repo
git clone --origin salt git@github.com:mfedec/salt-ext-cloudflare-tunnel.git

# Change to the repo dir
cd salt-ext-cloudflare-tunnel

# Create a new venv
python3 -m venv env --prompt saltext-cf-tunnel
source env/bin/activate

# On mac, you may need to upgrade pip
python -m pip install --upgrade pip

# On WSL or some flavors of linux you may need to install the `enchant`
# library in order to build the docs
sudo apt-get install -y enchant

# Install extension + test/dev/doc dependencies into your environment
python -m pip install -e '.[tests,dev,docs]'

# Run tests!
python -m nox -e tests-3

# skip requirements install for next time
export SKIP_REQUIREMENTS_INSTALL=1

# Build the docs, serve, and view in your web browser:
python -m nox -e docs && (cd docs/_build/html; python -m webbrowser localhost:8000; python -m http.server; cd -)
```
