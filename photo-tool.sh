#!/bin/bash

# This script is the main entry point for the finance module. It can be used to run various importers and other finance-related tasks.

PHY_ENV=.photo_tool_env

help() {
    echo "Usage: $0 [options] [arguments]"
    echo ""
    echo "Options:"
    echo "  -i, --install     Create virtual environment and install dependencies"
    echo "      --enter       Open an interactive shell with the virtualenv activated"
    echo "      --print-activate  Print the activation command after install"
    echo "      --leave       Deactivate the virtualenv in the current shell (works when script is sourced)"
    echo "  --help            Show this help message and exit"
    echo ""
    echo "Arguments:"
    echo "  [arguments]       Arguments to pass to the finance.py script (e.g., importer name)"
}

main() {
    INSTALL=false
    ENTER=false
    PRINT_ACTIVATE=false
    LEAVE=false

    # collect options first
    while [[ "$1" == -* ]]; do
        case "$1" in
            -i|--install)
                INSTALL=true
                ;;
            --enter)
                ENTER=true
                ;;
            --print-activate)
                PRINT_ACTIVATE=true
                ;;
            --leave)
                LEAVE=true
                ;;
            --help)
                help
                exit 0
                ;;
            *)
                # stop option parsing on unknown / positional
                break
                ;;
        esac
        shift
    done

    if [ "$INSTALL" = true ]; then
        echo "Creating virtual environment and installing dependencies..."
        if [ ! -d "$PHY_ENV" ]; then
            python3 -m venv $PHY_ENV
        fi
        # source in this process so exec $SHELL inherits the env
        source $PHY_ENV/bin/activate
        pip install -r requirements.txt
        echo "Environment setup complete."
        if [ "$PRINT_ACTIVATE" = true ]; then
            echo "Run: source $PHY_ENV/bin/activate"
        fi
        if [ "$ENTER" = true ]; then
            $SHELL
        fi
        exit 0
    fi

    if [ "$LEAVE" = true ]; then
        # If the script is sourced, BASH_SOURCE[0] != $0
        if [ "${BASH_SOURCE[0]}" != "$0" ]; then
            if type deactivate >/dev/null 2>&1; then
                deactivate
                echo "Virtualenv deactivated."
            else
                echo "No active virtualenv detected in this shell."
            fi
            return 0 2>/dev/null || exit 0
        else
            echo "This command must be sourced to deactivate the current shell's virtualenv."
            echo "Run: source ./photo-tool.sh --leave"
            echo "Or manually run: deactivate"
            exit 0
        fi
    fi

    # check execution environment
    if [ ! -d "$PHY_ENV" ]; then
        echo "Environment not found. Please run this script with -i option to create the environment and install dependencies."
        exit 1
    fi

    source $PHY_ENV/bin/activate

    if [ "$ENTER" = true ]; then
        $SHELL
    fi
}

main "$@"
