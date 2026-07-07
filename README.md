# Krishi Sahayak - AI Chatbot for Indian Farmers

Krishi Sahayak is a polished, hackathon-ready farming assistant for Indian farmers. It combines bilingual support, multi-model routing, knowledge-based guidance, voice input, chat export, and a professional UI to make agricultural help feel practical and modern.

## Highlights

- 🌾 Farming-themed, polished UI with green, modern visuals
- 🇮🇳 Full Hindi and English support with bilingual technical terms
- 🤖 Visible multi-model routing with model names and confidence scores
- 🧠 Deep RAG-style guidance: Expanded knowledge base for Wheat, Rice, Sugarcane, Potato, Tomato, Onion, Cotton, Pulses, and Mustard.
- 🐛 Pest & Disease Library: Detailed symptoms, causes, chemical dosages, and organic solutions in English and Hindi.
- 📜 Government Schemes: Integrated info on PM-KISAN, PMFBY, KCC, PKVY, and PM-KMY.
- 🎙️ Browser voice input for Hindi and English speech
- 💡 Quick suggestion chips for common farmer questions
- 📝 Local chat history persistence with browser storage
- 📤 Export chat as a text file
- ✨ Beautiful loading states and success feedback
- 📸 Image upload for crop issue review
- 📈 Simple crop price prediction based on current MSP/Market trends
- 🔍 Side-by-side multi-model comparison
- 📣 One-click WhatsApp sharing for farmer groups

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Mesh API key:

```bash
MESH_API_KEY=your_api_key_here
```

3. Run the app:

```bash
python app.py
```

4. Open your browser at: http://localhost:8000

## Project Structure

```text
krishi-sahayak/
├── app.py               # FastAPI backend server
├── knowledge_base.py    # Farming knowledge base and retrieval logic
├── requirements.txt     # Python dependencies
├── static/
│   └── index.html        # Polished frontend UI
└── tests/
    └── test_backend.py  # Backend regression tests
```

## Technologies

- Backend: FastAPI, Python
- Frontend: HTML, Tailwind CSS, Vanilla JavaScript
- AI: Mesh API with routed model support
- Features: RAG-style context retrieval, voice input, local persistence, export

## Submission Notes

This version is designed to impress judges with:

- strong user experience
- practical farming utility
- clear technical implementation
- polished demo flow

## License

# MIT License

# krishi-sahayak

"AI Farming Assistant for Indian Farmers"

43ea039c4f2bd027836be52ae14b1125e9cb0140
