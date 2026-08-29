from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ClientError


# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------

# Load environment variables from the .env file.
load_dotenv()

# Create the Gemini API client.
client = genai.Client()


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI()


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------

class Review(BaseModel):
    """
    Customer review received from the Streamlit application.
    """

    text: str


# ---------------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------------

class Analysis(BaseModel):
    """
    Structured analysis returned by Gemini.
    """

    label: str
    # "positive", "negative", or "neutral"

    score: int
    # 1 (very bad) to 5 (very good)

    theme: str
    # One lowercase word describing the main topic of the review.

    reason: str
    # Concise explanation for the classification and score.

    suggestion: str
    # Practical suggestion for negative reviews.
    # Empty for positive or neutral reviews.


# ---------------------------------------------------------------------------
# Analyze customer review
# ---------------------------------------------------------------------------

@app.post("/analyze", response_model=Analysis)
def analyze(review: Review):
    """
    Analyze a customer review using Gemini and return
    structured analysis results.
    """

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",

            contents=(
                "Analyze this customer review.\n\n"

                "The label must be exactly one of "
                "'positive', 'negative', or 'neutral'.\n"

                "The score must be an integer from 1 (very bad) "
                "to 5 (very good).\n"

                "The theme must be ONE lowercase word representing "
                "the main topic of the review. "
                "Examples: delivery, taste, price, service, quality.\n"

                "The reason must be a concise one-sentence explanation "
                "for the selected label, score, and theme.\n"

                "The suggestion must provide one concise and practical "
                "way the business could address the customer's problem "
                "when the review is negative. "
                "For positive or neutral reviews, return an empty string.\n\n"

                f"Review: {review.text}"
            ),

            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Analysis,
            ),
        )

        return response.parsed

    # -----------------------------------------------------------------------
    # Gemini quota / rate-limit errors
    # -----------------------------------------------------------------------

    except ClientError as error:

        # Gemini uses HTTP 429 when the request or quota limit
        # has been exceeded.
        if error.code == 429:

            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini API quota or rate limit exceeded. "
                    "Please try again later."
                ),
            )

        # Handle other Gemini client errors.
        raise HTTPException(
            status_code=502,
            detail=(
                "The Gemini API could not process the request."
            ),
        )

    # -----------------------------------------------------------------------
    # Unexpected backend errors
    # -----------------------------------------------------------------------

    except Exception:

        # Do not expose internal exception details to the client.
        raise HTTPException(
            status_code=500,
            detail=(
                "An unexpected error occurred while "
                "analyzing the review."
            ),
        )