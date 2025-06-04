#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause

import os
import time
import threading
import warnings

# Disable NNPACK at the environment level, so torch never tries to initialize it:
os.environ["TORCH_NNPACK"] = "0"

# Suppress NNPACK warnings from the C++ backend:
os.environ["GLOG_minloglevel"] = "2"         # hide INFO(0) and WARNING(1), only show ERROR(2)+
os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"  # ensure Torch’s C++ logs are at ERROR only

# Now import torch and force‐disable any NNPACK backend that slipped through
import torch
try:
    torch.backends.nnpack.enabled = False
except Exception:
    pass

# Silence any Python‐level warnings that mention “NNPACK”
warnings.filterwarnings(
    "ignore",
    message=".*NNPACK.*"
)

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup

from holomat_interface.action import JarvisCommand
from std_msgs.msg import String

from openai import OpenAI
from pygame import mixer

from RealtimeSTT import AudioToTextRecorder

# Fill these in with your actual keys/IDs
OPENAI_API_KEY = 
ASSISTANT_ID   = 
THREAD_ID      = 

class VoiceCommandNode(Node):
    def __init__(self):
        super().__init__('voice_command_node')
        self.get_logger().info("VoiceCommandNode (server+client) started")

        # ─ Setup OpenAI client
        self.openai = OpenAI(api_key=OPENAI_API_KEY)
        mixer.init()

        self._action_server = ActionServer(
            node=self,
            action_type=JarvisCommand,
            action_name='jarvis_command',
            execute_callback=self._on_action_execute
        )

        # We’ll use this client internally to send goals to OURSELF when STT hits “Jarvis”.
        self._callback_group = ReentrantCallbackGroup()
        self._action_client = ActionClient(
            self,
            JarvisCommand,
            'jarvis_command',
            callback_group=self._callback_group
        )

        # Publisher for any “#COMMAND” portion in the AI response
        self._command_pub = self.create_publisher(String, 'jarvis_command_output', 10)

        # Subscription for direct text‐mode queries (bypass mic)
        self._text_query_sub = self.create_subscription(
            String,
            'jarvis_text_query',
            self._on_text_query,
            10
        )

        # STT loop: hot‐word “Jarvis” listening
        self.hot_words = ["jarvis"]
        self.skip_hot_word_check = False
        self.recorder = AudioToTextRecorder(
            spinner=False,
            model="medium.en",
            language="en",
            device="default",
            sample_rate=16000,
            post_speech_silence_duration=0.5,
            silero_sensitivity=0.25
        )
        self._stop_event = threading.Event()
        self._stt_thread = threading.Thread(target=self._stt_loop, daemon=True)
        self._stt_thread.start()

    def _on_action_execute(self, goal_handle):
        """
        Called when a JarvisCommand goal arrives. 
        We forward the 'query' to OpenAI (using ASSISTANT_ID/THREAD_ID), 
        stream back partial responses as feedback, and finally set the result.
        """
        self.get_logger().info(f"[ActionServer] Received goal: “{goal_handle.request.query}”")

        # 1) Add the user message into the thread
        self.openai.beta.threads.messages.create(
            thread_id=THREAD_ID,
            role="user",
            content=goal_handle.request.query
        )

        # 2) Start a run in that thread
        run = self.openai.beta.threads.runs.create(
            thread_id=THREAD_ID,
            assistant_id=ASSISTANT_ID
        )

        # 3) Poll until completed (you could also stream for partial in a loop)
        while True:
            run_status = self.openai.beta.threads.runs.retrieve(
                thread_id=THREAD_ID,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break
            if run_status.status == 'failed':
                goal_handle.abort()  # abort the action
                return JarvisCommand.Result()
            time.sleep(0.5)

        # Step‑4: List all messages in that thread, pick the LAST one (assistant’s reply)
        try:
            messages = self.openai.beta.threads.messages.list(thread_id=THREAD_ID)
            total = len(messages.data)
            if total == 0:
                raise RuntimeError("No messages in thread!")
            # The very last element is the assistant’s reply
            assistant_msg = messages.data[0].content[0].text.value
            self.get_logger().debug(f"[ActionServer] Retrieved {total} messages, replying with index {total-1}")
        except Exception as e:
            self.get_logger().error(f"[ActionServer] Failed to fetch messages: {e}")
            goal_handle.abort()
            return JarvisCommand.Result()

        # Step‑5: Optionally publish a final “partial” feedback (same as full text) and return the Result
        try:
            fb = JarvisCommand.Feedback()
            fb.partial_response = assistant_msg
            goal_handle.publish_feedback(fb)
        except Exception:
            pass

        res = JarvisCommand.Result()
        res.response = assistant_msg
        goal_handle.succeed()
        return res

    def _stt_loop(self):
        """
        Continuously do STT. As soon as we detect “Jarvis <something>”, 
        we strip “Jarvis” and send the rest as a JarvisCommand goal to OUR ActionServer.
        """
        self.get_logger().info("[STT] Thread started. Say 'Jarvis' to invoke.")
        self.recorder.start()

        try:
            while not self._stop_event.is_set():
                text = self.recorder.text().strip()
                if not text:
                    time.sleep(0.1)
                    continue

                self.get_logger().debug(f"[STT] Raw text: “{text}”")

                if any(h in text.lower() for h in self.hot_words):
                    # First detect “jarvis” and strip it
                    if not self.skip_hot_word_check:
                        lowered = text.lower()
                        idx = lowered.find(self.hot_words[0])
                        query = text[idx + len(self.hot_words[0]):].strip()
                    else:
                        query = text

                    if not query:
                        time.sleep(0.1)
                        continue

                    self.get_logger().info(f"[STT] User says: “{query}”")
                    self.recorder.stop()

                    self._send_action_goal(query)

                    # Wait a bit, then resume STT
                    time.sleep(0.5)
                    self.recorder.start()
                else:
                    time.sleep(0.1)
        finally:
            self.recorder.stop()

    def _on_text_query(self, msg: String):
        """
        If somebody publishes a String on /jarvis_text_query, 
        we immediately send that (plus a timestamp) as a JarvisCommand goal.
        """
        raw = msg.data.strip()
        if not raw:
            return
        self.get_logger().info(f"[Text‐Query] “{raw}” → sending goal.")
        self._send_action_goal(raw)

    def _send_action_goal(self, query_text: str):
        """
        Send a JarvisCommand.Goal (with query_text) to /jarvis_command (ourselves).
        We attach a feedback callback and a result callback to do TTS and publish “#COMMAND”.
        """
        self.get_logger().info(f"[Client] Sending goal: “{query_text}”")
        while not self._action_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().warn("[Client] Waiting for own ActionServer…")

        goal = JarvisCommand.Goal()
        goal.query = query_text

        send_future = self._action_client.send_goal_async(
            goal,
            feedback_callback=self._on_feedback
        )
        send_future.add_done_callback(self._on_goal_response)

    def _on_goal_response(self, future):
        """
        Called when our own server acknowledges/rejects the goal.
        """
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("[Client] Goal was rejected!")
            self.skip_hot_word_check = False
            return

        self.get_logger().info("[Client] Goal accepted—awaiting result…")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._on_result)

    def _on_feedback(self, feedback_msg):
        """
        Called as partial text arrives from OpenAI. We simply log it.
        """
        self.get_logger().info(f"[Client] (partial) {feedback_msg.feedback.partial_response!r}")

    def _on_result(self, future):
        """
        Called when the ActionServer is finished. We get the final assistant text,
        do TTS on the “spoken” portion, and publish any “#COMMAND” suffix on /jarvis_command_output.
        """
        result = future.result().result
        response_text = result.response.strip()
        self.get_logger().info(f"[Client] Final Jarvis response: “{response_text}”")

        # Split at “#” if present
        parts = response_text.split('#', maxsplit=1)
        spoken = parts[0].strip()
        command = parts[1].strip() if len(parts) > 1 else ""

        if command:
            self.get_logger().info(f"[Result] Publishing embedded command: “{command}”")
            cmd_msg = String()
            cmd_msg.data = command
            self._command_pub.publish(cmd_msg)

        if spoken:
            tts_file = self._generate_tts(spoken)
            if tts_file:
                # Pause STT so Jarvis’s own audio isn’t picked up
                try:
                    self.recorder.stop()
                except Exception:
                    pass

                # Give the recorder thread a moment to fully shut down
                time.sleep(0.2)

                # Play the TTS audio (blocking until done)
                self._play_audio(tts_file)

                # Re‐initialize STT Recorder to ensure a clean start
                try:
                    # If AudioToTextRecorder has a teardown or join, ensure it’s invoked
                    self.recorder = AudioToTextRecorder(
                        spinner=False,
                        model="medium.en",
                        language="en",
                        device="default",
                        sample_rate=16000,
                        post_speech_silence_duration=0.5,
                        silero_sensitivity=0.25
                    )
                    self.recorder.start()
                except Exception:
                    self.get_logger().warning("[STT] Failed to restart recorder cleanly")


    def _generate_tts(self, text: str) -> str:
        """
        Calls OpenAI’s TTS endpoint to produce a local MP3 file in “jarvis_tts.mp3”.
        """
        try:
            response = self.openai.audio.speech.create(
                model="tts-1",
                voice="echo",
                input=text
            )
            outpath = "jarvis_tts.mp3"
            response.stream_to_file(outpath)
            return outpath
        except Exception as e:
            self.get_logger().error(f"[TTS] Generation failed: {e}")
            return ""

    def _play_audio(self, filepath: str):
        """
        Uses pygame.mixer to play “filepath” → blocks until done → then deletes file.
        """
        if not os.path.exists(filepath):
            self.get_logger().error(f"[TTS] File not found: {filepath}")
            return

        self.get_logger().info(f"[TTS] Playing audio file: {filepath}")

        mixer.music.load(filepath)
        mixer.music.play()
        while mixer.music.get_busy():
            time.sleep(0.1)
        mixer.music.unload()
        try:
            os.remove(filepath)
        except Exception:
            pass

        self.get_logger().info(f"[TTS] Done playing audio file: {filepath}")

    def destroy_node(self):
        # Stop STT thread cleanly on shutdown
        self._stop_event.set()
        self._stt_thread.join(timeout=1.0)
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = VoiceCommandNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
