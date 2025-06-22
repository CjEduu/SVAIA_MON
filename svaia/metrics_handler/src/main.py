from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from metrics_handler.src.utils import validate_data
from secure_log_manager.src.SecureLogManager import (
    SecureLogManager,
    monitor_funciones,
)

# Inicializar Log manager
# TODO Make this customizable
parent_path = Path(__file__).parent.parent
absolute_log_path = Path( parent_path / "logs/metrics_handler.log").resolve()
if not absolute_log_path.exists():
    open(absolute_log_path,'x').close()

log_manager = SecureLogManager(debug_mode=10)
log_manager.configure_logging(absolute_log_path)
log_manager.inicializar_log()
log_function = monitor_funciones(log_manager)


app = FastAPI()
project_clients:dict[str,list[WebSocket]] = {}

def validate_token(token: str) -> bool:
    """
       Debe conectarse con la BD y checkear el token. 
    """
    valid_tokens_mock = set(["token1","token2","token3"])
    return token in valid_tokens_mock

@app.websocket("/ws/agent")
@log_function("info")
async def agent_endpoint(websocket: WebSocket):
    """
        Espera una conexión WS en la que primero debe recibir un token con el que se autenticará la conexión
        y luego se iniciará el log
    """
    await websocket.accept()
    try:
        # Receive and validate token from the client
        token = await websocket.receive_text()

        # We should also know where to insert the logs given the token as
        # Project <-> Token relationship is 1 to 1
        if not validate_token(token):
            await websocket.close(code=1008,reason="Invalid project token")  # Invalid token
            return 

        #PubSub list 
        # TODO, everything that needs to identify a project and does it with a token, change it
        # to do it with project id by retrieving it once when validating the token
        # If i were in rust, validate_token could return Result(proyect_name) 
        # and then match on the error so i avoid storing tokens in mem >:/
        if token not in project_clients:
            project_clients[token] = []
        
        # Token is valid; handle monitoring data
        while True:
            data = await websocket.receive_text()
            # Process data (e.g., log it, save to DB, etc.)
            # We should have a table of Projects with a column that links to a table Agents with like name | bla | bla | bla
            # Also we should buffer them and be storing them like every 20 msgs or sum
            structured_data = validate_data(data)
            if structured_data is None:
                # Log that you where unable to parse the data
                # Keep receiving and do not send it
                # Maybe i can create a special msg that signals unparsable data was sent?
                continue
            
            # Forward it to clients listening
            # Currently, this is a kind of naive way to do it. If we were using raw websockets we could use its broadcasting internals
            # We copy as depicted in https://websockets.readthedocs.io/en/stable/topics/broadcast.html
            # project_clients[token] should never raise KeyNotFoundError as we are populating it with [] when connecting the agent
            # worst case we copy a []
            for client in project_clients[token].copy(): 
                await client.send_text(structured_data.model_dump_json())

            print(f"Project {token} agent sent: {data}")

    except WebSocketDisconnect:
        print(f"Agent disconnected from project {token}")



@app.websocket("/ws/get_data")
@log_function("info")
async def client_endpoint(websocket:WebSocket):
    """
        Function to subscribe to an specific project data stream    
    """
    await websocket.accept()
    # Need authentication first
    try:
        token = await websocket.receive_text()
        if not validate_token(token):
            await websocket.close(code=1008,reason="Invalid project token")  # Invalid token
            return

        # PubSub mechanism, same thing todo as in the other func
        # Currently you can suscribe to a non agent populated project
        project_clients.setdefault(token,[]).append(websocket)
        print(f"Client subscribed to project {token}")
        
        while True:
            # This seems to be the only way to keep alive the connection. At least in the 
            # fast API/ Starlette implementation
            await websocket.receive_text()

    except WebSocketDisconnect:
        project_clients[token].remove(websocket)
        print("Client disconected")

    
#For encrypted data, we enable the TSL,SSL certificates here
#if __name__ == "__main__":
#    uvicorn.run(
#        app,
#        host="0.0.0.0",
#        port=8000,
#        ssl_keyfile="path/to/key.pem",
#        ssl_certfile="path/to/cert.pem"
#    )
