# 📹 Multi-Camera RTSP Face Detection Processor

This Python application captures video streams from multiple RTSP-enabled CCTV cameras, detects faces using [InsightFace](https://github.com/deepinsight/insightface), and sends valid frames to a central server via HTTP POST requests.

It supports:

- ✅ Real-time face detection
- 🌙 Low-light enhancement
- 🔍 Blur detection
- 📡 Multi-camera support
- ⚙️ Production-ready deployment on Linux using `systemd`

---


## 🚀 Deployment

To deploy this project run

```bash
  chmod +x deploy.sh
  ./deploy.sh
```

## 🔧 Requirements

Make sure your Linux server has the following:

- Python 3.10 or newer
- FFmpeg installed (`sudo apt install ffmpeg`)
- OpenCV dependencies:
```bash
  sudo apt install libgl1 libglib2.0-0
```

## 🟢 START

```bash
  sudo systemctl start face-stream
```
## 🔴 STOP

```bash
  sudo systemctl stop face-stream
```

## 🔁 RESTART

```bash
  sudo systemctl restart face-stream
```

## 🔍 Monitoring & Logs

The application generates logs using systemd. You can view logs as follows:
View live logs:

```bash
  sudo journalctl -u face-stream -f
```

This will show real-time logs of the application's activity.
Check recent logs:

```bash
  journalctl -u face-stream --since "1 hour ago"
```
You can adjust the --since option to check logs from a specific time frame.
