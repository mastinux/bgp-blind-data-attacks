# bgp-blind-data-attacks

Code based on this [thesis](https://calhoun.nps.edu/handle/10945/52961)

Migrating configuration and tests from GNS3 to mininet

---
---
---

# Tools setup

## Mininet setup

- `git clone https://github.com/mininet/mininet`

- `cd mininet`

- `git checkout 2.3.0d4`

- `util/install.sh -a`

- `mn --test pingall`

- `mn --version`

---

## Quagga setup

- download quagga-1.2.4 from [here](http://download.savannah.gnu.org/releases/quagga/) in your `$HOME` and extract it

- `cd ~/quagga-1.2.4`

- `mkdir /var/run/quagga-1.2.4`

- `chown mininet:mininet /var/run/quagga-1.2.4`

- edit `configure` file, add `${quagga_statedir_prefix}/var/run/quagga-1.2.4` before all options in `QUAGGA_STATE_DIR` for loop 

- `./configure --enable-user=mininet --enable-group=mininet`

- `make`

---

## Contrib setup

- download [bgp.py](https://github.com/levigross/Scapy/blob/master/scapy/contrib/bgp.py)

- `mkdir /usr/lib/python2.7/dist-packages/scapy/contrib`

- `cp bgp.py /usr/lib/python2.7/dist-packages/scapy/contrib`

- `touch /usr/lib/python2.7/dist-packages/scapy/contrib/__init__.py`

---
---
---

# Expected results

## Blind RST attack

|-|expected AN|unexpected AN|
|-|:-:|:-:|
|**expected SN**						|interruped session							|interruped session|
|**unexpected SN and SN inside window**	|challenge ACK and uninterruped session		|challenge ACK and uninterruped session|
|**unexpected SN and SN outside window**|refused packet and uninterrupted session	|refused packet and uninterrupted session|

- start topology  
	`# python bgp.py`

- choose attack and follow the instructions printed on the opened window
	`> 1`

- stop topology  
	`> 0`

- analyze pcap capture files  
	`wireshark /tmp/atk1-eth0-blind-rst-attack.pcap`
	`wireshark /tmp/R2-eth4-blind-rst-attack.pcap`  
	`wireshark /tmp/R2-eth5-blind-rst-attack.pcap`

Anche se il Sequence Number e l'Acknowledgment Number sono quelli che R2 si aspetta da R3 la sessione TCP tra i due router non viene interrotta.  
L'implementazione di BGP di Quagga non risulta affetta dalla vulnerabilità sfruttata dal Blind RST Attack.

---

## Blind SYN attack

|-|expected AN|unexpected AN|
|-|:-:|:-:|
|**expected SN**						|challenge ACK and uninterruped session		|challenge ACK and uninterruped session|
|**unexpected SN and SN inside window**	|challenge ACK and uninterruped session		|challenge ACK and uninterruped session|
|**unexpected SN and SN outside window**|challenge ACK and uninterruped session		|challenge ACK and uninterruped session|

- start topology  
	`# python bgp.py`

- choose attack and follow the instructions printed on the opened window
	`> 2`

- stop topology  
	`> 0`

- analyze pcap capture files  
	`wireshark /tmp/atk1-eth0-blind-syn-attack.pcap`
	`wireshark /tmp/R2-eth4-blind-syn-attack.pcap`  
	`wireshark /tmp/R2-eth5-blind-syn-attack.pcap`

L'implementazione di Quagga reagisce secondo quanto ci si aspetta nei confronti del Blind SYN Attack.

---

## Blind Data attack

When the AN and the SN are in the acceptable window and also correspond to the end of a previous BGP message without overwriting any data that are present in the connection buffer.

|R1|-|atk1|-|R2|-|R3|
|-|:-:|-|:-:|-|:-:|-|
|-|-|-|_UPDATE message_ -&gt;|o|-|-|
|-|-|-|-|update RIB|-|-|
|o|&lt;- UPDATE or KEEPALIVE|-|-|-|-|-|
|-|UPDATE or KEEPALIVE -&gt;|o|-|-|-|-|
|o|&lt;- | ACK war | -&gt;|o|-|-|

*TODO*:  
	Path Attributes > Path Attribute - AS_PATH > Flags = 50  
	Path Attributes > Path Attribute - AS_PATH > Length = 0x06  
	but it must be  
	Path Attributes > Path Attribute - AS_PATH > Length = 0x00 0x06  
	lanciando l'attacco 3 non viene creato i file di log .out e .err  
	capire qual è il problema di estensione della classe degli attributi del bgp
