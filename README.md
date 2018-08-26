# bgp-blind-data-attacks

Code based on this [thesis](https://calhoun.nps.edu/handle/10945/52961)

Migrating configuration and tests from GNS3 to mininet

---

## Mininet preparation

- `git clone https://github.com/mininet/mininet`

- `cd mininet`

- `git checkout 2.3.0d4`

- `util/install.sh -a`

- `mn --test pingall`

- `mn --version`

## Quagga preparation

- download quagga-1.2.4 from [here](http://download.savannah.gnu.org/releases/quagga/) in your `$HOME` and extract it

- `cd ~/quagga-1.2.4`

- `chown mininet:mininet /var/run/quagga`

- edit `configure` file, add `${quagga_statedir_prefix}/var/run/quagga` before all options in `QUAGGA_STATE_DIR` for loop 

- `./configure --enable-user=mininet --enable-group=mininet`

- `make`

