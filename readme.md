# AI-Assisted Content Analysis and Generation Tools

This repository contains a collection of Python scripts and utilities for AI-assisted content analysis, web crawling, image processing, and text generation. These tools are designed to help with various tasks related to social media content creation, influencer analysis, and natural language processing.

## Features

- Web crawling and content extraction
- Image analysis and processing
- Video frame extraction and subtitle generation
- YouTube video downloading and transcript generation
- Text analysis and generation using AI models
- Social media influencer analysis
- SVG card generation for concept visualization

## Main Components

1. **Web Crawling**: 
   - `crawl_script.py`: Asynchronous web crawler
   - `web_snapshot.py`: Takes screenshots of web pages

2. **Image and Video Processing**:
   - `extract_frames.py`: Extracts frames from videos
   - `split_picture.py`: Splits large images into smaller parts
   - `download_youtube_video.py`: Downloads YouTube videos

3. **Text Processing and Analysis**:
   - `compare.py`: Compares different text analyses
   - `generate_srt.py`: Generates subtitle files
   - `translate.py`: Translates text between languages

4. **AI-Assisted Content Generation**:
   - `thinker.py`: Deep concept analysis
   - `knowlege_card.py`: Generates explanatory cards for concepts
   - `word_card.py`: Creates memory cards for vocabulary

5. **Social Media Analysis**:
   - `persona.py`: Analyzes social media influencer personas

## Setup and Usage

1. Clone the repository
2. Install required dependencies (list them or provide a `requirements.txt`)
3. Set up necessary API keys as environment variables
4. Run individual scripts as needed

## Dependencies

- Python 3.x
- Libraries: anthropic, moviepy, PIL, pytesseract, selenium, etc. (provide a complete list)

## Configuration

Some scripts require API keys or specific configurations. Make sure to set up the following:

- ANTHROPIC_API_KEY: For AI-assisted text generation
- CLAUDE_API_KEY: For web crawling and content analysis

## Contributing

Contributions to improve the tools or add new features are welcome. Please follow the standard GitHub pull request process.

## License

[Specify your chosen license here]

## Disclaimer

These tools are for educational and research purposes only. Ensure you comply with the terms of service of any platforms or APIs you interact with using these scripts.