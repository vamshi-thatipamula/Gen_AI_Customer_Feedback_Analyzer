from collections import Counter

import requests
import streamlit as st

from database import init_db, save_results, load_history, DB_FILE


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# FastAPI endpoint responsible for analyzing customer reviews.
API_URL = "http://127.0.0.1:8000/analyze"

# Text file containing sample customer reviews provided for the project.
SAMPLE_REVIEWS_FILE = "sample_reviews.txt"

# Create the database table when the Streamlit application starts.
init_db()


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Customer Feedback Analyzer",
    page_icon="📝",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Custom styling
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
        .main-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .subtitle {
            font-size: 1.05rem;
            color: #666;
            margin-bottom: 1.5rem;
        }

        .section-title {
            font-size: 1.35rem;
            font-weight: 600;
            margin-top: 1rem;
            margin-bottom: 0.75rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Application header
# ---------------------------------------------------------------------------

st.markdown(
    '<div class="main-title">📝 Customer Feedback Analyzer</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
        Analyze customer reviews using AI-powered sentiment, rating,
        theme detection, and business recommendations.
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:

    st.header("About")

    st.write(
        """
        This application analyzes customer feedback using a FastAPI backend
        connected to Google's Gemini API.
        """
    )

    st.divider()

    st.subheader("How to use")

    st.write(
        """
        1. Enter one customer review per line.
        2. Optionally load the sample reviews.
        3. Click **Analyze Reviews**.
        4. Review the sentiment, score, theme, and AI explanation.
        5. Review suggestions for negative feedback.
        6. Save the results to the database if required.
        """
    )


# ---------------------------------------------------------------------------
# Review input
# ---------------------------------------------------------------------------

st.markdown(
    '<div class="section-title">Enter customer reviews</div>',
    unsafe_allow_html=True,
)


# Load sample reviews from the text file.
if st.button(
    "📄 Load Sample Reviews",
    width="content",
):

    try:

        with open(
            SAMPLE_REVIEWS_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            st.session_state.reviews_text = file.read()

        st.success("Sample reviews loaded successfully.")

    except FileNotFoundError:

        st.error(
            f"Could not find '{SAMPLE_REVIEWS_FILE}'. "
            "Make sure the file is in the project root directory."
        )


# Store the text area content in session state so that
# loaded sample reviews remain visible after reruns.
if "reviews_text" not in st.session_state:
    st.session_state.reviews_text = ""


reviews_text = st.text_area(
    "Reviews",
    value=st.session_state.reviews_text,
    placeholder=(
        "The delivery was very fast and the food was excellent.\n"
        "The service was slow and the food arrived cold."
    ),
    height=220,
    label_visibility="collapsed",
)


# Keep session state synchronized with the text area.
st.session_state.reviews_text = reviews_text


# ---------------------------------------------------------------------------
# Analyze reviews
# ---------------------------------------------------------------------------

if st.button(
    "🔍 Analyze Reviews",
    type="primary",
    width="stretch",
):

    # Convert the text area into individual reviews
    # and ignore blank lines.
    reviews = [
        line.strip()
        for line in reviews_text.splitlines()
        if line.strip()
    ]

    if not reviews:

        st.warning(
            "Please enter at least one customer review."
        )

    else:

        results = []

        # Display progress when multiple reviews are being analyzed.
        progress_bar = st.progress(0)
        status_text = st.empty()

        for index, review in enumerate(reviews):

            status_text.write(
                f"Analyzing review {index + 1} of {len(reviews)}..."
            )

            try:

                # Send the review to the FastAPI backend.
                response = requests.post(
                    API_URL,
                    json={"text": review},
                    timeout=60,
                )

                # Raise an exception if FastAPI returns an HTTP error.
                response.raise_for_status()

                # Convert the JSON response into a Python dictionary.
                data = response.json()

                results.append(
                    {
                        "review": review,
                        "label": data["label"],
                        "score": data["score"],
                        "theme": data["theme"],
                        "reason": data["reason"],
                        "suggestion": data["suggestion"],
                    }
                )

            except requests.RequestException as error:

                # Try to read the clean error message returned by FastAPI.
                error_message = "Unable to analyze this review."

                if error.response is not None:
                    try:
                        error_data = error.response.json()
                        error_message = error_data.get(
                            "detail",
                            error_message,
                        )
                    except ValueError:
                        # Keep the default message if the response
                        # is not valid JSON.
                        pass

                # Display a user-friendly error message.
                st.error(
                    f"Review {index + 1}: {error_message}"
                )

                results.append(
                    {
                        "review": review,
                        "label": "error",
                        "score": 0,
                        "theme": "error",
                        "reason": "Analysis failed.",
                        "suggestion": "",
                    }
                )

            except (KeyError, ValueError) as error:

                # Handle unexpected or malformed API responses.
                st.error(
                    f"Invalid API response for review "
                    f"{index + 1}: {error}"
                )

                results.append(
                    {
                        "review": review,
                        "label": "error",
                        "score": 0,
                        "theme": "error",
                        "reason": "Invalid API response.",
                        "suggestion": "",
                    }
                )

            # Update the progress bar after each review.
            progress_bar.progress(
                (index + 1) / len(reviews)
            )

        status_text.success(
            "Analysis completed successfully."
        )

        # Store results in session state so they remain
        # available after Streamlit reruns.
        st.session_state.results = results


# ---------------------------------------------------------------------------
# Display analysis results
# ---------------------------------------------------------------------------

if "results" in st.session_state:

    results = st.session_state.results

    st.markdown(
        '<div class="section-title">Analysis Results</div>',
        unsafe_allow_html=True,
    )


    # -----------------------------------------------------------------------
    # Negative-review filter
    # -----------------------------------------------------------------------

    filter_option = st.selectbox(
        "Filter reviews",
        options=[
            "All reviews",
            "Negative reviews",
        ],
    )

    if filter_option == "Negative reviews":

        filtered_results = [
            result
            for result in results
            if result["label"] == "negative"
        ]

    else:

        filtered_results = results


    # Display the filtered results.
    st.dataframe(
        filtered_results,
        width="stretch",
        hide_index=True,
    )


    # -----------------------------------------------------------------------
    # Summary metrics
    # -----------------------------------------------------------------------

    # Ignore failed reviews when calculating summary statistics.
    valid_results = [
        result
        for result in results
        if result["label"] != "error"
    ]

    scores = [
        result["score"]
        for result in valid_results
    ]

    positive_reviews = [
        result
        for result in valid_results
        if result["label"] == "positive"
    ]

    negative_reviews = [
        result
        for result in valid_results
        if result["label"] == "negative"
    ]

    themes = [
        result["theme"]
        for result in valid_results
        if result["theme"] != "error"
    ]


    st.markdown(
        '<div class="section-title">Summary</div>',
        unsafe_allow_html=True,
    )


    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Reviews analyzed",
        len(valid_results),
    )

    if scores:

        average_score = round(
            sum(scores) / len(scores),
            1,
        )

        col2.metric(
            "Average score",
            f"{average_score} / 5",
        )

        positive_percentage = round(
            len(positive_reviews)
            / len(valid_results)
            * 100
        )

        col3.metric(
            "Positive feedback",
            f"{positive_percentage}%",
        )

    else:

        col2.metric(
            "Average score",
            "N/A",
        )

        col3.metric(
            "Positive feedback",
            "N/A",
        )


    # -----------------------------------------------------------------------
    # Negative feedback overview
    # -----------------------------------------------------------------------

    if negative_reviews:

        st.warning(
            f"⚠️ **{len(negative_reviews)} negative "
            "review(s) require attention.**"
        )


    # -----------------------------------------------------------------------
    # Most common theme
    # -----------------------------------------------------------------------

    if themes:

        # Identify the theme mentioned most frequently.
        top_theme = Counter(themes).most_common(1)[0][0]

        st.info(
            f"💡 **Most discussed theme:** {top_theme}"
        )


        # -------------------------------------------------------------------
        # Theme distribution
        # -------------------------------------------------------------------

        # Count how many reviews belong to each theme.
        theme_counts = Counter(themes)

        st.markdown(
            '<div class="section-title">Theme Distribution</div>',
            unsafe_allow_html=True,
        )

        # Convert Counter to a regular dictionary before
        # passing it to Streamlit's bar chart.
        theme_data = dict(theme_counts)

        # Display the number of reviews for each theme.
        st.bar_chart(theme_data)


    # -----------------------------------------------------------------------
    # AI explanations and suggestions
    # -----------------------------------------------------------------------

    st.markdown(
        '<div class="section-title">AI Insights</div>',
        unsafe_allow_html=True,
    )


    # Display detailed explanations for negative reviews.
    negative_results = [
        result
        for result in valid_results
        if result["label"] == "negative"
    ]

    if negative_results:

        for index, result in enumerate(
            negative_results,
            start=1,
        ):

            with st.expander(
                f"Negative Review {index}: "
                f"{result['theme'].title()}"
            ):

                st.write(
                    f"**Review:** {result['review']}"
                )

                st.write(
                    f"**Reason:** {result['reason']}"
                )

                st.write(
                    f"**Suggested action:** "
                    f"{result['suggestion']}"
                )

    else:

        st.success(
            "No negative reviews were identified."
        )


    # -----------------------------------------------------------------------
    # Save results
    # -----------------------------------------------------------------------

    st.divider()

    if st.button(
        "💾 Save Results to Database",
        width="stretch",
    ):

        save_results(results)

        st.success(
            f"Saved {len(results)} reviews to the database."
        )


# ---------------------------------------------------------------------------
# Saved history
# ---------------------------------------------------------------------------

with st.expander("📚 View Saved History"):

    history = load_history()

    if history:

        st.write(
            f"**Total saved reviews:** {len(history)}"
        )

        history_data = [
            {
                "review": row[0],
                "label": row[1],
                "score": row[2],
                "theme": row[3],
                "reason": row[4],
                "suggestion": row[5],
            }
            for row in history
        ]

        st.dataframe(
            history_data,
            width="stretch",
            hide_index=True,
        )

    else:

        st.info(
            "No reviews have been saved yet. "
            "Analyze some reviews and save the results."
        )