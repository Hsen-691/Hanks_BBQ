#!/bin/bash
# Start the Hank's BBQ backend (serves the API and the website on APP_PORT).
cd "$(dirname "$0")" || exit 1

if [ ! -f ".venv/bin/activate" ]; then
  echo "Could not find the virtual environment at .venv"
  echo "Create it first:  python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt"
  echo
  read -n 1 -s -r -p "Press any key to continue..."
  exit 1
fi

source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app

# If uvicorn exits with an error (e.g. port 8000 already in use), keep the
# window open so the message is readable instead of flashing closed.
if [ $? -ne 0 ]; then
  echo
  echo "The server stopped with an error (see the message above)."
  echo "If it says the address is already in use, port 8000 is taken by another"
  echo "instance - close it, or change the port, then run this again."
  echo
  read -n 1 -s -r -p "Press any key to continue..."
fi
