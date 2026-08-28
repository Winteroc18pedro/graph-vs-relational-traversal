########################################################################
# COPIE ANNOTÉE — à des fins d'apprentissage uniquement.
#
# Ceci est un duplicata expliqué ligne par ligne de scripts/download_gharchive.py.
# Il n'est PAS destiné à être exécuté dans le cadre du pipeline du projet — il se
# trouve dans docs_french/ car son but est d'enseigner, pas de s'exécuter. Le
# script réel et « propre » (sans tous ces commentaires) est
# scripts/download_gharchive.py.
#
# Lisez de haut en bas — chaque concept s'appuie sur le précédent.
########################################################################


########################################################################
# LA DOCSTRING DU MODULE (la chaîne entre triples guillemets ci-dessous)
#
# En Python, si la toute première chose dans un fichier est un littéral de
# chaîne de caractères (non assigné à une variable, simplement présent tel
# quel), Python le traite de façon spéciale : il devient la « docstring »
# du fichier, stockée dans un attribut caché appelé __doc__.
#
# Pourquoi s'en préoccuper ? Parce que des outils peuvent la relire
# automatiquement :
#   - Exécuter `python scripts/download_gharchive.py --help` affiche ce
#     texte dans la sortie d'aide (on le branche plus loin via
#     `argparse.ArgumentParser(description=__doc__)`).
#   - Si quelqu'un `import`e ce fichier comme module et exécute
#     `help(download_gharchive)` dans un shell Python, ce texte s'affiche.
#
# Elle est écrite en langage naturel (pas un commentaire commençant par #)
# précisément pour pouvoir être extraite et affichée par d'autres
# programmes, et pas seulement lue par un humain regardant le source.
########################################################################
"""Download and decompress a single GH Archive hourly dataset file.

Defaults to this project's fixed dataset hour (see README.md), but any
date/hour can be requested for exploration.

Usage:
    python scripts/download_gharchive.py
    python scripts/download_gharchive.py --date 2026-08-27 --hour 15
"""


########################################################################
# IMPORTS
#
# La bibliothèque standard de Python est livrée avec une immense
# collection de modules prêts à l'emploi (des fichiers remplis de code
# déjà écrit) que l'on peut importer dans son propre script avec le
# mot-clé `import`, plutôt que d'écrire cette fonctionnalité soi-même
# depuis zéro. Les quatre imports ci-dessous font tous partie de la
# « bibliothèque standard » — c'est-à-dire qu'ils sont fournis avec Python
# lui-même. Rien n'a besoin d'être installé séparément (par ex. aucun
# `pip install` requis) pour exécuter ce script.
#
# `import x` rend tout ce qui se trouve dans le module `x` accessible sous
# la forme `x.quelque_chose`.
# `from x import y` va chercher dans le module `x` uniquement `y`, en le
# rendant accessible directement sous le nom `y` (sans préfixe `x.`).
########################################################################

# argparse : transforme les drapeaux de ligne de commande (comme
# `--date 2026-08-27`) tapés après `python scripts/download_gharchive.py`
# en valeurs Python structurées, plutôt que d'avoir à analyser
# manuellement sys.argv (la liste brute des mots de la ligne de commande)
# soi-même.
import argparse

# gzip : permet à Python de lire des fichiers compressés avec l'algorithme
# gzip (la même compression que celle derrière l'extension de fichier
# `.gz`) sans avoir à implémenter la décompression soi-même.
import gzip

# shutil (« shell utilities ») : un ensemble d'opérations de haut niveau
# sur les fichiers. On utilise une seule fonction de ce module :
# copyfileobj, qui copie des données d'un fichier déjà ouvert vers un
# autre par petits blocs.
import shutil

# urllib.request : l'outil intégré de la bibliothèque standard pour
# effectuer des requêtes HTTP(S) — dans notre cas, simplement récupérer un
# fichier depuis une URL, comme ce que fait un navigateur web quand on
# clique sur un lien de téléchargement.
import urllib.request

# `from pathlib import Path` extrait la classe Path du module pathlib.
# Path représente un chemin du système de fichiers (l'emplacement d'un
# fichier ou d'un dossier) comme un objet doté de méthodes utiles, plutôt
# que comme une simple chaîne de caractères qu'il faudrait découper et
# recoller soi-même.
from pathlib import Path


########################################################################
# CONSTANTES
#
# Ce sont simplement des variables Python ordinaires, mais écrites en
# MAJUSCULES par convention. Python n'a pas de mot-clé ni de mécanisme
# spécial pour les « constantes » — les MAJUSCULES sont purement une
# convention humaine signifiant « par accord, cette valeur n'est pas
# censée être réassignée ailleurs dans le code ». Cela indique une
# intention, rien de plus.
########################################################################

# La date et l'heure spécifiques que ce projet a choisies comme jeu de
# données fixe et reproductible (voir README.md pour savoir pourquoi cette
# heure précise a été choisie). Les stocker ici permet à toute autre
# partie du script de faire référence à DEFAULT_DATE / DEFAULT_HOUR au
# lieu de répéter les valeurs littérales.
DEFAULT_DATE = "2026-08-27"
DEFAULT_HOUR = 15

# ---------------------------------------------------------------------
# Construction de DATA_DIR, étape par étape :
#
#   __file__
#     Une variable spéciale que Python définit automatiquement dans
#     chaque module, avec le chemin du fichier source de ce module
#     lui-même. Ici, ce serait quelque chose comme :
#       C:\dev\Research\scripts\download_gharchive.py
#
#   Path(__file__)
#     Enveloppe cette chaîne dans un objet Path, débloquant les méthodes
#     liées aux chemins (comme celles utilisées ensuite) plutôt que
#     d'avoir à manipuler la chaîne brute à la main.
#
#   .resolve()
#     Convertit le chemin en chemin absolu (partant de la racine du
#     disque, par ex. `C:\...`) et nettoie tout segment du type `..`.
#     Cela compte car __file__ peut parfois être un chemin relatif,
#     selon la façon dont le script a été lancé — .resolve() garantit
#     qu'on obtient toujours l'emplacement complet et non ambigu.
#
#   .parent
#     Les objets Path comprennent la hiérarchie des dossiers. `.parent` de
#     `C:\dev\Research\scripts\download_gharchive.py` est
#     `C:\dev\Research\scripts` (le dossier contenant le fichier).
#
#   .parent.parent
#     En remontant encore d'un niveau : le parent de
#     `C:\dev\Research\scripts` est `C:\dev\Research` — la racine du
#     projet.
#
#   / "data"
#     Les objets Path surchargent l'opérateur `/` pour signifier « ajouter
#     un segment de chemin à ce chemin » — c'est l'alternative lisible de
#     pathlib à os.path.join(). Le résultat est `C:\dev\Research\data`.
#
# Pourquoi calculer cela à partir de __file__ plutôt que d'écrire
# simplement "data" comme chemin relatif ? Parce qu'un chemin relatif
# comme "data" est interprété relativement à l'endroit où l'on se trouve
# dans le terminal (le « répertoire de travail courant ») au moment
# d'exécuter le script — ce qui pourrait être n'importe où. Construire le
# chemin à partir de __file__ garantit au contraire que le dossier data/
# se trouve toujours à côté du projet, quel que soit le répertoire dans
# lequel on se trouvait en tapant la commande `python ...`.
# ---------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


########################################################################
# FONCTIONS — POURQUOI S'EN DONNER LA PEINE ?
#
# Une fonction est un bloc de code nommé et réutilisable. Plutôt que
# d'écrire la logique de téléchargement en ligne, tout en bas du fichier,
# l'envelopper dans une fonction appelée `download` permet :
#   1. De l'appeler plusieurs fois avec des arguments différents (par ex.
#      des dates/heures différentes) sans dupliquer le code.
#   2. De pouvoir plus tard l'importer et la réutiliser dans d'autres
#      scripts (par ex. un futur script qui télécharge plusieurs heures
#      dans une boucle).
#   3. De donner un nom au bloc de logique, ce qui documente l'intention.
########################################################################

# ---------------------------------------------------------------------
# Lecture de la signature de la fonction :
#
#   def download(date: str, hour: int, data_dir: Path = DATA_DIR) -> Path:
#
#   `def`            mot-clé qui démarre une définition de fonction.
#   `download`       le nom de la fonction — celui utilisé pour l'appeler
#                    plus tard.
#   `date: str`      un paramètre nommé `date`. Le `: str` qui suit est une
#                    « annotation de type » — une note (non imposée par
#                    Python à l'exécution !) indiquant aux lecteurs et aux
#                    outils de l'éditeur « ceci est censé être une chaîne
#                    de caractères ». C'est de la documentation, pas une
#                    garantie — Python ne vous empêchera pas de passer
#                    autre chose.
#   `hour: int`      un autre paramètre, annoté comme un entier.
#   `data_dir: Path = DATA_DIR`
#                    un paramètre annoté comme un objet Path, avec une
#                    VALEUR PAR DÉFAUT de DATA_DIR. Les valeurs par défaut
#                    signifient que l'appelant peut omettre entièrement cet
#                    argument, auquel cas il reviendra automatiquement à
#                    DATA_DIR. C'est ce qui permet à des tests ou à du code
#                    futur de changer l'emplacement d'enregistrement des
#                    fichiers sans modifier la fonction elle-même.
#   `-> Path`        une annotation de type de retour : cette fonction est
#                    censée renvoyer un objet Path lorsqu'elle se termine.
# ---------------------------------------------------------------------
def download(date: str, hour: int, data_dir: Path = DATA_DIR) -> Path:
    # ---------------------------------------------------------------
    # S'assurer que le dossier de destination existe avant d'essayer d'y
    # enregistrer quoi que ce soit.
    #
    #   .mkdir(...)        « make directory » — crée le dossier.
    #   parents=True        crée aussi tout dossier parent manquant en
    #                        chemin (pas nécessaire ici puisque la racine
    #                        du projet existe déjà, mais c'est une valeur
    #                        par défaut sûre).
    #   exist_ok=True        NE PAS lever d'erreur si le dossier existe
    #                        déjà — continuer simplement en silence. Sans
    #                        cela, réexécuter le script une seconde fois
    #                        planterait à cette ligne.
    # ---------------------------------------------------------------
    data_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------
    # f-strings : un littéral de chaîne préfixé par `f` permet d'insérer
    # directement des valeurs de variables entre `{accolades}`. Cette
    # ligne construit un nom de fichier comme "2026-08-27-15.json.gz" en
    # substituant les valeurs réelles de `date` et `hour` dans le modèle.
    # ---------------------------------------------------------------
    filename = f"{date}-{hour}.json.gz"

    # Même technique de f-string, construisant l'URL de téléchargement
    # complète en insérant le nom de fichier dans le modèle d'URL connu de
    # GH Archive.
    url = f"https://data.gharchive.org/{filename}"

    # L'opérateur `/` à nouveau (venant de pathlib) : joint le Path
    # data_dir avec la chaîne filename, produisant un Path complet comme
    # C:\dev\Research\data\2026-08-27-15.json.gz — c'est là que le fichier
    # téléchargé (encore compressé) sera enregistré.
    gz_path = data_dir / filename

    # print() écrit du texte dans le terminal afin qu'un humain exécutant
    # le script voie ce qui se passe, car le téléchargement lui-même
    # (ligne suivante) peut prendre quelques secondes sans aucun retour
    # visible sinon.
    print(f"Downloading {url} ...")

    # ---------------------------------------------------------------
    # Pourquoi pas le plus simple urllib.request.urlretrieve(url, gz_path) ?
    #
    # C'était l'approche d'origine, et elle semble correcte — mais elle
    # échoue face au serveur de GH Archive avec « HTTP Error 403: Forbidden ».
    # Chaque requête HTTP porte un en-tête appelé User-Agent, qui identifie
    # quel type de client effectue la requête (un navigateur, un script,
    # etc.). urlretrieve envoie un User-Agent par défaut qui indique
    # littéralement « Python-urllib/3.14 » — et le serveur de GH Archive
    # rejette les requêtes qui ne semblent pas provenir d'un vrai
    # navigateur, comme mesure anti-bot élémentaire. 403 signifie
    # spécifiquement « j'ai compris votre requête et je la refuse » (par
    # opposition à 404, qui signifierait « ce fichier n'existe pas »).
    #
    # Le correctif : construire la requête manuellement afin de pouvoir
    # définir notre propre en-tête User-Agent, en se faisant passer pour
    # un navigateur.
    #
    #   urllib.request.Request(url, headers={...})
    #     Crée un OBJET Request — décrivant quoi récupérer et avec quels
    #     en-têtes — sans encore rien envoyer. C'est la version
    #     « manuelle » de ce que urlretrieve faisait automatiquement (et
    #     de façon peu flexible) en coulisses.
    #
    #   urllib.request.urlopen(request)
    #     Envoie réellement la requête sur le réseau et renvoie un objet de
    #     réponse, qui se comporte comme un fichier lisible : on peut en
    #     extraire des octets en flux, tout comme en lisant un fichier
    #     ouvert. Il est utilisé ici dans le MÊME bloc `with` que le
    #     fichier de sortie, afin que la réponse réseau et le fichier de
    #     destination soient correctement fermés tous les deux ensuite.
    #
    #   shutil.copyfileobj(response, f_out)
    #     Même principe de copie en flux qu'expliqué plus loin dans ce
    #     fichier pour l'étape de décompression : lire depuis `response`
    #     et écrire vers `f_out` par petits blocs, plutôt que de charger
    #     tout le téléchargement en mémoire d'abord.
    # ---------------------------------------------------------------
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request) as response, open(gz_path, "wb") as f_out:
        shutil.copyfileobj(response, f_out)
    print(f"Saved to {gz_path}")

    # ---------------------------------------------------------------
    # gz_path.with_suffix("") :
    # Les objets Path comprennent les extensions de fichier
    # (« suffixes »). `with_suffix` renvoie un NOUVEAU Path avec
    # l'extension remplacée — passer une chaîne vide la supprime
    # entièrement. Donc :
    #   C:\...\2026-08-27-15.json.gz   -->   C:\...\2026-08-27-15.json
    # Cela devient le nom de fichier cible pour la sortie décompressée.
    # (Le gz_path d'origine n'est pas modifié — les objets Path sont
    # immuables ; ceci crée un nouvel objet plutôt que de modifier gz_path
    # en place.)
    # ---------------------------------------------------------------
    json_path = gz_path.with_suffix("")
    print(f"Decompressing to {json_path} ...")

    # ---------------------------------------------------------------
    # L'INSTRUCTION `with` (un « gestionnaire de contexte »)
    #
    # Ouvrir un fichier crée une connexion active vers celui-ci, qui doit
    # être refermée une fois le travail terminé — sinon on peut fuir des
    # ressources (un bug subtil qui s'aggrave à mesure qu'on ouvre des
    # fichiers au cours de la vie d'un programme) ou laisser des données
    # partiellement écrites non transférées sur le disque. `with ... as
    # ...:` garantit que le fichier sera correctement fermé une fois le
    # bloc indenté en dessous terminé — même si une erreur survient en
    # cours de route. C'est la façon standard et idiomatique de travailler
    # avec les fichiers en Python ; on la rencontre constamment.
    #
    # Cette ligne ouvre DEUX fichiers à la fois dans un seul `with`, en
    # les combinant avec une virgule :
    #
    #   gzip.open(gz_path, "rb") as f_in
    #     Ouvre le fichier .gz téléchargé, mais en utilisant la fonction
    #     open() propre à gzip plutôt que la fonction open() intégrée
    #     ordinaire de Python. Cela signifie que les lectures depuis f_in
    #     sont automatiquement décompressées à la volée — on ne voit
    #     jamais les octets bruts compressés, seulement le contenu
    #     décompressé, comme si le fichier n'avait jamais été compressé.
    #     "rb" signifie « lecture, mode binaire » (octets bruts, pas du
    #     texte — important car les données JSON Lines doivent être
    #     traitées ici comme des octets ; on n'essaie pas encore de les
    #     interpréter/décoder, seulement de les déplacer vers un autre
    #     fichier).
    #
    #   open(json_path, "wb") as f_out
    #     Ouvre (en le créant si nécessaire) le fichier .json de
    #     destination en texte brut, pour l'écriture. "wb" signifie
    #     « écriture, mode binaire » — correspondant au mode binaire de
    #     f_in, puisqu'on copie des octets bruts, pas du texte.
    # ---------------------------------------------------------------
    with gzip.open(gz_path, "rb") as f_in, open(json_path, "wb") as f_out:
        # ---------------------------------------------------------------
        # shutil.copyfileobj(f_in, f_out) :
        # Lit depuis f_in et écrit vers f_out par petits blocs (une taille
        # de tampon interne par défaut), en bouclant jusqu'à ce que f_in
        # soit épuisé. Le principal avantage par rapport à quelque chose
        # comme `f_out.write(f_in.read())` est l'utilisation de la
        # mémoire : `f_in.read()` chargerait la TOTALITÉ du fichier
        # décompressé en mémoire d'un seul coup avant d'en écrire quoi que
        # ce soit. Pour un fichier volumineux, cela pourrait utiliser une
        # grande quantité de RAM d'un coup. copyfileobj le diffuse à la
        # place par petits morceaux, gardant l'utilisation de la mémoire
        # basse quelle que soit la taille totale du fichier.
        # ---------------------------------------------------------------
        shutil.copyfileobj(f_in, f_out)

    # Une fois le bloc `with` ci-dessus terminé, les deux fichiers ont été
    # automatiquement fermés. On informe maintenant l'utilisateur que
    # c'est terminé.
    print(f"Done: {json_path}")

    # Renvoie le chemin vers le fichier final, décompressé, afin que le
    # code appelant (voir main(), ci-dessous) — ou quiconque importe cette
    # fonction depuis un autre script — puisse immédiatement savoir où les
    # données exploitables ont atterri, sans avoir à reconstruire le
    # chemin lui-même.
    return json_path


########################################################################
# parse_args() : transformer les drapeaux de ligne de commande en un
# objet structuré
########################################################################
def parse_args() -> argparse.Namespace:
    # ---------------------------------------------------------------
    # argparse.ArgumentParser(...) crée un objet « analyseur » qui sait
    # lire la liste des mots tapés après `python
    # scripts/download_gharchive.py` sur la ligne de commande (par ex.
    # `--date 2026-08-27 --hour 15`) et les transformer en valeurs
    # Python.
    #
    # `description=__doc__` réutilise la docstring du module de ce
    # fichier (la chaîne entre triples guillemets tout en haut du
    # fichier) comme texte descriptif affiché quand quelqu'un exécute le
    # script avec `--help`. C'est exactement l'idée « les docstrings
    # peuvent être relues par des outils » mentionnée en haut de ce
    # fichier, mise en pratique.
    # ---------------------------------------------------------------
    parser = argparse.ArgumentParser(description=__doc__)

    # ---------------------------------------------------------------
    # Enregistrement du drapeau `--date` :
    #   "--date"              le nom du drapeau tel que tapé sur la ligne
    #                          de commande (par ex. `--date 2026-08-27`).
    #   default=DEFAULT_DATE   si l'utilisateur ne passe pas `--date` du
    #                          tout, utiliser cette valeur à la place —
    #                          c'est ce qui permet d'exécuter le script
    #                          SANS aucun argument et que cela fonctionne
    #                          quand même, en utilisant la date fixe du
    #                          jeu de données du projet.
    #   help=...               affiché dans la sortie de `--help`,
    #                          expliquant ce que fait ce drapeau et
    #                          quelle est sa valeur par défaut actuelle.
    # (Aucun `type=` n'est fourni ici, donc argparse traite la valeur
    # comme une simple chaîne de caractères par défaut — ce qui est ce
    # qu'on veut pour une date écrite comme "YYYY-MM-DD".)
    # ---------------------------------------------------------------
    parser.add_argument(
        "--date",
        default=DEFAULT_DATE,
        help=f"Date in YYYY-MM-DD format (default: {DEFAULT_DATE})",
    )

    # ---------------------------------------------------------------
    # Enregistrement du drapeau `--hour` :
    #   type=int               contrairement à --date, on spécifie bien
    #                          un type ici. Les entrées de ligne de
    #                          commande arrivent toujours sous forme de
    #                          texte (par ex. les caractères "1", "5"),
    #                          donc `type=int` indique à argparse de les
    #                          convertir en un véritable entier Python
    #                          (15) avant de nous le rendre — et de lever
    #                          automatiquement une erreur claire si
    #                          l'utilisateur tape quelque chose qui n'est
    #                          pas un entier valide (par ex.
    #                          `--hour fifteen`).
    #   default=DEFAULT_HOUR    même idée que précédemment : revenir à
    #                          l'heure fixe du projet si non spécifiée.
    #   choices=range(0, 24)    restreint les valeurs valides de 0 à 23
    #                          inclus (range(0, 24) génère
    #                          0,1,2,...,23). Si l'utilisateur passe une
    #                          valeur hors de cette plage, argparse la
    #                          rejette automatiquement avec un message
    #                          d'erreur, avant même que notre propre code
    #                          ne s'exécute — on n'a pas besoin d'écrire
    #                          cette validation nous-mêmes.
    #   metavar="[0-23]"        purement cosmétique : contrôle la façon
    #                          dont l'argument est affiché dans le texte
    #                          de `--help`, en montrant "[0-23]" plutôt
    #                          que le comportement par défaut d'argparse
    #                          (qui essaierait de lister les 24 choix
    #                          individuels).
    # ---------------------------------------------------------------
    parser.add_argument(
        "--hour",
        type=int,
        default=DEFAULT_HOUR,
        choices=range(0, 24),
        metavar="[0-23]",
        help=f"UTC hour, 0-23 (default: {DEFAULT_HOUR})",
    )

    # ---------------------------------------------------------------
    # parser.parse_args() :
    # Lit réellement les arguments de ligne de commande avec lesquels le
    # script a été lancé (Python les expose en interne via sys.argv) et
    # renvoie un objet « Namespace » — que l'on peut voir comme un simple
    # conteneur où chaque drapeau devient un attribut. Après cette ligne,
    # on peut accéder à `args.date` et `args.hour` comme des valeurs
    # Python ordinaires (respectivement un str et un int), entièrement
    # analysées et validées.
    # ---------------------------------------------------------------
    return parser.parse_args()


########################################################################
# main() : le point d'entrée du script
#
# Par convention, les scripts Python regroupent souvent leur logique de
# premier niveau dans une fonction appelée `main`, plutôt que d'écrire
# cette logique librement en bas du fichier. Ce n'est pas un nom
# spécial/magique pour Python lui-même — c'est simplement une convention
# forte — mais cela garde la logique « que se passe-t-il quand on exécute
# ce fichier » organisée en un seul endroit clairement nommé.
########################################################################
def main() -> None:
    # `-> None` dans la signature est une annotation de type signifiant
    # « cette fonction ne renvoie pas de valeur significative » (elle se
    # contente d'effectuer des actions).

    # Demande à parse_args() (définie ci-dessus) de lire et de valider les
    # drapeaux de ligne de commande, en nous rendant un Namespace avec
    # .date et .hour déjà renseignés (soit à partir de ce que l'utilisateur
    # a tapé, soit à partir des valeurs par défaut).
    args = parse_args()

    # Appelle la fonction download() définie précédemment, en lui passant
    # la date et l'heure analysées. Notez que `data_dir` n'est PAS passé
    # ici — la valeur par défaut de ce paramètre (DATA_DIR) est utilisée
    # automatiquement, puisqu'on n'a pas besoin de la surcharger dans un
    # usage normal.
    download(args.date, args.hour)


########################################################################
# LA GARDE `if __name__ == "__main__":`
#
# Chaque module Python (fichier) reçoit automatiquement une variable
# intégrée appelée `__name__`. Sa valeur dépend de LA FAÇON dont le
# fichier est utilisé :
#
#   - Si vous exécutez le fichier directement depuis la ligne de commande
#     (`python scripts/download_gharchive.py`), Python définit `__name__`
#     à la chaîne "__main__" pour ce fichier.
#
#   - Si, au contraire, ce fichier est importé depuis ailleurs
#     (`import download_gharchive` dans un autre script), Python définit
#     `__name__` au nom du module lui-même ("download_gharchive") plutôt
#     qu'à "__main__".
#
# Ce test `if` signifie donc : « n'appeler main() — c'est-à-dire n'effectuer
# un téléchargement — que lorsque ce fichier est exécuté directement, pas
# lorsqu'il est simplement importé. »
#
# Pourquoi cette distinction compte-t-elle ? Elle permet à quelqu'un
# d'écrire plus tard un script différent qui fait :
#
#   from download_gharchive import download
#   download("2026-08-20", 9)
#
# ...et de réutiliser la fonction download() pour une heure différente,
# SANS déclencher le téléchargement par défaut du fichier comme effet de
# bord juste en l'important. Sans cette garde, importer le fichier
# exécuterait immédiatement main() aussi, ce qui n'est presque jamais ce
# qu'on souhaite d'un import.
########################################################################
if __name__ == "__main__":
    main()
