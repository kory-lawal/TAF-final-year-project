# AI Oriki System

The AI Oriki System is a web-based application designed to generate culturally rich Yoruba praise poetry, commonly known as Oríkì, for individuals, families, and communities. The system combines data-driven generation, language translation, and speech synthesis to produce meaningful and expressive oríkì that reflect identity, heritage, and social values. The application is intended to preserve cultural expression in a digital form while making the experience interactive, accessible, and user-friendly.

## Project Structure

```text
ai-oriki-system/
│
├── app/                        # Main application
│   ├── main.py                # Streamlit frontend (UI)
│   ├── config.py              # API keys and configurations
│   ├── services/              # Core logic
│   │   ├── oriki_service.py   # Handles CSV + generation
│   │   ├── translation.py     # Translation logic
│   │   ├── tts.py            # TTS integration
│   │   ├── nla_client.py     # External language/data client
│   │   ├── oriki_glossary.py # Glossary support
│   ├── utils/                 # Helper modules
│   │   ├── loader.py          # Load CSV files
│   │   ├── generator.py       # Combine/generate Oríkì
│   ├── data/                  # Datasets
│   │   ├── yoruba.csv
│   │   ├── igbo.csv
│   │   ├── hausa.csv
│
├── requirements.txt
├── README.md
```

## Installation & Setup

Follow these steps to install and run the project locally (tested on Windows):

- **Prerequisites:** Python 3.10+, Git, and pip. Optional: Streamlit for local UI.
- **Clone repository:**

  git clone <your-repo-url>
  cd <your-repo-dir>

- **Create and activate a virtual environment:**

  python -m venv .venv
  # PowerShell
  .\.venv\Scripts\Activate.ps1
  # CMD
  .\.venv\Scripts\activate

- **Install dependencies:**

  pip install --upgrade pip
  pip install -r requirements.txt

- **Environment variables:**

  Create a `.env` file in the project root containing at minimum:

  YARNGPT_API_KEY=your_api_key_here
  YARNGPT_TTS_URL=https://yarngpt.ai/api/v1/tts

  If you do not have a `YARNGPT_API_KEY`, audio will fall back to `gTTS` if installed: `pip install gTTS`.

- **Run the app (Streamlit):**

  streamlit run app/main.py

- **Run tests:**

  pytest

If you need to change remote settings or push changes, use normal Git commands (`git add`, `git commit`, `git push`).


## CHAPTER FOUR: SYSTEM IMPLEMENTATION AND RESULT

### 4.1 Introduction

This chapter presents the implementation of the AI Oriki System and discusses the results obtained after the system was developed and tested. The aim of the implementation phase was to transform the proposed design into a functional application that could generate Oríkì, provide translations, and deliver an interactive user experience. The implementation process involved combining the user interface, business logic, cultural data sources, and multimedia services into a single system that is easy to use and relevant to the intended users.

The successful development of the system shows that artificial intelligence and cultural computing can be combined to produce meaningful digital content. In this system, the Oríkì generation process is not only based on pre-defined text patterns but is also shaped by cultural categories such as family lineage, honor, bravery, royalty, wisdom, and social identity. This gives the generated output a deeper cultural value and makes the system more than a simple text generator.

### 4.2 Development Environment and Tools

The system was implemented using Python as the primary programming language because of its simplicity, flexibility, and strong support for scientific and web-based applications. The user interface was built using Streamlit, which allows rapid development of interactive web applications without requiring extensive front-end programming knowledge. Python was also suitable for managing data processing, string generation, translation routines, and integration with speech synthesis services.

The system made use of structured datasets stored in CSV files, which contain entries for different names, meanings, oríkì texts, categories, and cultural tags. These datasets were loaded into the application and used as the foundation for the generation engine. In addition, the implementation included support for text transformation, translation, and audio generation so that the system could offer a more complete and engaging experience for users.

### 4.3 System Architecture

The system architecture was designed around a modular structure to make it simple, maintainable, and expandable. The architecture consists of four major layers: the presentation layer, the application logic layer, the data layer, and the external service layer.

The presentation layer is represented by the front-end interface where users enter names, select preferences, and view the generated results. The application layer contains the main modules responsible for processing the user request, generating the Oríkì, applying translation rules, and handling cultural text formatting. The data layer stores the cultural content in CSV files and other structured resources. The external service layer handles additional features such as text-to-speech generation and connection to vocabulary or language support services.

This modular architecture ensures that each part of the system performs a specific role. The user interface remains separate from the core logic, which allows the system to be improved or extended without affecting the entire application. This also makes the system suitable for future enhancements such as voice-based interaction, larger datasets, multilingual support, and cloud deployment.

### 4.4 Implementation of the Main Functional Modules

#### 4.4.1 User Interface Module

The user interface was designed to be simple, interactive, and culturally appealing. Users are able to enter a name, choose a preferred cultural context, and receive an output that includes a generated Oríkì, its translation, and related cultural interpretation. The interface provides a direct way for users to interact with the system without requiring technical knowledge.

The design of the interface is important because the system is not meant to be used only by technical users. It is intended to serve a wide range of people, including students, researchers, cultural enthusiasts, and individuals interested in Yoruba heritage. The interface therefore focuses on clarity, accessibility, and ease of operation.

#### 4.4.2 Oríkì Generation Module

The Oríkì generation module is the core of the system. It takes user input and uses stored cultural records to construct meaningful praise poetry. The module analyzes the input name and matches it with relevant cultural patterns stored in the datasets. It then combines the selected content into a short, expressive, and meaningful composition that reflects the name's association with values such as honor, lineage, bravery, royalty, or wisdom.

This module is very important because the value of the system depends on the quality of the generated text. The generation process is designed to preserve a balance between originality and cultural relevance. Instead of simply producing random lines, the system attempts to create text that sounds meaningful, respectful, and suitable for the cultural context of the name.

#### 4.4.3 Translation and Interpretation Module

Translation is also an essential feature of the system. After the Oríkì is generated, the application provides a meaning or translation of the output so that users who are not fluent in Yoruba can understand the message. This makes the system more inclusive by bridging language barriers while still preserving the cultural depth of the original expression.

The translation module is useful because it allows the system to communicate the meaning of the Oríkì in a form that is easier for contemporary users to understand. In addition to direct translation, the system also provides contextual interpretation, helping users understand the cultural symbols and values embedded in the praise poetry.

#### 4.4.4 Text-to-Speech Module

The text-to-speech component adds a multimedia dimension to the system. Once the Oríkì has been generated, the user can listen to the content in spoken form. This feature improves accessibility for users who may prefer audio over reading and also adds an emotional dimension to the cultural expression.

The inclusion of speech functionality strengthens the system's practical usefulness. It helps create a more immersive experience and demonstrates how technology can enhance the preservation and presentation of oral culture. Through audio output, the system becomes closer to the oral tradition from which Oríkì originally emerged.

#### 4.4.5 Data Handling and Storage Module

The system uses structured datasets to provide the content for generation. These datasets are stored in CSV format and organized according to categories such as name, language, content, description, and tags. This makes it easier to manage and expand the database over time. The data handling module ensures that the application can read, process, and retrieve the appropriate information when a request is made.

The storage approach was chosen because CSV files are easy to maintain and can be updated by adding new entries without changing the programming code. This provides flexibility for future expansion and makes the system more adaptable to larger cultural datasets.

### 4.5 Workflow of the System

The workflow of the system begins when the user enters a name or selects a cultural category. The application then searches the dataset for matching or relevant content. After the relevant content is identified, the generation module constructs the Oríkì text. The translation module converts or interprets the text into a more accessible form, while the speech module produces audio output. The final result is presented to the user through the interface in a well-structured and readable format.

This workflow is simple but effective. It shows how the system receives input, processes it through multiple modules, and presents a final output that is both culturally meaningful and technologically functional. The workflow also demonstrates that the application is built on a clear process rather than a random generation mechanism.

### 4.6 Results Obtained After Development and Testing

After the development and testing of the system, several positive results were obtained. The system successfully produced Oríkì output based on user input and cultural data, showing that the application could function as intended. The generated results demonstrated a clear relationship between the provided name and the cultural meanings associated with identity, heritage, honor, lineage, and social values.

The testing process also showed that the system was able to perform its core functions effectively. It could receive user input, retrieve relevant cultural data, generate meaningful poetic output, display interpretation or translation, and provide audio output where applicable. These results indicate that the system is not only technically functional but also relevant for cultural communication and digital preservation.

Another important result was the system’s ability to present Yoruba cultural content in a modern and interactive format. This made the traditional practice of Oríkì generation more accessible to users who may not be familiar with the oral or textual traditions behind it. The application therefore served as a bridge between indigenous cultural knowledge and digital technology.

The results also revealed that the system has strong educational value. Users can learn about Yoruba naming traditions, cultural symbolism, and the meanings attached to certain names through the generated output. In this way, the system contributes not only to creativity but also to cultural awareness and appreciation.

Although the output was not always perfect, the results showed that the system produced meaningful and useful content. This confirms that the project achieved its main objective of creating a practical and culturally relevant Oríkì generation system.

### 4.7 Testing and Evaluation

Several aspects of the system were tested during the implementation phase. Functional testing was carried out to ensure that the application could receive input, generate output, display translations, and produce audio effectively. Data validation was also performed to confirm that the CSV files were correctly loaded and that the content was available when needed.

The testing process also focused on quality of output. The generated Oríkì was evaluated based on relevance, readability, cultural connection, and general usefulness. The results showed that the system could produce appropriate content for many names and cultural categories. In some cases, improvements may still be needed to refine the wording, strengthen the cultural accuracy, or expand the dataset for more complete coverage.

### 4.8 Challenges Encountered During Implementation

Although the system was successfully implemented, some challenges were encountered during development. One major challenge was ensuring that the generated text remained culturally meaningful while still being understandable to users. Another challenge was managing and organizing large amounts of cultural data so that it could be retrieved efficiently and used consistently.

There were also challenges related to text quality, because automatic generation can sometimes produce output that is repetitive or less expressive than expected. In addition, speech synthesis required careful handling to ensure that the audio output was clear and properly synchronized with the generated content. These issues were addressed through careful module design, structured data management, and continuous testing.

### 4.9 Results and Discussion

The final result of the implementation is a functional and interactive Oríkì generation system that brings together technology and culture. The application is able to generate meaningful praise poetry, provide context, and make cultural expression accessible through digital platforms. This demonstrates the practical value of using artificial intelligence and data-driven systems in preserving and promoting cultural heritage.

The system is especially relevant in the context of digital preservation because it allows cultural content to be shared beyond traditional oral settings. Users can interact with the system from different locations, learn about Yoruba naming traditions, and experience Oríkì in a modern and accessible format. The project therefore contributes to cultural education, preservation, and technological innovation.

### 4.10 Screenshot Placeholder Section

The following section is reserved for visual evidence of the developed system. These screenshots should be inserted to support the discussion in this chapter and to give a clearer presentation of the system interface and output.

- Screenshot 1: Home page of the system showing the input form and user instructions.
  [Insert Screenshot 1 Here]

- Screenshot 2: Interface showing a generated Oríkì result for a selected name.
  [Insert Screenshot 2 Here]

- Screenshot 3: Translation or interpretation output displayed alongside the generated Oríkì.
  [Insert Screenshot 3 Here]

- Screenshot 4: Audio or text-to-speech output section of the system.
  [Insert Screenshot 4 Here]

- Screenshot 5: Example of the system displaying cultural meaning, lineage, or related tags.
  [Insert Screenshot 5 Here]

- Screenshot 6: Additional view showing the system in use with another sample input.
  [Insert Screenshot 6 Here]

### 4.11 Summary of Chapter Four

Chapter Four has presented the implementation of the AI Oriki System and the results obtained from the development process. It has discussed the architecture, major modules, workflow, testing, challenges, and overall outcomes of the system. The chapter shows that the system successfully combines cultural data, language processing, and interactive technology to generate meaningful Oríkì output. The implementation demonstrates that the project is not only technically functional but also culturally valuable and relevant to the preservation of Yoruba heritage.
