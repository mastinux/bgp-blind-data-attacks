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
	`wireshark /tmp/atk1-eth0-blind-attack.pcap`
	`wireshark /tmp/R2-eth4-blind-attack.pcap`  
	`wireshark /tmp/R2-eth5-blind-attack.pcap`

L'attacco è stato provato sia con un pacchetto TCP con il solo flag Reset abilitato che con un pacchetto TCP con i flag Reset e Acknowledge abilitati. I risultati sono identici.

- (pacchetto inviato sull'interfaccia atk1-eth0) Anche se il Sequence Number e l'Acknowledgment Number sono quelli che R2 si aspetta da R3 la sessione TCP tra i due router non viene interrotta.
L'implementazione di BGP di Quagga non risulta affetta dalla vulnerabilità sfruttata dal Blind RST Attack.

- (pacchetto inviato sull'interfaccia atk1-eth1) la sessione BGP viene interrotta e ne viene creata un'altra; è il risultato che ci aspettiamo dall'attacco.

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
	`wireshark /tmp/atk1-eth0-blind-attack.pcap`
	`wireshark /tmp/R2-eth4-blind-attack.pcap`  
	`wireshark /tmp/R2-eth5-blind-attack.pcap`

- (pacchetto inviato sull'interfaccia atk1-eth0) il pacchetto non influenza la sessione tra R2 ed R3.

- (pacchetto inviato sull'interfaccia atk1-eth1) R3 risponde con un pacchetto di Reset; è il risultato che ci aspettiamo dall'attacco.

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

- start topology  
	`# python bgp.py`

- choose attack and follow the instructions printed on the opened window
	`> 2`

- stop topology  
	`> 0`

- analyze pcap capture files  
	`wireshark /tmp/atk1-eth0-blind-attack.pcap`
	`wireshark /tmp/R2-eth4-blind-attack.pcap`  
	`wireshark /tmp/R2-eth5-blind-attack.pcap`

- (pacchetto inviato sull'interfaccia atk1-eth0) il pacchetto non influenza la sessione tra R2 ed R3.

- (pacchetto inviato sull'interfaccia atk1-eth1) la routing table di R2 viene contaminata dalla rotta contenuta nel BGP UPDATE dell'attacco, allo scadere dell'Hold Timer R2 rimuove le rotte che ha conosciuto tramite R3 e riapre una sessione con lo stesso R3, ripopolando la sua routing table; è il risultato che ci aspettiamo dall'attacco.

---

show quagga routing table

`show ip bgp`

---

*TODO*:

- prova a impostare un timer più lungo

- trova il modo di creare il log della routing table

- capire se l'attacco deve essere eseguito da atk1-eth0 o atk1-eth1
