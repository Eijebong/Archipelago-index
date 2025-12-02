INDEX_ROOT=$1

if [[ "$INDEX_ROOT" == "" ]]; then
    echo "Usage: add_supported.sh index_root"
    exit 1
fi

if [[ ! -d "$INDEX_ROOT" ]] then
    echo "Provided index root isn't a directory"
    exit 1
fi

if [[ ! -d "$INDEX_ROOT/index" ]] then
    echo "Provided index root isn't an index"
    exit 1
fi

git clone https://github.com/ArchipelagoMW/Archipelago.git /tmp/ap
(cd /tmp/ap && git reset --hard 0.6.4)
(cd /tmp/ap && find . -type f -exec dos2unix {} \;)

for f in /tmp/ap/worlds/*; do
    if [[ -f $f ]]; then
        continue
    fi

    if [[ "$(basename $f)" == _* ]]; then
        continue;
    fi

    echo $f
    GAME=$(cat $f/__init__.py | grep "game.*= \".*\"$" | head -n1 | sed "s/.*game.*= \"\(.*\)\"/\\1/")
    if [[ "$GAME" == "" ]]; then
        if [[ -f $f/world.py ]]; then
            GAME=$(cat $f/world.py | grep "game.*= \".*\"$" | head -n1 | sed "s/.*game.*= \"\(.*\)\"/\\1/")
        fi
    fi
    # LADX is a special child and defines its world name from a const for some reason so we can't easily guess it.
    if [[ "$(basename $f)" == "ladx" ]]; then
        GAME="Links Awakening DX"
    fi

    # same with stardew valley
    if [[ "$(basename $f)" == "stardew_valley" ]]; then
        GAME="Stardew Valley"
    fi

    # same with saving princess
    if [[ "$(basename $f)" == "saving_princess" ]]; then
        GAME="Saving Princess"
    fi

    # And jakanddaxter
    if [[ "$(basename $f)" == "jakanddaxter" ]]; then
        GAME="Jak and Daxter: The Precursor Legacy"
    fi

    # And shapez
    if [[ "$(basename $f)" == "shapez" ]]; then
        GAME="shapez"
    fi

    if [[ "$GAME" == "" ]]; then
        echo "Couldn't find game name for $f, aborting"
        exit 1
    fi

    INDEX_FILE="name = \"${GAME}\"\nhome = \"https://archipelago.gg\"\nsupported = true"
    echo -e ${INDEX_FILE} > "${INDEX_ROOT}/index/$(basename $f).toml"
done

rm -Rf /tmp/ap
