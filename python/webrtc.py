import logging
import re
import time
import threading

import aiortc.mediastreams
import socketio
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, RTCConfiguration, RTCIceServer
import cv2
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder

# Configure logging
logging.basicConfig(level=logging.INFO)

# Signaling server configuration
SIGNALING_SERVER = "http://192.168.33.217:9999"

# ICE servers configuration
ICE_SERVERS = [
    RTCIceServer(urls="stun:47.120.76.27:3478", username="bobo", credential="123456")
]
pc = RTCPeerConnection(RTCConfiguration(iceServers=ICE_SERVERS))
sio = socketio.Client()

asyncio_loop = asyncio.new_event_loop()


@sio.event
def connect():
    print("Connected to signaling server")
    sio.emit("self_dial_in", {"from": "接收方", "to": "提供方"})  # 向服务器发送事件


@sio.event
def disconnect():
    print("Disconnected from signaling server")
    attempt_reconnect()
@sio.event
def connect_error(data):
    print("Connection failed with error:", data)
    attempt_reconnect()


@sio.on("IceInfo")
def on_ice_info(data):
    # pass
    print("Received IceInfo:",data)
    candidate = parse_candidate(data["candidate"])
    candidate.sdpMid = data["id"]
    candidate.sdpMLineIndex = data["label"]
    asyncio.run_coroutine_threadsafe(pc.addIceCandidate(candidate), asyncio_loop)


def parse_candidate(candidate_str):
    # Define regex pattern for parsing candidate string
    pattern = (
        r"candidate:(?P<foundation>\d+) "
        r"(?P<component>\d) "
        r"(?P<protocol>\w+) "
        r"(?P<priority>\d+) "
        r"(?P<ip>[\d\.]+) "
        r"(?P<port>\d+) "
        r"typ (?P<type>\w+)"
    )

    # Match the pattern
    match = re.match(pattern, candidate_str)
    if not match:
        raise ValueError("Invalid ICE candidate string")

    # Extract the values
    groups = match.groupdict()
    foundation = groups['foundation']
    component = int(groups['component'])
    protocol = groups['protocol']
    priority = int(groups['priority'])
    ip = groups['ip']
    port = int(groups['port'])
    type = groups['type']

    # Optional fields
    relatedAddress = None
    relatedPort = None
    sdpMid = None
    sdpMLineIndex = None
    tcpType = None

    # Create RTCIceCandidate instance
    candidate = RTCIceCandidate(
        foundation=foundation,
        component=component,
        protocol=protocol,
        priority=priority,
        ip=ip,
        port=port,
        type=type,
        relatedAddress=relatedAddress,
        relatedPort=relatedPort,
        sdpMid=sdpMid,
        sdpMLineIndex=sdpMLineIndex,
        tcpType=tcpType
    )

    return candidate

@sio.on("SdpInfo")
def on_sdp_info(data):
    asyncio.run_coroutine_threadsafe(handle_sdp_info(data), asyncio_loop)


async def handle_sdp_info(data):
    # print("Running handle_sdp_info function with data:", data)
    description = RTCSessionDescription(
        sdp=data["description"],
        type=data["type"]
    )
    await pc.setRemoteDescription(description)

    print("Remote description set")

    if description.type == "offer":
        print("Creating answer")
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        response_data = {
            "type": pc.localDescription.type,
            "description": pc.localDescription.sdp,
            "source": "接收方",
            "destination": "提供方"
        }
        # print("Sending response data:", response_data)
        sio.emit("SdpInfo", response_data)


@pc.on("icecandidate")
def on_icecandidate(candidate):
    if candidate:
        print("Sending IceCandidate:", candidate)
        sio.emit("IceInfo", {
            "id": candidate.sdpMid,
            "label": candidate.sdpMLineIndex,
            "candidate": candidate.candidate,
            "source": "接收方",
            "destination": "提供方",
        })
    else:
        print("No ICE candidate available.")


@pc.on("track")
def on_track(track):
    # print(f"Track {track.kind} received aaaaaaaaaaaaaaaa")
    if track.kind == "video":
        # print("Starting display_video coroutine")
        asyncio.run_coroutine_threadsafe(display_video(track), asyncio_loop)


async def display_video(track):
    while True:
        # print("Entered display_video method")
        try:
            # print("Waiting to receive frame")
            # frame_recv_start = time.time()
            frame = await track.recv()
            # frame_recv_end = time.time()
            # print("Frame received")
            # ndarray_start = time.time()
            img = frame.to_ndarray(format="bgr24")
            # print("Converted frame to ndarray")
            # ndarray_end = time.time()
            # print("img: ", img)
            # show_start = time.time()
            cv2.imshow("frame", img)
            cv2.waitKey(1)
            # print("Displayed frame")
            # show_end = time.time()
            #
            # end_time = time.time()

            # print(f"Total time: {end_time - frame_recv_start:.6f} seconds")
            # print(f"Time for track.recv(): {frame_recv_end - frame_recv_start:.6f} seconds")
            # print(f"Time for frame.to_ndarray: {ndarray_end - ndarray_start:.6f} seconds")
            # print(f"Time for show(img): {show_end - show_start:.6f} seconds")
        except Exception as e:
            print(f"Error in display_video: {e}")
            break


# def show(frame):



def connect_to_signaling_server():
    try:
        sio.connect(SIGNALING_SERVER)
    except socketio.exceptions.ConnectionError as e:
        print("Connection Error:", e)
        attempt_reconnect()


def attempt_reconnect():
    time.sleep(5)
    if not sio.connected:
        connect_to_signaling_server()
    else:
        print("Already connected, no need to reconnect")


def main():
    def start_loop(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    asyncio_thread = threading.Thread(target=start_loop, args=(asyncio_loop,))
    asyncio_thread.start()

    connect_to_signaling_server()

    while True:
        asyncio.run_coroutine_threadsafe(asyncio.sleep(100), asyncio_loop).result()


if __name__ == "__main__":
    main()
