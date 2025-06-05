"""
Class-based video clip selector using CLIP embeddings and scene detection
"""

import os
import numpy as np
import torch
import open_clip
from PIL import Image
import hashlib
from typing import List, Dict, Any
from moviepy.editor import VideoFileClip
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
from scenedetect.detectors import ContentDetector


class ClipSelector:
    def __init__(self, model_name='ViT-L-14', device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(model_name, pretrained='openai')
        self.tokenizer = open_clip.get_tokenizer(model_name)
        self.model.to(self.device).eval()

        # Runtime-only caches
        self.scene_cache: Dict[str, List[tuple]] = {}
        self.embedding_cache: Dict[str, np.ndarray] = {}
        self.text_embedding_cache: Dict[str, np.ndarray] = {}

    def make_segment_key(self, video_path: str, start: float, end: float) -> str:
        key = f"{video_path}_{start:.2f}_{end:.2f}"
        return hashlib.md5(key.encode()).hexdigest()

    def get_text_embedding(self, text: str) -> np.ndarray:
        if text in self.text_embedding_cache:
            return self.text_embedding_cache[text]

        tokens = self.tokenizer([text]).to(self.device)
        with torch.no_grad():
            text_embed = self.model.encode_text(tokens)
            text_embed /= text_embed.norm(dim=-1, keepdim=True)

        result = text_embed.cpu().numpy().flatten()
        self.text_embedding_cache[text] = result
        return result
    
    def get_image_embedding(self, image_path: str) -> np.ndarray:
        if image_path in self.embedding_cache:
            return self.embedding_cache[image_path]

        image = Image.open(image_path).convert("RGB")
        image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            embedding = self.model.encode_image(image_tensor)
            embedding /= embedding.norm(dim=-1, keepdim=True)

        result = embedding.cpu().numpy().flatten()
        self.embedding_cache[image_path] = result
        return result


    def get_clip_embedding_multi(self, clip: VideoFileClip, num_frames: int = 5) -> np.ndarray:
        # Sample evenly spaced timestamps starting from 0.0 to just before the clip ends
        if clip.duration <= 0:
            raise ValueError("Clip duration must be positive.")
        
        times = np.linspace(0.0, max(0.0, clip.duration - 0.01), num_frames)
        embeddings = []

        for t in times:
            frame = clip.get_frame(t)
            image = Image.fromarray(frame.astype(np.uint8))
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                embedding = self.model.encode_image(image_tensor)
                embedding /= embedding.norm(dim=-1, keepdim=True)
                embeddings.append(embedding.cpu().numpy())

        embeddings = np.vstack(embeddings)
        avg_embedding = embeddings.mean(axis=0)
        avg_embedding /= np.linalg.norm(avg_embedding)
        return avg_embedding


    def split_video_by_scene(self, path: str, threshold: float = 40.0) -> List[tuple]:
        if path in self.scene_cache:
            return self.scene_cache[path]

        video = open_video(path)
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=threshold))
        scene_manager.detect_scenes(video)

        scene_list = scene_manager.get_scene_list()
        scenes = [(start.get_seconds(), end.get_seconds()) for start, end in scene_list]

        self.scene_cache[path] = scenes
        return scenes

    def get_ranked_clips(
        self,
        video_paths: List[str],
        embedding_prompt: str,
        max_segment_duration: int = 5,
        min_segment_duration: int = 1,
        reference_image_path: str = None,
        text_weight: float = 0.5  # Range [0, 1]
    ) -> List[Dict[str, Any]]:

        text_embedding = self.get_text_embedding(embedding_prompt)
        reference_image_embedding = None
        if reference_image_path:
            reference_image_embedding = self.get_image_embedding(reference_image_path)

        segments_scores = []

        for video_path in video_paths:
            print(f'Analyzing video: {os.path.basename(video_path)}')
            try:
                clip = VideoFileClip(video_path)
                scenes = self.split_video_by_scene(video_path)

                final_segments = []
                for start, end in scenes:
                    duration = end - start
                    if duration > max_segment_duration:
                        for s in range(0, int(duration), max_segment_duration):
                            seg_start = start + s
                            seg_end = min(seg_start + max_segment_duration, end)
                            if seg_end - seg_start >= min_segment_duration:
                                final_segments.append((seg_start, seg_end))
                    elif duration >= min_segment_duration:
                        final_segments.append((start, end))

                for i, (seg_start, seg_end) in enumerate(final_segments):
                    seg_key = self.make_segment_key(video_path, seg_start, seg_end)

                    if seg_key in self.embedding_cache:
                        embedding = self.embedding_cache[seg_key]
                    else:
                        segment = clip.subclip(seg_start, seg_end)
                        embedding = self.get_clip_embedding_multi(segment, num_frames=4)
                        self.embedding_cache[seg_key] = embedding
                        segment.close()

                    text_similarity = float(np.dot(embedding, text_embedding))
                    if reference_image_embedding is not None:
                        image_similarity = float(np.dot(embedding, reference_image_embedding))
                        similarity = (text_weight * text_similarity) + ((1 - text_weight) * image_similarity)
                    else:
                        similarity = text_similarity

                    segments_scores.append({
                        "start": seg_start,
                        "end": seg_end,
                        "similarity": similarity,
                        "duration": seg_end - seg_start,
                        "source": video_path
                    })

                clip.close()

            except Exception as e:
                print(f"Error processing video {video_path}: {e}")

        segments_scores.sort(key=lambda x: x['similarity'], reverse=True)
        return segments_scores