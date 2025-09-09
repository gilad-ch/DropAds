# DropAds

**DropAds** is an automated pipeline that uses multimodal AI models
combined with scene detection and vector similarity search to generate short style vertical ads for products.  


Vector Role in DropAds
The **vector embeddings** are central:  
- Product description → embedding prompt → **vector representation of “what to show.”**  
- Video frames → CLIP embeddings → **vector representation of “what’s in the footage.”**  
- Matching = **vector similarity search** → ensures every spoken line aligns with the most relevant scene.

---

## Product Understanding
- **Input:** Product image + metadata.  
- **AI Processing:**  
  - `prompt_image(...)` → Uses a vision to language model to generate a **product description** from the uploaded image.  
  - `prompt_llm(...)` → Expands the description into two things:  
    1. **Embedding Prompt** (used for clip selection).  
    2. **Ad Script** (hook → features → call-to-action).  

---

## Clip Ranking with Vectors
- **Input:** Media assets directory (user-provided videos).  
- **Scene Detection:** Each raw video is segmented into smaller clips/shots.  
- **Embedding Representation:**  
  - The **ad embedding prompt** is converted into a **vector embedding**.  
  - Each video scene is converted into **CLIP embeddings** (image vectors).  
- **Vector Search:**  
  - Cosine similarity ranks video scenes against the ad embedding prompt.  
  - **Output:** `ranked_clips`, ordered by semantic relevance to the product + script.  

---

## Video Assembly
- **assemble_final_video(...)** merges:  
  - Ranked clips (trimmed/ordered).  
  - TTS audio narration.  
  - Script text (for captions / overlays).  
  - Optional background music.  

---



