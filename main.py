import os
import json
import traceback
import asyncio
import nest_asyncio
import streamlit as st
from dotenv import load_dotenv
from excel.excel_converter import StoryBranchExcelConverter
from ai_agents.story_branch_generator import StoryBranchGenerator
from utils.utils import (
    setup_directories, 
    extract_text_from_pdf, 
    save_text_to_file, 
    extract_text_from_url, 
    get_filename_from_url
)

load_dotenv()

nest_asyncio.apply()

# directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_TEXT_DIR, SUMMARY_TEXT_DIR, JSON_OUTPUT_DIR = setup_directories(BASE_DIR)

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
    
    st.write("---")
    
    # verify api key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("Please set OPENAI_API_KEY in your .env file")
        return
    
    if st.button("Generate Story Branches"):
        if not disease:
            st.error("Please enter a disease name")
            return
            
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # create event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        excel_converter = StoryBranchExcelConverter(BASE_DIR)
        story_generator = StoryBranchGenerator(model, SUMMARY_TEXT_DIR)
        
        # store all story branches for combined export
        all_story_branches = []
        
        try:
            # process pdfs if present
            if uploaded_files:
                total_files = len(uploaded_files)
                for file_index, pdf_file in enumerate(uploaded_files):
                    status_text.text(f"Processing PDF {file_index+1} of {total_files}: {pdf_file.name}")
                    progress_bar.progress(file_index / total_files)
                    
                    # temporary save of uploaded file
                    temp_path = f"temp_{pdf_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(pdf_file.getbuffer())
                    
                    try:
                        # extract text from pdf
                        pdf_text = extract_text_from_pdf(temp_path)
                        if not pdf_text:
                            st.error(f"Impossible to extract text from {pdf_file.name}")
                            continue
                        
                        # save raw text
                        base_filename = pdf_file.name.replace('.pdf', '')
                        raw_text_path = os.path.join(RAW_TEXT_DIR, f"{base_filename}.txt")
                        save_text_to_file(pdf_text, raw_text_path)
                        
                        # process text with agents
                        story_branch, base_filename = loop.run_until_complete(
                            story_generator.create_story_branch_from_text(pdf_text, pdf_file.name, disease, "Italian")
                        )
                        
                        if story_branch:
                            # save story branch for combined export
                            all_story_branches.append((story_branch, base_filename))
                            
                            # save story branch in json
                            output_path = os.path.join(JSON_OUTPUT_DIR, f"{base_filename}_story_branch.json")
                            with open(output_path, "w") as f:
                                json.dump(story_branch.model_dump(), f, indent=2, ensure_ascii=False)
                            
                            # notify about text cleaning
                            st.info(f"Text cleaned and formatted saved in: {os.path.join(SUMMARY_TEXT_DIR, f'{base_filename}_cleaned.txt')}")
                            
                            if not combine_excel:
                                # convert to excel (individual file)
                                excel_path = excel_converter.story_branch_to_excel(story_branch, base_filename)
                                if excel_path:
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
                                for choice_index, choice in enumerate(node.choices, 1):
                                    st.write(f"- **Choice {choice_index}:** {choice.text}")
                                    st.write(f"  - **Outcome:** {choice.outcome}")
                                    st.write(f"  - **Impact:** {choice.impact}")
                            
                            st.write("---")
                    
                    finally:
                        # cleanup temporary file
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
            
            # process urls if present
            if urls_list:
                total_urls = len(urls_list)
                for url_index, url in enumerate(urls_list):
                    status_text.text(f"Processing URL {url_index+1} of {total_urls}: {url}")
                    progress_bar.progress(url_index / total_urls)
                    
                    try:
                        # extract text from url
                        url_text = extract_text_from_url(url)
                        if not url_text:
                            st.error(f"Impossible to extract text from {url}")
                            continue
                        
                        # extract filename from url
                        base_filename = get_filename_from_url(url)
                        
                        # save raw text
                        raw_text_path = os.path.join(RAW_TEXT_DIR, f"{base_filename}.txt")
                        save_text_to_file(url_text, raw_text_path)
                        
                        # process text with agents
                        story_branch, base_filename = loop.run_until_complete(
                            story_generator.create_story_branch_from_text(url_text, base_filename, disease, "Italian")
                        )
                        
                        if story_branch:
                            # save story branch for combined export
                            all_story_branches.append((story_branch, base_filename))
                            
                            # save story branch in json
                            output_path = os.path.join(JSON_OUTPUT_DIR, f"{base_filename}_story_branch.json")
                            with open(output_path, "w") as f:
                                json.dump(story_branch.model_dump(), f, indent=2, ensure_ascii=False)
                            
                            # notify about summary
                            st.info(f"Summary saved in: {os.path.join(SUMMARY_TEXT_DIR, f'{base_filename}_summary.txt')}")
                            
                            if not combine_excel:
                                # convert to excel (individual file)
                                excel_path = excel_converter.story_branch_to_excel(story_branch, base_filename)
                                if excel_path:
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
                                for choice_index, choice in enumerate(node.choices, 1):
                                    st.write(f"- **Choice {choice_index}:** {choice.text}")
                                    st.write(f"  - **Outcome:** {choice.outcome}")
                                    st.write(f"  - **Impact:** {choice.impact}")
                            
                            st.write("---")
                    
                    except Exception as e:
                        st.error(f"Error processing URL {url}: {str(e)}")
                        print(f"Error processing URL {url}: {str(e)}")
                        print(traceback.format_exc())
            
            # create combined excel file if requested and there are story branches
            if combine_excel and all_story_branches:
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
                    st.info(f"Combined Excel file saved in: {combined_path}")
            
            status_text.text("Processing completed!")
            progress_bar.progress(1.0)
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            print(f"Error in main processing loop: {str(e)}")
            print(traceback.format_exc())
        
        finally:
            # close event loop
            loop.close()
        
        st.success("All files have been processed!")

if __name__ == "__main__":
    main()