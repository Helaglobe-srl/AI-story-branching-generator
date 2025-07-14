import os
import json
from urllib.parse import urlparse
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_community.document_transformers import Html2TextTransformer
from utils.logger import get_logger

logger = get_logger("utils")

def setup_directories(base_dir):
    """Set up necessary directories
    
    Args:
        base_dir (str): The base directory for the application
        
    Returns:
        tuple: A tuple containing the paths to the raw text, summary text, and JSON output directories
    """
    RAW_TEXT_DIR = os.path.join(base_dir, "raw_text")
    SUMMARY_TEXT_DIR = os.path.join(base_dir, "summarized_text")
    JSON_OUTPUT_DIR = os.path.join(base_dir, "json_story_branches")
    
    for directory in [RAW_TEXT_DIR, SUMMARY_TEXT_DIR, JSON_OUTPUT_DIR]:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"Created directory: {directory}")
        
    logger.info("Application directories setup complete")
    return RAW_TEXT_DIR, SUMMARY_TEXT_DIR, JSON_OUTPUT_DIR

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF
    
    Args:
        pdf_path (str): The path of the PDF file to extract text from

    Returns:
        str: The text extracted from the PDF
    """
    try:
        logger.info(f"Extracting text from PDF: {pdf_path}")
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        text = "\n".join([page.page_content for page in pages])
        logger.info(f"Successfully extracted {len(pages)} pages from PDF")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return ""

def save_text_to_file(text: str, file_path: str) -> None:
    """Save text to file
    
    Args:
        text (str): The text to save
        file_path (str): The path of the file where to save the text
    """
    try:
        logger.debug(f"Saving text to file: {file_path}")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
        logger.debug(f"Successfully saved {len(text)} characters to file")
    except Exception as e:
        logger.error(f"Error saving text to file: {str(e)}")

def save_json_to_file(data: dict, file_path: str) -> None:
    """Save JSON data to file with UTF-8 encoding
    
    Args:
        data (dict): The JSON data to save
        file_path (str): The path of the file where to save the JSON
    """
    try:
        logger.debug(f"Saving JSON to file: {file_path}")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.debug(f"Successfully saved JSON data to file")
    except Exception as e:
        logger.error(f"Error saving JSON to file: {str(e)}")

def read_json_from_file(file_path: str) -> dict:
    """Read JSON data from file with UTF-8 encoding
    
    Args:
        file_path (str): The path of the file to read JSON from
        
    Returns:
        dict: The JSON data read from the file
    """
    try:
        logger.debug(f"Reading JSON from file: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"Successfully read JSON data from file")
        return data
    except Exception as e:
        logger.error(f"Error reading JSON from file: {str(e)}")
        return {}

def extract_text_from_url(url: str) -> str:
    """Extract text from URL
    
    Args:
        url (str): The URL to extract text from

    Returns:
        str: The text extracted from the URL
    """
    try:
        logger.info(f"Extracting text from URL: {url}")
        loader = WebBaseLoader(url)
        docs = loader.load()
        
        # html to text
        logger.debug("Converting HTML to text")
        html2text = Html2TextTransformer()
        docs_transformed = html2text.transform_documents(docs)
        
        # combine pages into a single text
        text = "\n".join([doc.page_content for doc in docs_transformed])
        logger.info(f"Successfully extracted {len(text)} characters from URL")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from URL {url}: {str(e)}")
        return ""

def get_filename_from_url(url: str) -> str:
    """Extract filename from URL
    
    Args:
        url (str): The URL to extract filename from

    Returns:
        str: The filename extracted from the URL
    """
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path) or parsed.netloc
    # remove file extension
    filename = os.path.splitext(filename)[0]
    logger.debug(f"Generated filename '{filename}' from URL: {url}")
    return filename 