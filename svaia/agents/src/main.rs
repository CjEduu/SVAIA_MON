mod types;

use config::{Config, File};
use futures_util::{SinkExt, StreamExt};
use jiff;
use notify::{self, Event, RecommendedWatcher, Watcher};
use serde::Deserialize;
use serde_json;
use std::sync::Arc;
use std::{io, path::PathBuf};
use sysinfo::System;
use tokio::{
    fs::OpenOptions,
    io::AsyncWriteExt,
    net::TcpStream,
    runtime::Handle,
    sync::{
        Mutex,
        mpsc::{self, Receiver},
    },
    time::{Duration, sleep},
};
use tokio_tungstenite::{
    WebSocketStream, connect_async,
    tungstenite::{self, protocol::Message},
};
use types::{SharedWriteHalf, SystemMetric, SystemMetricError, ToLog, ValidMetrics};
use url;

impl From<tungstenite::Error> for SystemMetricError {
    fn from(err: tungstenite::Error) -> Self {
        SystemMetricError::WebSocket(err)
    }
}

impl From<io::Error> for SystemMetricError {
    fn from(err: io::Error) -> Self {
        SystemMetricError::Io(err)
    }
}

async fn log_to_file(message: &str) -> Result<(), SystemMetricError> {
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open("agent.log")
        .await?;

    let timestamp = jiff::Timestamp::now();
    let log_message = format!("[{}] {}\n", timestamp, message);
    file.write_all(log_message.as_bytes()).await?;
    file.flush().await?;
    Ok(())
}

async fn connect_with_retry(
    url: &str,
    max_attempts: u32,
) -> Result<WebSocketStream<tokio_tungstenite::MaybeTlsStream<TcpStream>>, SystemMetricError> {
    let delays: Vec<u64> = vec![5, 10, 30, 60, 300];
    for (attempts, delay) in delays.iter().enumerate() {
        match connect_async(url).await {
            Ok((ws_stream, _)) => return Ok(ws_stream),
            Err(e) => {
                // Log the error to file
                if let Err(log_err) =
                    log_to_file(&format!("Connection attempt {} failed: {}", attempts, e)).await
                // Hace la conversión &String->&str automatica? simplemente sería &*format!...?
                {
                    eprintln!("Failed to log to file: {:?}", log_err);
                }
                eprintln!(
                    "Connection attempt {} failed: {}. Retrying in {:?}",
                    attempts, e, delay
                );
                sleep(Duration::from_secs(delay.clone())).await; // Este clone me huele a que se puede hacer mejor de otra forma
            }
        }
    }

    return Err(SystemMetricError::ConnectionFailure(format!(
        "Failed to connect after {} attempts",
        max_attempts
    )));
}

async fn send_system_metrics(
    write_sink: SharedWriteHalf,
    metrics_tx: tokio::sync::mpsc::Sender<String>,
) -> Result<(), SystemMetricError> {
    println!("Into system_metrics_thread!");
    let mut system_metrics = SystemMetric::new_empty();
    let mut system = System::new_all();
    // Maybe need to wait here a second i dont remember if it suffered from that
    loop {
        system_metrics.get_metrics(&mut system);
        let data = serde_json::to_value(&system_metrics).unwrap(); // TODO: Match parsing errors
        let message = ToLog::create_message(ValidMetrics::SystemMetric, data);

        // Always log to file via channel
        if let Err(e) = metrics_tx.send(message.clone()).await {
            eprintln!("Failed to queue message for logging: {}", e);
        }

        // Attempt to send via WebSocket
        let mut guard = write_sink.lock().await;
        match guard.send(Message::Text(message.into())).await {
            Ok(_) => {}
            Err(e) => {
                eprintln!("WebSocket send error: {}. Continuing to log to file.", e);
                drop(guard);
                return Err(e.into());
            }
        }
        drop(guard);
        sleep(Duration::from_secs(2)).await;
    }
}

fn create_async_watcher() -> notify::Result<(RecommendedWatcher, Receiver<notify::Result<Event>>)> {
    let (mut tx, rx) = mpsc::channel(100);

    // Automatically select the best implementation for your platform.
    let handle = Handle::current();
    let watcher = RecommendedWatcher::new(
        move |res: Result<notify::Event, notify::Error>| {
            handle.block_on(async {
                tx.send(res).await.unwrap();
            })
        },
        notify::Config::default(),
    )?;

    Ok((watcher, rx))
}

async fn watch_files(
    write_sink: SharedWriteHalf,
    log_tx: tokio::sync::mpsc::Sender<String>,
    files: Vec<PathBuf>,
) -> Result<(), notify::Error> {
    let (mut watcher, mut rx) = create_async_watcher()?;

    for path in files {
        match watcher.watch(&path, notify::RecursiveMode::Recursive) {
            Ok(_) => {}
            Err(err) => {
                eprintln!("Couldnt' watch file {:?}:{} ", path, err);
            }
        }
    }

    // Wait for events
    while let Some(res) = rx.recv().await {
        let message = match res {
            Ok(event) => {
                let data = serde_json::to_value(&event).unwrap(); // TODO: Match parsing errors
                ToLog::create_message(ValidMetrics::FileLog, data)
            }
            Err(e) => {
                println!("watch error: {:?}", e);
                ToLog::create_message(
                    ValidMetrics::FileLog,
                    serde_json::to_value(format!("Error watching file: {}", e)).unwrap(),
                )
            }
        };

        println!("Message_sent: {}", message);
        // Always log to file via channel
        if let Err(e) = log_tx.send(message.clone()).await {
            eprintln!("Failed to queue message for logging: {}", e);
        }

        // Attempt to send via WebSocket
        let mut guard = write_sink.lock().await;
        match guard.send(Message::Text(message.into())).await {
            Ok(_) => {}
            Err(e) => {
                eprintln!("WebSocket send error: {}. Continuing to log to file.", e);
                drop(guard);
                return Err(notify::Error::new(notify::ErrorKind::Generic(
                    "Error Websocket".into(),
                )));
            }
        }
        drop(guard);
        sleep(Duration::from_secs(2)).await;
    }

    Ok(())
}

#[derive(Debug, Deserialize)]
struct Settings {
    url: String,
    files: Vec<PathBuf>,
    token: String,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let settings = Config::builder()
        .add_source(File::with_name("Settings"))
        .build()
        .unwrap();

    // Deserialize (and thus freeze) the entire configuration
    let settings = settings.try_deserialize::<Settings>().unwrap();

    let url = url::Url::parse(&settings.url).expect("Failed to parse URL");
    let end_host = url.host_str().unwrap_or("UNKNOWN ENDPOINT");
    let token = settings.token;
    let files = settings.files;

    // Only Ws connections
    match url.scheme() {
        "ws" => println!(
            "WARNING: INITIATING NON-ENCRYPTED CONNECTION WITH {:?}",
            end_host
        ),
        "wss" => println!("INFO: INITIATING ENCRYPTED CONNECTION WITH {:?}", end_host),
        _ => return Err("ENDPOINT URI.SCHEME SHOULD BE WS/WSS".into()),
    }

    // Create channel for file logging
    let (logging_tx, mut logging_rx) = mpsc::channel::<String>(100);

    // Spawn file logger thread
    tokio::spawn(async move {
        while let Some(message) = logging_rx.recv().await {
            if let Err(e) = log_to_file(&message).await {
                eprintln!("Failed to log metrics to file: {:?}", e);
            }
        }
    });

    // MAIN LOOP ------
    loop {
        match connect_with_retry(url.as_str(), 5).await {
            Ok(ws_stream) => {
                // AUTH ---------------
                println!("Successfully connected to WebSocket");

                // Split the channel to get the sink
                let (mut write, _) = ws_stream.split();
                write
                    .send(Message::text(&token))
                    .await
                    .expect("Failed to send token");

                let shared_write_sink: SharedWriteHalf = Arc::new(Mutex::new(write));

                // TASKS --------------

                // ---------- SYSTEM METRICS TASK
                let write_sink_clone = Arc::clone(&shared_write_sink);
                let logging_tx_clone = logging_tx.clone();
                let mut system_metrics_handle = tokio::spawn(async {
                    send_system_metrics(write_sink_clone, logging_tx_clone).await
                });

                // ---------- FILEWATCHER TASK
                let write_sink_clone_2 = Arc::clone(&shared_write_sink);
                let loggin_tx_clone_2 = logging_tx.clone();
                let files_clone = files.clone();
                let mut filewatcher_handle = tokio::spawn(async {
                    watch_files(write_sink_clone_2, loggin_tx_clone_2, files_clone).await
                });

                // WAIT FOR THREADS --------------- ? TODO: Maybe this is not the way lol
                tokio::select! {
                    result = &mut system_metrics_handle => {
                            eprintln!("Task system_metrics_task failed, initiating reconnection");
                            match result {
                                Ok(_)=>{
                                }
                                Err(err) => {
                                    // restart
                                    eprintln!("System metrics handler failed: {}",err);
                                }
                            }
                    }
                    result = &mut filewatcher_handle => {
                            match result {
                                Ok(_) => {
                                }
                                Err(err) => {
                                    //restart
                                    eprintln!("File watching failed: {}",err);
                                }
                            }

                    }
                }

                // Wait before checking for reconnection
                sleep(Duration::from_secs(5)).await;
            }
            Err(e) => {
                eprintln!("Connection failed: {:?}", e);
                // Continue logging to file during reconnection attempts
                sleep(Duration::from_secs(5)).await;
                continue;
            }
        }
    }
}
