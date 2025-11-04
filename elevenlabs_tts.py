import asyncio
import logging
import os
import uuid
import io
from typing import AsyncIterator
from livekit import rtc, agents
from livekit.agents.tts import TTS, TTSCapabilities, ChunkedStream, SynthesizedAudio
from livekit.agents import APIConnectOptions
from elevenlabs import ElevenLabs, VoiceSettings
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class ElevenLabsTTS(TTS):
    def __init__(
        self,
        *,
        api_key: str = None,
        voice_id: str = "pNInz6obpgDQGcFmaJgB",  # Adam voice by default
        model: str = "eleven_turbo_v2_5",
        stability: float = 0.5,
        similarity_boost: float = 0.8,
        style: float = 0.0,
        use_speaker_boost: bool = True,
        sample_rate: int = 24000,
    ):
        super().__init__(
            capabilities=TTSCapabilities(
                streaming=False,  # ElevenLabs streaming requires websockets
            ),
            sample_rate=sample_rate,
            num_channels=1,
        )
        
        self._api_key = api_key or os.getenv("ELEVENLABS_API")
        self._voice_id = voice_id
        self._model = model
        self._voice_settings = VoiceSettings(
            stability=stability,
            similarity_boost=similarity_boost,
            style=style,
            use_speaker_boost=use_speaker_boost,
        )
        
        if not self._api_key:
            raise ValueError("ElevenLabs API key is required")
        
        self._client = ElevenLabs(api_key=self._api_key)

    async def aclose(self):
        pass  # ElevenLabs client doesn't need explicit closing

    def synthesize(
        self, 
        text: str, 
        *, 
        conn_options: APIConnectOptions = APIConnectOptions()
    ) -> ChunkedStream:
        return ElevenLabsChunkedStream(
            tts=self,
            input_text=text,
            conn_options=conn_options,
            client=self._client,
            voice_id=self._voice_id,
            model=self._model,
            voice_settings=self._voice_settings,
        )

class ElevenLabsChunkedStream(ChunkedStream):
    def __init__(
        self,
        *,
        tts: ElevenLabsTTS,
        input_text: str,
        conn_options: APIConnectOptions,
        client: ElevenLabs,
        voice_id: str,
        model: str,
        voice_settings: VoiceSettings,
    ):
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._client = client
        self._voice_id = voice_id
        self._model = model
        self._voice_settings = voice_settings
        self._request_id = str(uuid.uuid4())
        self._audio_frame = None
        self._done = False

    async def _run(self) -> None:
        try:
            logger.info(f"Synthesizing with ElevenLabs: '{self._input_text[:50]}...'")
            
            # Generate audio with ElevenLabs in proper PCM format
            def generate_audio():
                return self._client.text_to_speech.convert(
                    voice_id=self._voice_id,
                    text=self._input_text,
                    model_id=self._model,
                    voice_settings=self._voice_settings,
                    output_format="pcm_24000"  # Request PCM format at 24kHz
                )
            
            # Generate audio in thread and collect all chunks
            audio_generator = await asyncio.to_thread(generate_audio)
            
            # Collect all audio chunks from the iterator
            audio_data = b""
            try:
                for chunk in audio_generator:
                    if chunk:
                        audio_data += chunk
                
                logger.info(f"Collected {len(audio_data)} bytes from ElevenLabs")
                
                if len(audio_data) > 0:
                    # PCM data: 16-bit samples, 1 channel, 24kHz
                    samples_per_channel = len(audio_data) // 2  # 16-bit = 2 bytes per sample
                    
                    self._audio_frame = rtc.AudioFrame(
                        data=audio_data,
                        sample_rate=24000,
                        num_channels=1,
                        samples_per_channel=samples_per_channel,
                    )
                    
                    logger.info(f"Created AudioFrame: {samples_per_channel} samples, {len(audio_data)} bytes")
                else:
                    logger.error("Empty audio data from ElevenLabs")
                    self._audio_frame = None
                    
            except Exception as e:
                logger.error(f"Error collecting audio chunks: {e}")
                self._audio_frame = None
            
            self._done = True
            
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self._audio_frame = None
            self._done = True
            raise

    def __aiter__(self) -> AsyncIterator[SynthesizedAudio]:
        return self

    async def __anext__(self) -> SynthesizedAudio:
        # Run synthesis if not done yet
        if not self._done:
            await self._run()
        
        # Return audio frame if we have one
        if self._audio_frame is not None:
            audio = SynthesizedAudio(
                frame=self._audio_frame,
                request_id=self._request_id,
                is_final=True,
                segment_id="",
                delta_text=self._input_text,
            )
            self._audio_frame = None  # Only return once
            logger.info(f"Returning SynthesizedAudio with {len(self._input_text)} chars")
            return audio
        
        # If we're done but have no audio, that's an error
        if self._done and self._audio_frame is None:
            logger.error("ElevenLabs synthesis completed but no audio frame was created")
            
        raise StopAsyncIteration