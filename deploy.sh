#!/bin/bash


PID_FILE="services.pid"

echo "Initializing.."

cd svaia/

start_web_gui(){
  cd web-gui/

  flask --debug --app app.py run --port 4444 &
  WEB_PID=$!

  cd ..
  echo $WEB_PID >> $PID_FILE
}

start_api() {
   cd web_api/
   
   flask --debug --app app.py run --port 4447 &
   API_PID=$! 
   echo "API server started with PID: $API_PID"

   cd ..
   echo $API_PID >> $PID_FILE # Append PID to the file
}

start_metrics_handler(){
  cd metrics_handler/src

  fastapi dev --port 4445 &
  MET_PID=$!

  cd ../..
  echo $MET_PID >> $PID_FILE
}

start_sbom_analyzer(){
  cd sbom_analyzer/src

  fastapi dev --port 4446 &
  SBM_PID=$!

  cd ../..
  echo $SBM_PID >> $PID_FILE
}

stop_all(){
  if [ -f "$PID_FILE" ]; then
      echo "Stopping servers..."
      while read PID; do
        if ps -p $PID > /dev/null; then
          echo "Killing process $PID..."
          kill $PID
        else
          echo "Process $PID not found, likely already stopped."
        fi
      done < "$PID_FILE"
      rm "$PID_FILE" # Remove the PID file after killing processes
      echo "Servers stopped."
  else
      echo "PID file not found. Are the servers running?"
  fi
}

case "$1" in
    start)
      # Clean up any old PID file
      if [ -f "$PID_FILE" ]; then
        echo "Removing old PID file: $PID_FILE"
        rm "$PID_FILE"
      fi
      # Set dev mode for flask
      start_web_gui
      sleep 1

      start_metrics_handler
      sleep 1

      start_sbom_analyzer
      sleep 1

      start_api
      sleep 1
      
      ;;
    stop)
      stop_all
      ;;
    *)
      echo "Usage: $0 {start|stop}"
      exit 1
      ;;
  esac
