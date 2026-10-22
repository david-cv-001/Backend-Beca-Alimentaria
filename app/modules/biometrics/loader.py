import asyncio


async def preload_models() -> None:
    def _load() -> None:
        try:
            from deepface import DeepFace

            # Warm up models if available
            _ = DeepFace.build_model("Facenet512")
        except Exception:
            return

    await asyncio.to_thread(_load)
