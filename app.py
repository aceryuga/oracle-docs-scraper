from flask import Flask, render_template, request, Response, stream_with_context, send_from_directory
from oracle_scraper import OracleDocumentationScraper
import os
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    """Renders the main page with the input form."""
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """Handles the scraping request, streams progress, and provides a download link."""
    toc_url = request.form.get('toc_url')
    output_file_name = request.form.get('output_file')

    if not toc_url or not output_file_name:
        return Response("Error: Both URL and Filename are required.", status=400)

    if not output_file_name.endswith('.json'):
        output_file_name += '.json'

    # Generate a unique path for the output file to avoid conflicts
    unique_filename = f"{uuid.uuid4()}_{output_file_name}"
    output_path = os.path.join(DOWNLOAD_FOLDER, unique_filename)

    def generate_scrape_stream():
        scraper = OracleDocumentationScraper(toc_url=toc_url)
        # The scraper now saves the file and yields progress
        yield from scraper.scrape_all_pages(output_path)
        # Signal that the download is ready
        yield f"DOWNLOAD_READY:{unique_filename}"

    return Response(stream_with_context(generate_scrape_stream()), content_type='text/plain; charset=utf-8')

@app.route('/download/<filename>')
def download_file(filename):
    """Serves the specified file for download."""
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
