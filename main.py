import os
import json
import traceback
import asyncio
import nest_asyncio
import streamlit as st
import time
from dotenv import load_dotenv
from excel.excel_converter import StoryBranchExcelConverter
from ai_agents.story_branch_generator import StoryBranchGenerator
from ai_agents.conversation_enhancer import ConversationEnhancer
from utils.logger import app_logger, get_logger
from utils.utils import (
    setup_directories, 
    extract_text_from_pdf, 
    save_text_to_file, 
    extract_text_from_url, 
    get_filename_from_url,
    save_json_to_file
)

logger = get_logger("main")

load_dotenv()

nest_asyncio.apply()

# directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_TEXT_DIR, SUMMARY_TEXT_DIR, JSON_OUTPUT_DIR = setup_directories(BASE_DIR)

LANGUAGE = "Italian"

def main():
    st.title("Story Branch Maker")
    
    st.write("""
    Instructions:
    1. Upload PDF files or enter a list of URLs about a specific disease
    2. Specify the disease name
    3. Files are analyzed and cleaned
    4. Story branches are generated in JSON format and available in Excel format for download
    """)
    
    st.write("---")
    
    # disease input
    disease = st.text_input(
        "Enter the disease name:",
        help="Enter the name of the disease the story branch will be about"
    )
    
    # create tabs for pdf and url input
    tab1, tab2 = st.tabs(["PDF files", "URLs"])
    
    with tab1:
        uploaded_files = st.file_uploader(
            "Upload PDF files", 
            type="pdf", 
            accept_multiple_files=True,
            help="You can upload multiple PDF files. They will be processed one at a time."
        )
    
    with tab2:
        urls = st.text_area(
            "Enter URLs (one per line)",
            help="Enter multiple URLs, one per line. They will be processed one at a time."
        )
        urls_list = [url.strip() for url in urls.split('\n') if url.strip()]
        
    st.write("---")
    
    # model selection
    model = st.selectbox(
        "Select model:",
        ["gpt-4.1", "gpt-4o-mini", "gpt-4o"],
        index=0  # default gpt-4o-mini
    )
    
    # option for combined excel file
    combine_excel = st.checkbox("Create a single Excel file with all story branches", value=True)
    
    # number of nodes selection
    how_many_nodes = st.number_input(
        "Number of story branch nodes:",
        min_value=1,
        max_value=10,
        value=10,
        help="Choose how many decision nodes to generate in the story branch"
    )
    
    # option for conversation enhancement
    enhance_conversations = st.checkbox("Enhance conversations in story branches", value=True, 
                                       help="Add more detailed conversations to story branches")

    
    st.write("---")
    
    # verify api key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("Please set OPENAI_API_KEY in your .env file")
        return
    
    if st.button("Generate Story Branches"):
        if not disease:
            st.error("Please enter a disease name")
            return
            
        # Create status display area
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Set up the logger to use the status text
        app_logger.set_status_text(status_text)
        
        # create event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        logger.info(f"Starting story branch generation for disease: {disease}")
        logger.info(f"Using model: {model}")
        logger.info(f"Number of nodes: {how_many_nodes}")
        
        excel_converter = StoryBranchExcelConverter(BASE_DIR)
        story_generator = StoryBranchGenerator(model, SUMMARY_TEXT_DIR)
        conversation_enhancer = ConversationEnhancer(model)
        
        # store all story branches for combined export
        all_story_branches = []
        
        try:
            # process pdfs if present
            if uploaded_files:
                total_files = len(uploaded_files)
                logger.info(f"Processing {total_files} PDF files")
                
                for file_index, pdf_file in enumerate(uploaded_files):
                    start_time = time.time()
                    status_text.text(f"Processing PDF {file_index+1} of {total_files}: {pdf_file.name}")
                    progress_bar.progress(file_index / total_files)
                    logger.info(f"Starting processing of PDF {file_index+1}/{total_files}: {pdf_file.name}")
                    
                    # temporary save of uploaded file
                    temp_path = f"temp_{pdf_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(pdf_file.getbuffer())
                    logger.info(f"PDF saved temporarily as {temp_path}")
                    
                    try:
                        # extract text from pdf
                        logger.info(f"Extracting text from PDF")
                        pdf_text = extract_text_from_pdf(temp_path)
                        if not pdf_text:
                            error_msg = f"Impossible to extract text from {pdf_file.name}"
                            logger.error(error_msg)
                            st.error(error_msg)
                            continue
                        logger.info(f"Successfully extracted {len(pdf_text)} characters of text")
                        
                        # save raw text
                        base_filename = pdf_file.name.replace('.pdf', '')
                        raw_text_path = os.path.join(RAW_TEXT_DIR, f"{base_filename}.txt")
                        save_text_to_file(pdf_text, raw_text_path)
                        logger.info(f"Raw text saved to {raw_text_path}")
                        
                        # process text with agents
                        logger.info(f"Starting story branch generation with AI agent")
                        story_branch, base_filename = loop.run_until_complete(
                            story_generator.create_story_branch_from_text(pdf_text, pdf_file.name, disease, language=LANGUAGE, how_many_nodes=how_many_nodes)
                        )
                        logger.info(f"Story branch generation completed")
                        
                        if story_branch:
                            # save initial story branch in json
                            output_path = os.path.join(JSON_OUTPUT_DIR, f"{base_filename}_story_branch.json")
                            save_json_to_file(story_branch.model_dump(), output_path)
                            logger.info(f"Story branch saved to {output_path}")
                            
                            # enhance conversations if requested
                            if enhance_conversations:
                                status_text.text(f"Enhancing conversations for {base_filename}...")
                                logger.info(f"Starting conversation enhancement")
                                enhanced_output_path = os.path.join(JSON_OUTPUT_DIR, f"{base_filename}_enhanced_story_branch.json")
                                story_branch = loop.run_until_complete(
                                    conversation_enhancer.enhance_conversations(story_branch, enhanced_output_path)
                                )
                                logger.info(f"Conversation enhancement completed")
                                logger.info(f"Enhanced story branch saved to {enhanced_output_path}")
                                
                                # use the enhanced story branch for further processing
                                output_path = enhanced_output_path
                            
                            # save story branch for combined export
                            all_story_branches.append((story_branch, base_filename))
                            
                            # notify about text cleaning
                            summary_path = os.path.join(SUMMARY_TEXT_DIR, f'{base_filename}_summary.txt')
                            logger.info(f"Text cleaned and formatted saved in: {summary_path}")
                            st.info(f"Text cleaned and formatted saved in: {summary_path}")
                            
                            if not combine_excel:
                                # convert to excel (individual file)
                                logger.info(f"Converting story branch to Excel")
                                excel_path = excel_converter.story_branch_to_excel(story_branch, base_filename)
                                if excel_path:
                                    logger.info(f"Excel story branch saved in: {excel_path}")
                                    st.info(f"Excel story branch saved in: {excel_path}")
                                    
                                    # download button
                                    excel_buffer = excel_converter.get_excel_download_buffer(story_branch)
                                    st.download_button(
                                        label=f"Download {base_filename} Story Branch (Excel)",
                                        data=excel_buffer,
                                        file_name=f"{base_filename}_story_branch.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                            
                            # display story branch in streamlit
                            st.write(f"### Story Branch for {base_filename}")
                            st.write(f"**Disease:** {story_branch.disease}")
                            
                            for node_index, node in enumerate(story_branch.nodes, 1):
                                st.write(f"\n**Node {node_index}:** {node.situation}")
                                st.write(f"**Reasoning:** {node.reasoning}")
                                
                                # display chat if it exists
                                if node.chat and len(node.chat) > 0:
                                    st.write("**Conversation:**")
                                    for chat_msg in node.chat:
                                        # Handle both ChatMessage objects and dictionaries
                                        if isinstance(chat_msg, dict):
                                            who_value = chat_msg.get('who', 0)
                                            text_value = chat_msg.get('text', '')
                                        else:
                                            who_value = getattr(chat_msg, 'who', 0)
                                            text_value = getattr(chat_msg, 'text', '')
                                        
                                        speaker = "Patient" if who_value == 1 else node.character2.type if node.character2 and hasattr(node.character2, 'type') else "Other"
                                        st.write(f"- **{speaker}:** {text_value}")
                                
                                # display choices
                                for choice_index, choice in enumerate(node.choices, 1):
                                    st.write(f"- **Choice {choice_index}:** {choice.text}")
                                    st.write(f"  - **Outcome:** {choice.outcome}")
                                    st.write(f"  - **Impact:** {choice.impact}")
                            
                            st.write("---")
                            
                            # Log processing time
                            end_time = time.time()
                            processing_time = end_time - start_time
                            logger.info(f"Processing of {pdf_file.name} completed in {processing_time:.2f} seconds")
                    
                    except Exception as e:
                        error_msg = f"Error processing PDF {pdf_file.name}: {str(e)}"
                        logger.error(error_msg)
                        logger.error(traceback.format_exc())
                        st.error(error_msg)
                    
                    finally:
                        # cleanup temporary file
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                            logger.info(f"Temporary file {temp_path} removed")
            
            # process urls if present
            if urls_list:
                total_urls = len(urls_list)
                logger.info(f"Processing {total_urls} URLs")
                
                for url_index, url in enumerate(urls_list):
                    start_time = time.time()
                    status_text.text(f"Processing URL {url_index+1} of {total_urls}: {url}")
                    progress_bar.progress(url_index / total_urls)
                    logger.info(f"Starting processing of URL {url_index+1}/{total_urls}: {url}")
                    
                    try:
                        # extract text from url
                        logger.info(f"Extracting text from URL")
                        url_text = extract_text_from_url(url)
                        if not url_text:
                            error_msg = f"Impossible to extract text from {url}"
                            logger.error(error_msg)
                            st.error(error_msg)
                            continue
                        logger.info(f"Successfully extracted {len(url_text)} characters of text")
                        
                        # extract filename from url
                        base_filename = get_filename_from_url(url)
                        logger.info(f"Generated base filename: {base_filename}")
                        
                        # save raw text
                        raw_text_path = os.path.join(RAW_TEXT_DIR, f"{base_filename}.txt")
                        save_text_to_file(url_text, raw_text_path)
                        logger.info(f"Raw text saved to {raw_text_path}")
                        
                        # process text with agents
                        logger.info(f"Starting story branch generation with AI agent")
                        story_branch, base_filename = loop.run_until_complete(
                            story_generator.create_story_branch_from_text(url_text, base_filename, disease, language=LANGUAGE, how_many_nodes=how_many_nodes)
                        )
                        logger.info(f"Story branch generation completed")
                        
                        if story_branch:
                            # save initial story branch in json
                            output_path = os.path.join(JSON_OUTPUT_DIR, f"{base_filename}_story_branch.json")
                            save_json_to_file(story_branch.model_dump(), output_path)
                            logger.info(f"Story branch saved to {output_path}")
                            
                            # enhance conversations if requested
                            if enhance_conversations:
                                status_text.text(f"Enhancing conversations for {base_filename}...")
                                logger.info(f"Starting conversation enhancement")
                                enhanced_output_path = os.path.join(JSON_OUTPUT_DIR, f"{base_filename}_enhanced_story_branch.json")
                                story_branch = loop.run_until_complete(
                                    conversation_enhancer.enhance_conversations(story_branch, enhanced_output_path)
                                )
                                logger.info(f"Conversation enhancement completed")
                                logger.info(f"Enhanced story branch saved to {enhanced_output_path}")
                                
                                # use the enhanced story branch for further processing
                                output_path = enhanced_output_path
                            
                            # save story branch for combined export
                            all_story_branches.append((story_branch, base_filename))
                            
                            # notify about summary
                            summary_path = os.path.join(SUMMARY_TEXT_DIR, f'{base_filename}_summary.txt')
                            logger.info(f"Summary saved in: {summary_path}")
                            st.info(f"Summary saved in: {summary_path}")
                            
                            if not combine_excel:
                                # convert to excel (individual file)
                                logger.info(f"Converting story branch to Excel")
                                excel_path = excel_converter.story_branch_to_excel(story_branch, base_filename)
                                if excel_path:
                                    logger.info(f"Excel story branch saved in: {excel_path}")
                                    st.info(f"Excel story branch saved in: {excel_path}")
                                    
                                    # download button
                                    excel_buffer = excel_converter.get_excel_download_buffer(story_branch)
                                    st.download_button(
                                        label=f"Download {base_filename} Story Branch (Excel)",
                                        data=excel_buffer,
                                        file_name=f"{base_filename}_story_branch.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                            
                            # display story branch
                            st.write(f"### Story Branch for {url}")
                            st.write(f"**Disease:** {story_branch.disease}")
                            
                            for node_index, node in enumerate(story_branch.nodes, 1):
                                st.write(f"\n**Node {node_index}:** {node.situation}")
                                st.write(f"**Reasoning:** {node.reasoning}")
                                
                                # display chat if it exists
                                if node.chat and len(node.chat) > 0:
                                    st.write("**Conversation:**")
                                    for chat_msg in node.chat:
                                        # handle both ChatMessage objects and dictionaries
                                        if isinstance(chat_msg, dict):
                                            who_value = chat_msg.get('who', 0)
                                            text_value = chat_msg.get('text', '')
                                        else:
                                            who_value = getattr(chat_msg, 'who', 0)
                                            text_value = getattr(chat_msg, 'text', '')
                                        
                                        speaker = "Patient" if who_value == 1 else node.character2.type if node.character2 and hasattr(node.character2, 'type') else "Other"
                                        st.write(f"- **{speaker}:** {text_value}")
                                
                                # display choices
                                for choice_index, choice in enumerate(node.choices, 1):
                                    st.write(f"- **Choice {choice_index}:** {choice.text}")
                                    st.write(f"  - **Outcome:** {choice.outcome}")
                                    st.write(f"  - **Impact:** {choice.impact}")
                            
                            st.write("---")
                            
                            # log processing time
                            end_time = time.time()
                            processing_time = end_time - start_time
                            logger.info(f"Processing of URL {url} completed in {processing_time:.2f} seconds")
                    
                    except Exception as e:
                        error_msg = f"Error processing URL {url}: {str(e)}"
                        logger.error(error_msg)
                        logger.error(traceback.format_exc())
                        st.error(error_msg)
            
            # create combined excel file if requested and there are story branches
            if combine_excel and all_story_branches:
                logger.info(f"Creating combined Excel file for {len(all_story_branches)} story branches")
                combined_buffer = excel_converter.combine_story_branches_to_excel(all_story_branches)
                
                # download button for combined file
                st.download_button(
                    label="Download Combined Story Branches (Excel)",
                    data=combined_buffer,
                    file_name="story_branches.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # also save to file system with timestamp
                combined_path = excel_converter.save_combined_excel(combined_buffer)
                if combined_path:
                    logger.info(f"Combined Excel file saved in: {combined_path}")
                    st.info(f"Combined Excel file saved in: {combined_path}")
            
            status_text.text("Processing completed!")
            progress_bar.progress(1.0)
            logger.info("All processing completed successfully!")
            
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            st.error(error_msg)
        
        finally:
            # close event loop
            loop.close()
            logger.info("Event loop closed")
        
        st.success("All files have been processed!")

if __name__ == "__main__":
    main()