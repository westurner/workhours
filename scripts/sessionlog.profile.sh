#!/bin/bash

# Bash profile script for logging unique console sessions in userspace

randstr() {
    # Generate a random string
    # param $1: number of characters
    echo `dd if=/dev/urandom bs=1 count=$1 2>/dev/null | base64 -w 0 | rev | cut -b 2- | tr '/+' '0' | rev`
}

SESSION_LOG="$HOME/.session_log"

TERM_ID=$(randstr 8)

#TERM_SED_STR='s/^\s*[0-9]*\s\(.*\)/$TERM_ID: \1/'
TERM_SED_STR='s/^\s*[0-9]*\s*//'

writehistline() {
    # Write a line to the SESSION_LOG file
    # param $1: text (command) to log
    printf "%-11s: %s ::: %s\n" "$TERM_ID" "`date +'%D %R'`" "$1" >> $SESSION_LOG
}

writelastcmd() {
    writehistline "$(history 1 | sed -e $TERM_SED_STR)";
}

set_term_id() {
    # Set an explicit terminal name
    # param $1: terminal name
    RENAME_MSG="# Renaming $TERM_ID to $1 ..."
    echo $RENAME_MSG
    writehistline "$RENAME_MSG" 
    export TERM_ID="__$1"
}

stid() {
    # Shortcut alias to set_term_id
    set_term_id $@
}

stlog() {
    # Alias to less the current session log
    less $SESSION_LOG $@
}

stgrep() {
    # Grep for specific sessions
    # param $1: session name
    # param $2: don't strip the line prefix
    NO_STRIP_LINE_PREFIX=$2
    cat $SESSION_LOG | egrep "$1 .* \:\:\:|Renaming .* to $1" | \
        if [ $NO_STRIP_LINE_PREFIX -n ]; then
            sed -e 's/^\s*.*\:\:\:\s\(.*\)/\1/'
        else
            cat
        fi
}

#TODO: if REM_SHELL; 
#echo "# Starting terminal session: $TERM_ID"
touch $SESSION_LOG

PROMPT_COMMAND="writelastcmd;" #$PROMPT_COMMAND"


# Respect: http://ubuntuforums.org/archive/index.php/t-1710642.html
screenrec() {
    # Record the screen
    # param $1: destination directory (use /tmp if possible)
    # param $2: video name to append to datestamp

    # Press "q" to stop recording

    FILEBASE="screenrec-`date +%Y%m%d-%H%M`"
    if [ -z "$2" ]; then
        FILENAME="$1/${FILEBASE}_unnamed.mpg"
    else
        FILENAME="$1/${FILEBASE}_${2}.mpg"
    fi

    ffmpeg -f x11grab -s `xdpyinfo | grep 'dimensions:'|awk '{print $2}'` -r 25 -i :0.0 -sameq "$FILENAME" > "$FILENAME.txt"
}
