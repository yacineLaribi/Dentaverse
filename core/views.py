from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from .models import XrayAnalysis
import base64, json, re, os
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import io

# Load API key
load_dotenv()
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def index(request):
    return render(request, "index.html")

def analyze(request):
    return render(request, "analyze.html")

@csrf_exempt
def create_analysis(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    file = request.FILES.get("xray")
    if not file:
        return JsonResponse({"error": "No file uploaded"}, status=400)

    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
    if file.content_type not in allowed_types:
        return JsonResponse({"error": "Invalid file type. Please upload JPEG or PNG images."}, status=400)

    # Validate file size (e.g., max 10MB)
    if file.size > 10 * 1024 * 1024:
        return JsonResponse({"error": "File too large. Maximum size is 10MB."}, status=400)

    analysis = XrayAnalysis.objects.create(
        image=file,
        status="pending",
    )
    return JsonResponse({"success": True, "analysisId": analysis.id})

@csrf_exempt
def analyze_xray(request, analysis_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
        
    try:
        analysis = XrayAnalysis.objects.get(id=analysis_id)
    except XrayAnalysis.DoesNotExist:
        return JsonResponse({"error": "Analysis not found"}, status=404)

    if analysis.status == "completed":
        return JsonResponse({"success": True, "results": analysis.ai_results})

    analysis.status = "processing"
    analysis.save()

    prompt = """You are an expert dental radiologist AI assistant. 
    Analyze this dental X-ray image and provide a detailed clinical assessment.
    
    Please examine the image for:
    - Les Bridges / Prothèses
    - Tooth decay/cavities
    - Root canal issues
    - Bone density
    - Periodontal disease
    - Impacted teeth
    - Fractures
    - Obturations
    - Abnormal growths
    
    Return your analysis in the following JSON format:
    {
        "detections": [
            {
                "finding": "description of finding",
                "severity": "low/medium/high",
                "location": "specific tooth or area"
            }
        ],
        "recommendations": [
            "specific recommendation 1",
            "specific recommendation 2"
        ],
        "overallAssessment": "comprehensive summary of findings",
        "urgency": "routine/urgent/emergency"
    }
    
    Provide only valid JSON in your response and make the response in FRENCH."""

    try:
        # Open and process the image
        with open(analysis.image.path, "rb") as f:
            image_data = f.read()
        
        # Convert to PIL Image for processing
        pil_image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Use the correct Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generate content
        response = model.generate_content([prompt, pil_image])
        
        result_text = response.text.strip()
        
        # Try to parse JSON from the response
        try:
            # Look for JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                json_str = json_match.group()
                ai_results = json.loads(json_str)
                
                # Validate the JSON structure
                required_fields = ['detections', 'recommendations', 'overallAssessment', 'urgency']
                if not all(field in ai_results for field in required_fields):
                    raise ValueError("Missing required fields in AI response")
                    
            else:
                # If no valid JSON found, create a structured response
                ai_results = {
                    "detections": [],
                    "recommendations": ["Please consult with a dental professional for proper diagnosis"],
                    "overallAssessment": result_text[:500] + "..." if len(result_text) > 500 else result_text,
                    "urgency": "routine",
                    "raw_response": result_text
                }
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback if JSON parsing fails
            ai_results = {
                "detections": [],
                "recommendations": ["Please consult with a dental professional for proper diagnosis"],
                "overallAssessment": "AI analysis completed, but response format needs review",
                "urgency": "routine",
                "raw_response": result_text,
                "parsing_error": str(e)
            }

        # Save successful results
        analysis.status = "completed"
        analysis.ai_results = ai_results
        analysis.processed_at = now()
        analysis.save()

        return JsonResponse({"success": True, "results": ai_results})

    except Exception as e:
        # Log the error and save failed status
        print(f"Error analyzing X-ray {analysis_id}: {str(e)}")
        analysis.status = "failed"
        analysis.error_message = str(e)
        analysis.save()
        return JsonResponse({"error": f"Analysis failed: {str(e)}"}, status=500)