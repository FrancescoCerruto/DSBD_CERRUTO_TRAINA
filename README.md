# Progetto di Sistemi Distribuiti e Big Data

## Cerruto - Traina

### Prima di cominciare
Valorizzare nei file **.env** e **K8S/Microservices/notifier.yml** i campi

SENDER_EMAIL

APP_PASSWORD

### Istruzioni per il build del docker compose
Per effettuare il build del progetto basta utilizzare il file docker-compose.yaml:
avendo docker engine avviato, posizionarsi nella root directory del progetto e
digitare nel terminale il seguente comando:

**docker compose up**

In questo modo non solo verranno costruite (o recuperate da docker hub) le immagini dei micro servizi, ma la costruzione e l'avvio dei container avverrà rispettando una catena di dipendenza
specificata nel file in questione (tramite healtcheck).

Da sottolineare è la presenza di un dockerfile nella root directory che contiene operazioni comuni a tutti i micro servizi Flask: questi si distinguono solo per i diversi requirements da dover installare per il loro funzionamento,
per cui si è deciso di creare questo dockerfile comune che viene, di volta in volta, contestualizzato all'interno del docker compose per costruire il micro servizio opportuno.

Inoltre, verranno creati anche i volumi per le componenti stateful del progetto (i database e prometheus)
e le diverse reti in cui si collocano i micro servizi.

Qualora, invece, si volesse effettuare il build del singolo micro servizio, posizionarsi nella root specifica
e digitare il seguente comando, specificando nome dell'immagine e tag:

**docker build -t <image_name>:<image_tag> .**

Per creare ed avviare un container basterà digitare il seguente comando:

**docker run --name <container_name> -p <local_port>:<container_port> -v <volume_mapping> -e <env_variable> <image_name>:<image_tag>**

### Istruzioni per il deploy su K8S

Per effettuare il deploy su K8S in locale utilizzare Kind ed installare Kubectl

Posizionarsi all'interno della directory k8s e creare il cluster usando il seguente comando:

**kind create cluster --config=config.yml**

In questo modo verrà creato un cluster costituito da due nodi: un control plane node e
un worker node. Il cluster sarà raggiungibile tramite localhost, usando le porte 80 (HTTP) e
443 (HTTPS).

Creato il cluster effettuare il deploy dei pod col seguente comando:

**kubectl apply -f __filename__.yml**

Nello specifico, l'ordine in cui fare il deploy è il seguente:

#### NAMESPACE
Partizionamento logico dei pod

**kubectl apply -f namespace.yml**

#### KAFKA:
Effetuare il deploy del broker Kafka in quanto essenziale alla comunicazione tra i vari micro servizi;

Dopo aver deployato kafka, bisognerà creare i 4 topic, 

##### cryptoupdate

##### subscriptionupdate

##### purchaseupdate

##### alert

utilizzati dai micro servizi. Per fare ciò utilizzare il seguente comando, dove bisognerà specificare il nome del pod kafka e il nome del topic che si vuole creare:

**kubectl get pods -n dsbd** --> prendere il nome del POD Kafka

**kubectl -n dsbd exec -it __kafka-pod-name__ -- /bin/bash -c "kafka-topics --bootstrap-server kafka:9092 --create --if-not-exists --topic __topic-name__ --replication-factor 1 --partitions 11"**

Da sottolineare che tutti e 4 i topic sono divisi in 11 partizioni in quanto 11 sono le cripto valute gestite dal sistema

#### NGINX - ingress.yml:
**kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml**

**kubectl apply -f __filename__.yml**

#### DATABASE - spostarsi sulla relativa cartella:
Effettuare il deploy dei database (cartella Databse) in quanto i relativi micro servizi, una volta avviati, proveranno subito a connettersi con essi. Se non ci fossero restituirebbero un errore;

**kubectl apply -f .**

#### MICROSERVIZI - spostarsi sulla relativa cartella:
Infine, sarà possibile effettuare il deploy di tutti i micro servizi (cartella microservices)

**kubectl apply -f .**