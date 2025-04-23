import streamlit as st

def display_model_info(model_name):
    """
    Display information about the selected Gemini model
    
    Args:
        model_name (str): The name of the model
    """
    st.subheader("Model Information")
    
    model_info = {
        "gemini-1.5-pro-latest": {
            "Description": "The most capable model for complex tasks requiring reasoning and understanding.",
            "Best for": "Complex reasoning, detailed conversations, creative tasks",
            "Context window": "Up to 1 million tokens (~700,000 words)",
            "Speed": "Standard processing time"
        },
        "gemini-1.5-flash": {
            "Description": "A faster, more lightweight model for simpler tasks.",
            "Best for": "Quick responses, simpler queries, lower cost processing",
            "Context window": "Up to 1 million tokens (~700,000 words)",
            "Speed": "Faster than Pro models"
        },
        "gemini-pro-vision": {
            "Description": "Model capable of understanding both text and images.",
            "Best for": "Image-based queries, visual analysis, multimodal tasks",
            "Context window": "Standard",
            "Speed": "Slower due to image processing"
        },
        "gemini-1.0-pro-vision-latest": {
            "Description": "Earlier version of vision model for image and text understanding.",
            "Best for": "Basic image analysis and text generation",
            "Context window": "Standard",
            "Speed": "Standard for vision models"
        }
    }
    
    if model_name in model_info:
        info = model_info[model_name]
        for key, value in info.items():
            st.markdown(f"**{key}:** {value}")
    else:
        st.markdown("No detailed information available for this model.")
    
    st.markdown("---")
    
    st.markdown("""
    **Note:** All models are accessed through the v1beta endpoint.
    Using this endpoint requires a Gemini API key from Google AI Studio.
    """)
