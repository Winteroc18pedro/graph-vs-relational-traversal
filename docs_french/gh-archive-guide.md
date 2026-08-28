# Comprendre GH Archive

Ce guide procède à partir des principes fondamentaux : ce que sont les
événements GitHub, ce que GH Archive en fait, ce que les fichiers contiennent
réellement, et comment transformer cela en données exploitables pour ce
projet.

> La date/heure spécifique que ce projet utilise réellement comme jeu de
> données est enregistrée dans le [README](../README.md) du projet, et non
> ici — ce fichier porte sur la compréhension de GH Archive lui-même, et non
> sur le choix spécifique fait pour ce projet.

## 1. Qu'est-ce qu'un « événement GitHub » ?

Chaque fois qu'il se passe quelque chose sur un dépôt GitHub *public* —
quelqu'un pousse des commits, ouvre une issue, ouvre une pull request,
commente, fork un dépôt, met une étoile à un dépôt, crée une branche, etc. —
GitHub l'enregistre sous forme d'un **événement** discret. Conceptuellement,
il s'agit simplement d'une entrée de journal : « à cet horodatage, cet
utilisateur a effectué cette action sur ce dépôt. »

GitHub expose un flux en direct de ces événements via son API publique
Events. Mais un flux en direct n'est pas utile pour la recherche — on ne
peut pas remonter dans le temps et demander « que s'est-il passé mardi
dernier ». Il faut quelque chose qui enregistre en continu et qui permette
de récupérer une tranche précise du passé.

## 2. Ce qu'est GH Archive

GH Archive est un projet de longue durée (lancé en 2011, toujours actif) qui
s'appuie sur le flux d'événements publics de GitHub et a un seul rôle :
enregistrer en continu chaque événement public, les regrouper **par heure**,
et publier chaque heure sous forme de fichier téléchargeable, de façon
permanente, à une URL prévisible. Il n'est pas affilié à GitHub lui-même —
c'est un projet d'archivage indépendant — mais il utilise les données
publiques de GitHub elles-mêmes, ce qui en fait un enregistrement historique
fidèle de l'activité publique sur GitHub.

Résultat pratique : pour *n'importe quelle* heure depuis 2011, on peut
récupérer un fichier contenant chaque événement public survenu sur GitHub
durant cette heure, dans le monde entier.

## 3. Pourquoi cela compte pour votre projet

Votre question de recherche porte sur le moment où un modèle de graphe
surpasse un modèle relationnel pour des requêtes à plusieurs sauts. Pour le
tester, il faut un jeu de données réel contenant de véritables relations —
et non des données synthétiques inventées, qui risquent d'avoir une forme
artificielle favorisant l'un ou l'autre modèle.

Les événements de GH Archive encodent naturellement un graphe :

```
User --[pushed to]--> Repository
User --[starred]-----> Repository
User --[forked]-------> Repository
User --[opened PR on]-> Repository
```

Un « repo » peut aussi se reconnecter à d'autres utilisateurs (par ex. tous
ceux qui lui ont mis une étoile), donc suivre des chaînes de ces relations —
« les utilisateurs ayant mis une étoile à des dépôts forkés par des
utilisateurs qui ont également poussé vers... » — correspond précisément au
type de traversée à plusieurs sauts au cœur de votre question de recherche.
Les mêmes enregistrements d'événements peuvent être aplatis en tables
relationnelles (une table `users`, une table `repos`, une table `events`
avec des clés étrangères) ou chargés comme des nœuds et des arêtes dans une
base de données graphe, ce qui permet une comparaison équitable sur des
données réelles.

## 4. La structure de l'URL

Chaque fichier horaire se trouve à :

```
https://data.gharchive.org/{YYYY-MM-DD}-{H}.json.gz
```

- `{YYYY-MM-DD}` — la date, par ex. `2026-08-27`.
- `{H}` — l'heure **en UTC**, de `0` à `23`, écrite **sans** zéro devant
  (`5`, et non `05` ; `15` reste `15`).

Ainsi `https://data.gharchive.org/2026-08-27-15.json.gz` correspondrait à
tous les événements GitHub publics survenus entre 15:00:00 et 15:59:59 UTC
le 27 août 2026 — utilisé ici purement comme exemple de la forme de l'URL.

Il n'y a ni clé d'API, ni authentification, ni limite de débit pour
télécharger ces fichiers — ce sont des fichiers statiques sur un serveur,
récupérés comme n'importe quel autre téléchargement.

## 5. Fraîcheur et disponibilité — pourquoi on ne peut pas utiliser « maintenant »

GH Archive ne peut publier un fichier que pour une heure entièrement
**terminée**, car il a besoin de tous les événements de `:00` à `:59` de
cette heure avant de pouvoir la regrouper et la publier. Deux conséquences
pratiques :

- **On ne peut pas choisir l'heure actuelle, encore en cours** — elle
  n'existe pas encore sous forme de fichier, puisqu'elle n'est pas encore
  terminée.
- **Il y a un court délai de publication après la fin d'une heure.** GH
  Archive a besoin d'un peu de temps pour collecter et empaqueter l'heure
  qui vient de se terminer, donc même l'heure la plus récemment achevée
  peut ne pas être disponible immédiatement au téléchargement. En pratique,
  ce délai est généralement court (bien moins d'une heure), mais il n'y a
  aucune garantie ferme sur le moment exact où le fichier d'une heure
  donnée apparaîtra.

Pour des raisons de recherche, il existe une seconde raison, plus
importante, d'éviter « l'instant présent », indépendamment du délai de
publication : la **reproductibilité**. Tout l'intérêt de votre projet est un
résultat mesurable et comparable — si le jeu de données était défini comme
« quelle que soit l'heure au moment où vous exécutez ceci », l'entrée serait
différente à chaque exécution du pipeline, et personne (y compris vous-même
plus tard) ne pourrait reproduire vos résultats. La solution est simple :
choisir une date et une heure précises et fixes, suffisamment dans le passé
(quelques heures suffisent déjà largement comme marge), et enregistrer cette
valeur exacte une seule fois — elle devient alors une entrée constante, et
non quelque chose de calculé au moment de l'exécution.

## 6. Ce que contient le fichier

Le nom du fichier se termine par `.json.gz`. Ce nom indique que deux couches
sont empilées :

1. **`.gz`** — la couche externe est une compression gzip, la même
   compression utilisée par les outils proches de `.zip`. Il faut la
   décompresser avant de pouvoir lire quoi que ce soit.
2. **`.json`** — après décompression, on obtient du texte. Mais malgré
   l'extension `.json`, ce n'est **pas un seul gros document JSON**. C'est
   un format appelé **JSON Lines** (parfois `.jsonl`) : chaque ligne du
   fichier est un objet JSON complet et indépendant, et il n'y a ni virgule
   ni crochet reliant les lignes entre elles. Un fichier de 60 000
   événements est un fichier texte de 60 000 lignes, chacune analysable
   indépendamment.

Cela a une importance pratique : on ne peut pas faire `json.load()`
(analyser tout le fichier d'un coup) dessus dans la plupart des langages —
on le lit ligne par ligne et on appelle l'analyseur JSON sur chaque ligne
individuellement.

### Anatomie d'un événement

Une seule ligne, une fois analysée, ressemble approximativement à ceci
(champs simplifiés pour plus de clarté) :

```json
{
  "id": "40123456789",
  "type": "PushEvent",
  "actor": {
    "id": 987654,
    "login": "some-user"
  },
  "repo": {
    "id": 111222,
    "name": "someorg/somerepo"
  },
  "payload": {
    "commits": [ { "sha": "...", "message": "..." } ]
  },
  "created_at": "2026-08-27T15:03:11Z"
}
```

Champs clés :

- **`type`** — le type d'événement. Les plus courants : `PushEvent` (code
  poussé), `WatchEvent` (c'est le nom interne de GitHub pour **mettre une
  étoile** à un dépôt, pas littéralement « regarder »), `ForkEvent`,
  `PullRequestEvent`, `IssuesEvent`, `IssueCommentEvent`, `CreateEvent`
  (nouvelle branche/étiquette/dépôt), `DeleteEvent`.
- **`actor`** — l'utilisateur GitHub ayant effectué l'action.
- **`repo`** — le dépôt sur lequel l'action a eu lieu.
- **`payload`** — des détails supplémentaires spécifiques au type
  d'événement (par ex. pour un `PushEvent`, les commits eux-mêmes ; pour un
  `PullRequestEvent`, les détails de la PR).
- **`created_at`** — l'horodatage de l'événement.

Pour construire un graphe, les champs dont on a presque toujours besoin sont
`type`, `actor.login`, `repo.name`, et `created_at` — cela suffit pour
construire des arêtes `(user)-[ACTION]->(repo)`. Le `payload` n'est
généralement nécessaire que si l'analyse s'intéresse au contenu de
l'action, et pas seulement au fait qu'elle ait eu lieu.

## 7. Récupérer les données sur votre machine

Puisqu'il s'agit d'un simple fichier HTTPS, n'importe laquelle de ces
méthodes fonctionne (substituez la date/heure réelle utilisée par ce projet,
telle qu'enregistrée dans le README) :

```bash
# curl
curl -O https://data.gharchive.org/YYYY-MM-DD-H.json.gz

# wget
wget https://data.gharchive.org/YYYY-MM-DD-H.json.gz
```

Ou simplement coller l'URL dans un navigateur — cela se télécharge comme
n'importe quel fichier.

Puis décompressez-le :

```bash
gunzip YYYY-MM-DD-H.json.gz
# produces: YYYY-MM-DD-H.json
```

(De nombreux langages de programmation peuvent aussi lire directement les
fichiers `.gz`, en diffusant la décompression, sans étape de décompression
manuelle séparée — par ex. le module `gzip` de Python.)

## 8. La lire dans du code

Un exemple minimal en Python, lisant ligne par ligne afin que le fichier
entier n'ait jamais à tenir en mémoire d'un seul coup :

```python
import gzip
import json

with gzip.open("YYYY-MM-DD-H.json.gz", "rt", encoding="utf-8") as f:
    for line in f:
        event = json.loads(line)
        if event["type"] in ("PushEvent", "ForkEvent", "WatchEvent"):
            actor = event["actor"]["login"]
            repo = event["repo"]["name"]
            # record (actor, event["type"], repo, event["created_at"])
```

À partir de là, les mêmes enregistrements extraits `(actor, type, repo,
timestamp)` peuvent être :

- Insérés dans des tables relationnelles (`users`, `repos`, `events` avec
  des clés étrangères vers les deux), ou
- Insérés comme nœuds (`User`, `Repo`) et arêtes (`PUSHED`, `STARRED`,
  `FORKED`) dans une base de données graphe.

Comme les deux modèles sont construits à partir des *mêmes* enregistrements
extraits, toute différence de performance mesurée entre eux est attribuable
au modèle de stockage/requête — et non à des différences dans les données
sous-jacentes.

## 9. Monter en volume plus tard

Une seule heure contient typiquement des dizaines de milliers d'événements —
suffisant pour construire un graphe réel avec une structure à plusieurs
sauts significative. Si des expériences ultérieures nécessitent davantage de
volume (par ex. pour pousser la profondeur de traversée plus loin avant
d'atteindre des rendements décroissants), il est possible de répéter le même
processus de téléchargement et d'analyse pour des heures ou des jours
supplémentaires — les fichiers de GH Archive sont adressés individuellement,
donc monter en volume signifie simplement en récupérer davantage et fusionner
les enregistrements extraits, sans changement de format nécessaire.

## 10. Alternative : interroger sans télécharger de fichiers

Les données de GH Archive sont également répliquées dans Google BigQuery
sous forme de tables publiques (`githubarchive.hour.YYYYMMDD_HH`, ainsi que
des agrégats journaliers/annuels). Si vous disposez d'un accès Google Cloud
(ou pouvez en configurer un), vous pouvez exécuter du SQL directement sur ces
tables dans un navigateur — utile pour des questions exploratoires rapides
(« combien d'événements `ForkEvent` se sont produits durant cette heure ? »)
sans écrire de code de téléchargement/analyse. Ceci est entièrement facultatif
pour ce projet ; télécharger et analyser directement un seul fichier horaire,
comme décrit ci-dessus, est suffisant et permet de garder une liste de
dépendances plus réduite.
