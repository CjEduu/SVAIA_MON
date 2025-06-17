use futures_util::stream::SplitSink;
use gethostname::gethostname;
use jiff;
use serde::Serialize;
use serde_json;
use std::fmt::Debug;
use std::io;
use std::sync::Arc;
use sysinfo::System;
use tokio::{net::TcpStream, sync::Mutex};
use tokio_tungstenite::{
    WebSocketStream,
    tungstenite::{self, protocol::Message},
};

pub type SharedWriteHalf =
    Arc<Mutex<SplitSink<WebSocketStream<tokio_tungstenite::MaybeTlsStream<TcpStream>>, Message>>>;

#[derive(Serialize)]
pub enum ValidMetrics {
    SystemMetric,
    FileLog,
}

#[derive(Serialize)]
pub struct ToLog {
    message_type: ValidMetrics,
    host: String,
    timestamp: jiff::Timestamp,
    data: serde_json::Value, // Json, couldnt manage to get around lifetimes, not worth for this mock project
}

impl ToLog {
    pub fn create_message(in_message_type: ValidMetrics, in_data: serde_json::Value) -> String {
        let result = ToLog {
            message_type: in_message_type,
            host: gethostname().into_string().unwrap_or("Unknown".into()), // LMAO
            timestamp: jiff::Timestamp::now(),
            data: in_data,
        };
        serde_json::to_string(&result).unwrap() // TODO Manage parsing errors
    }
}

#[derive(Serialize)]
pub struct FileLog {
    attrs: serde_json::Value,
    kind: String,
    mode: String,
    paths: Vec<String>,
    event_type: String,
}

#[derive(Debug, Serialize)]
pub struct SystemMetric {
    total_memory: u64, // In MB
    used_memory: u64,
    total_swap: u64,
    used_swap: u64,
    cpu_usage: f32,
    load_avg: (f64, f64, f64),
    uptime: u64, // In seconds
}

impl SystemMetric {
    pub fn new_empty() -> SystemMetric {
        SystemMetric {
            total_memory: 0,
            used_memory: 0,
            total_swap: 0,
            used_swap: 0,
            cpu_usage: 0.0,
            load_avg: (0.0, 0.0, 0.0),
            uptime: 0,
        }
    }

    pub fn get_metrics(&mut self, system: &mut System) {
        system.refresh_all();
        self.total_memory = system.total_memory() >> 20;
        self.used_memory = system.used_memory() >> 20;
        self.total_swap = system.total_swap() >> 20;
        self.used_swap = system.used_swap() >> 20;
        self.cpu_usage = system.global_cpu_usage();
        self.load_avg = {
            let avg = System::load_average();
            (avg.one, avg.five, avg.fifteen)
        };
        self.uptime = System::uptime();
    }
}

#[derive(Debug)]
pub enum SystemMetricError {
    WebSocket(tungstenite::Error),
    Io(io::Error),
    ConnectionFailure(String),
}
