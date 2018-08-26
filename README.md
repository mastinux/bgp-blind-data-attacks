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

---

## Quagga preparation

- download quagga-1.2.4 from [here](http://download.savannah.gnu.org/releases/quagga/) in your `$HOME` and extract it

- `cd ~/quagga-1.2.4`

- `mkdir /var/run/quagga-1.2.4`

- `chown mininet:mininet /var/run/quagga-1.2.4`

- edit `configure` file, add `${quagga_statedir_prefix}/var/run/quagga-1.2.4` before all options in `QUAGGA_STATE_DIR` for loop 

- `./configure --enable-user=mininet --enable-group=mininet`

- `make`

---

## Contrib preparation

- download [bgp.py](https://github.com/levigross/Scapy/blob/master/scapy/contrib/bgp.py)

- `mkdir /usr/lib/python2.7/dist-packages/scapy/contrib`

- `cp bgp.py /usr/lib/python2.7/dist-packages/scapy/contrib`

- `touch /usr/lib/python2.7/dist-packages/scapy/contrib/__init__.py`

