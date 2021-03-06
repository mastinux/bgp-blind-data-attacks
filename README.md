# bgp-blind-data-attacks

## Installazione VM

Scaricare la VM Mininet [http://www.scs.stanford.edu/~jvimal/mininet-sigcomm14/mininet-tutorial-vm-64bit.zip](http://www.scs.stanford.edu/~jvimal/mininet-sigcomm14/mininet-tutorial-vm-64bit.zip).  
Per accedere:

- username: mininet
- password: mininet

## Preparazione mininet

- `$ git clone https://github.com/mininet/mininet`

- `$ cd mininet`

- `$ git checkout 2.3.0d4`

- `$ ./util/install.sh -a`

- `$ mn --test pingall`

- `$ mn --version`

## Quagga preparation

Scaricare quagga-1.2.4 from [http://download.savannah.gnu.org/releases/quagga/](http://download.savannah.gnu.org/releases/quagga/) nella tua `$HOME` ed estrai il package

- `$ cd ~/quagga-1.2.4`

- `# chown mininet:mininet /var/run/quagga`

- modifica il file `configure`, aggiungendo `${quagga_statedir_prefix}/var/run/quagga` prima di tutte le opzioni del loop su `QUAGGA_STATE_DIR` 

- `$ ./configure --enable-user=mininet --enable-group=mininet`

- `$ make`

## Contrib setup

Scaricare [https://github.com/levigross/Scapy/blob/master/scapy/contrib/bgp.py](https://github.com/levigross/Scapy/blob/master/scapy/contrib/bgp.py)

- `$ mkdir /usr/lib/python2.7/dist-packages/scapy/contrib`

- `$ cp bgp.py /usr/lib/python2.7/dist-packages/scapy/contrib`

- `$ touch /usr/lib/python2.7/dist-packages/scapy/contrib/__init__.py`

---

# Risultati attesi

## Blind RST attack

|-|expected AN|unexpected AN|
|-|:-:|:-:|
|**expected SN**						|interruped session							|interruped session|
|**unexpected SN and SN inside window**	|challenge ACK and uninterruped session		|challenge ACK and uninterruped session|
|**unexpected SN and SN outside window**|refused packet and uninterrupted session	|refused packet and uninterrupted session|

- avviare la topologia
	`# python bgp.py`

- scegliere l'attacco `1` e seguire le istruzioni nel nuovo terminale
	`> 1`

- fermare la topologia
	`> 0`

- analizzare i file di cattura
	`wireshark /tmp/atk1-eth0-blind-attack.pcap`
	`wireshark /tmp/R2-eth4-blind-attack.pcap`  
	`wireshark /tmp/R2-eth5-blind-attack.pcap`

L'attacco è stato provato sia con un pacchetto TCP con il solo flag Reset abilitato che con un pacchetto TCP con i flag Reset e Acknowledge abilitati. I risultati sono identici.

- attacco remoto (pacchetto inviato sull'interfaccia atk1-eth0) Anche se il Sequence Number e l'Acknowledgment Number sono quelli che R2 si aspetta da R3 la sessione TCP tra i due router non viene interrotta.
L'implementazione di BGP di Quagga non risulta affetta dalla vulnerabilità sfruttata dal Blind RST Attack.

- attacco locale (pacchetto inviato sull'interfaccia atk1-eth1) la sessione BGP viene interrotta e ne viene creata un'altra; è il risultato che ci aspettiamo dall'attacco.

---

## Blind SYN attack

|-|expected AN|unexpected AN|
|-|:-:|:-:|
|**expected SN**						|challenge ACK and uninterruped session		|challenge ACK and uninterruped session|
|**unexpected SN and SN inside window**	|challenge ACK and uninterruped session		|challenge ACK and uninterruped session|
|**unexpected SN and SN outside window**|challenge ACK and uninterruped session		|challenge ACK and uninterruped session|

- fermare la topologia
	`# python bgp.py`

- scegliere l'attacco `2` e seguire le istruzioni nel nuovo terminale
	`> 2`

- fermare la topologia
	`> 0`

- analizzare i file di cattura
	`wireshark /tmp/atk1-eth0-blind-attack.pcap`
	`wireshark /tmp/R2-eth4-blind-attack.pcap`  
	`wireshark /tmp/R2-eth5-blind-attack.pcap`

- attacco remoto (pacchetto inviato sull'interfaccia atk1-eth0) il pacchetto non disturba la sessione tra R2 ed R3.

- attacco locale (pacchetto inviato sull'interfaccia atk1-eth1) R3 risponde con un pacchetto di Reset; è il risultato che ci aspettiamo dall'attacco.

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

- avviare la topologia
	`# python bgp.py`

- scegliere l'attacco `3` e seguire le istruzioni nel nuovo terminale
	`> 3`

- fermare la topologia
	`> 0`

- analizzare i file di cattura
	`wireshark /tmp/atk1-eth0-blind-attack.pcap`
	`wireshark /tmp/R2-eth4-blind-attack.pcap`  
	`wireshark /tmp/R2-eth5-blind-attack.pcap`

- attacco remoto (pacchetto inviato sull'interfaccia atk1-eth0) il pacchetto non disturba la sessione tra R2 ed R3.

- attacco locale (pacchetto inviato sull'interfaccia atk1-eth1) la routing table di R2 viene contaminata dalla rotta contenuta nel BGP UPDATE dell'attacco, allo scadere dell'Hold Timer R2 rimuove le rotte che ha conosciuto tramite R3 e riapre una sessione con lo stesso R3, ripopolando la sua routing table; è il risultato che ci aspettiamo dall'attacco.
