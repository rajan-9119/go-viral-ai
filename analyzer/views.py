import json
import os
import re
from groq import Groq
from django.shortcuts import render, redirect
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def home(request):
    score = None
    feedback = []
    suggestions = []
    hashtags = []
    caption = ""
    breakdown = {}
    improved_caption = ""
    competitor_tip = ""

    # Session data
    data = request.session.pop('result', None)
    if data:
        score = data['score']
        feedback = data['feedback']
        suggestions = data['suggestions']
        hashtags = data['hashtags']
        caption = data['caption']
        breakdown = data['breakdown']
        improved_caption = data.get('improved_caption', "")
        competitor_tip = data.get('competitor_tip', "")

    if request.method == "POST":
        caption = request.POST.get('caption') or ""
        file = request.FILES.get('file')

        file_type = None
        if file:
            if file.content_type.startswith('image'):
                file_type = "image"
            elif file.content_type.startswith('video'):
                file_type = "video"

        if caption or file:
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a viral content expert."},
                        {
                            "role": "user",
                            "content": f"""
Analyze this content like a viral expert.

Return ONLY JSON:

{{
  "hook": "analysis",
  "emotion": "low/medium/high",
  "cta": "present or missing",
  "caption_improvement": "better caption",
  "competitor_tip": "what similar viral content does",
  "suggestions": ["point1", "point2"],
  "hashtags": ["tag1", "tag2"]
}}

Caption:
"{caption}"

Content Type:
{"Video" if file_type=="video" else "Image" if file_type=="image" else "Text"}
"""
                        }
                    ],
                    temperature=0.7,
                    max_tokens=300
                )

                ai_output = response.choices[0].message.content.strip()

                # 🔥 CLEAN JSON
                ai_output = re.sub(r"```json|```", "", ai_output).strip()

                ai_data = json.loads(ai_output)

                # 🔥 SMART SCORING
                hook_score = 20 if "strong" in ai_data.get('hook', '').lower() else 10
                emotion_score = 30 if "high" in ai_data.get('emotion', '').lower() else 15
                cta_score = 20 if "present" in ai_data.get('cta', '').lower() else 5

                score = hook_score + emotion_score + cta_score

                # 🎯 FEEDBACK
                feedback = [
                    "🤖 AI Analysis:",
                    f"Hook: {ai_data.get('hook')}",
                    f"Emotion: {ai_data.get('emotion')}",
                    f"CTA: {ai_data.get('cta')}"
                ]

                # 🔥 IMAGE / VIDEO DETECTION FIX
                if file_type == "image":
                    feedback.append("🖼️ Image detected")
                elif file_type == "video":
                    feedback.append("🎥 Video detected")

                # 💡 EXTRA OUTPUT
                suggestions = ai_data.get("suggestions", [])
                hashtags = ai_data.get("hashtags", [])
                improved_caption = ai_data.get("caption_improvement", "")
                competitor_tip = ai_data.get("competitor_tip", "")

                # 📊 BREAKDOWN
                breakdown = {
                    "hook": hook_score,
                    "emotion": emotion_score,
                    "cta": cta_score
                }

            except Exception as e:
                feedback = ["❌ AI Error", str(e)]
                score = 50

        else:
            feedback = ["⚠️ Add caption or file"]
            score = 0

        # safety clamp
        score = max(0, min(score, 100))

        request.session['result'] = {
            'score': score,
            'feedback': feedback,
            'suggestions': suggestions,
            'hashtags': hashtags,
            'caption': caption,
            'breakdown': breakdown,
            'improved_caption': improved_caption,
            'competitor_tip': competitor_tip
        }

        return redirect('home')

    return render(request, 'index.html', {
        'score': score,
        'feedback': feedback,
        'suggestions': suggestions,
        'hashtags': hashtags,
        'caption': caption,
        'breakdown': breakdown,
        'improved_caption': improved_caption,
        'competitor_tip': competitor_tip
    })