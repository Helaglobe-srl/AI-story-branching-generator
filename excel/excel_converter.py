import os
import json
import io
from typing import List, Tuple, Optional
import pandas as pd
from models.models import StoryBranch
import datetime
from utils.logger import get_logger

logger = get_logger("excel_converter")

class StoryBranchExcelConverter:
    """Class for converting story branches to Excel format"""
    
    def __init__(self, base_dir: str):
        """Initialize the Excel converter
        
        Args:
            base_dir (str): Base directory for output files
        """
        self.excel_output_dir = os.path.join(base_dir, "excel_story_branches")
        os.makedirs(self.excel_output_dir, exist_ok=True)
        logger.info(f"StoryBranchExcelConverter initialized with output directory: {self.excel_output_dir}")
    
    def story_branch_to_excel(self, story_branch: StoryBranch, filename: str) -> Optional[str]:
        """Convert a story branch to Excel format
        
        Args:
            story_branch (StoryBranch): The story branch to convert
            filename (str): The base filename to use for the Excel file
            
        Returns:
            Optional[str]: The path to the Excel file, or None if conversion failed
        """
        try:
            logger.info(f"Converting story branch for {filename} to Excel")
            # Create a list to store all rows
            rows = []
            
            # Add disease information
            rows.append({
                "Story Branch": filename,
                "Node": "Disease",
                "Situation": story_branch.disease,
                "Reasoning": "",
                "Choice": "",
                "Outcome": "",
                "Impact": ""
            })
            
            # Add node information
            for i, node in enumerate(story_branch.nodes, 1):
                # Add situation
                rows.append({
                    "Story Branch": filename,
                    "Node": f"Node {i}",
                    "Situation": node.situation,
                    "Reasoning": node.reasoning,
                    "Choice": "",
                    "Outcome": "",
                    "Impact": ""
                })
                
                # Add choices
                for j, choice in enumerate(node.choices, 1):
                    rows.append({
                        "Story Branch": filename,
                        "Node": f"Node {i} Choice {j}",
                        "Situation": "",
                        "Reasoning": "",
                        "Choice": choice.text,
                        "Outcome": choice.outcome,
                        "Impact": choice.impact
                    })
            
            # Create DataFrame
            df = pd.DataFrame(rows)
            logger.debug(f"Created DataFrame with {len(rows)} rows")
            
            # Generate timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save to Excel using xlsxwriter engine
            excel_path = os.path.join(self.excel_output_dir, f"{filename}_story_branch_{timestamp}.xlsx")
            with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Story Branch')
                writer.close()
            
            logger.info(f"Saved Excel file to {excel_path}")
            return excel_path
            
        except Exception as e:
            logger.error(f"Error converting story branch to Excel: {str(e)}")
            return None
    
    def get_excel_download_buffer(self, story_branch: StoryBranch) -> io.BytesIO:
        """Get an Excel file buffer for download
        
        Args:
            story_branch (StoryBranch): The story branch to convert
            
        Returns:
            io.BytesIO: A buffer containing the Excel file
        """
        try:
            logger.info("Creating Excel download buffer")
            # Create a list to store all rows
            rows = []
            
            # Add disease information
            rows.append({
                "Story Branch": "Story Branch",
                "Node": "Disease",
                "Situation": story_branch.disease,
                "Reasoning": "",
                "Choice": "",
                "Outcome": "",
                "Impact": ""
            })
            
            # Add node information
            for i, node in enumerate(story_branch.nodes, 1):
                # Add situation
                rows.append({
                    "Story Branch": "Story Branch",
                    "Node": f"Node {i}",
                    "Situation": node.situation,
                    "Reasoning": node.reasoning,
                    "Choice": "",
                    "Outcome": "",
                    "Impact": ""
                })
                
                # Add choices
                for j, choice in enumerate(node.choices, 1):
                    rows.append({
                        "Story Branch": "Story Branch",
                        "Node": f"Node {i} Choice {j}",
                        "Situation": "",
                        "Choice": choice.text,
                        "Outcome": choice.outcome,
                        "Impact": choice.impact
                    })
            
            # Create DataFrame
            df = pd.DataFrame(rows)
            
            # Create buffer and save Excel file
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Story Branch')
                writer.close()
            
            # Reset buffer position
            buffer.seek(0)
            
            logger.info("Excel download buffer created successfully")
            return buffer
            
        except Exception as e:
            logger.error(f"Error creating Excel buffer: {str(e)}")
            return io.BytesIO()
    
    def combine_story_branches_to_excel(self, story_branches: List[Tuple[StoryBranch, str]]) -> io.BytesIO:
        """Combine multiple story branches into a single Excel file
        
        Args:
            story_branches (List[Tuple[StoryBranch, str]]): List of tuples containing story branches and filenames

        Returns:
            io.BytesIO: A buffer containing the combined Excel file
        """
        try:
            logger.info(f"Combining {len(story_branches)} story branches into a single Excel file")
            # Create a list to store all rows
            all_rows = []
            
            # Process each story branch
            for story_branch, filename in story_branches:
                logger.debug(f"Processing story branch for {filename}")
                # Add separator row
                all_rows.append({
                    "Story Branch": f"=== {filename} ===",
                    "Node": "",
                    "Situation": "",
                    "Reasoning": "",
                    "Choice": "",
                    "Outcome": "",
                    "Impact": ""
                })
                
                # Add disease information
                all_rows.append({
                    "Story Branch": filename,
                    "Node": "Disease",
                    "Situation": story_branch.disease,
                    "Reasoning": "",
                    "Choice": "",
                    "Outcome": "",
                    "Impact": ""
                })
                
                # Add node information
                for i, node in enumerate(story_branch.nodes, 1):
                    # Add situation
                    all_rows.append({
                        "Story Branch": filename,
                        "Node": f"Node {i}",
                        "Situation": node.situation,
                        "Reasoning": node.reasoning,
                        "Choice": "",
                        "Outcome": "",
                        "Impact": ""
                    })
                    
                    # Add choices
                    for j, choice in enumerate(node.choices, 1):
                        all_rows.append({
                            "Story Branch": filename,
                            "Node": f"Node {i} Choice {j}",
                            "Situation": "",
                            "Reasoning": "",
                            "Choice": choice.text,
                            "Outcome": choice.outcome,
                            "Impact": choice.impact
                        })
            
            # Create DataFrame
            df = pd.DataFrame(all_rows)
            logger.debug(f"Created combined DataFrame with {len(all_rows)} rows")
            
            # Create buffer and save Excel file
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Story Branches')
                writer.close()
            
            # Reset buffer position
            buffer.seek(0)
            
            logger.info("Combined Excel buffer created successfully")
            return buffer
            
        except Exception as e:
            logger.error(f"Error combining story branches to Excel: {str(e)}")
            return io.BytesIO()
            
    def save_combined_excel(self, buffer: io.BytesIO) -> str:
        """Save the combined Excel file to disk
        
        Args:
            buffer (io.BytesIO): The buffer containing the Excel file
            
        Returns:
            str: The path to the saved Excel file
        """
        try:
            logger.info("Saving combined Excel file to disk")
            # Generate timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create DataFrame from buffer using openpyxl for reading
            df = pd.read_excel(buffer, engine='openpyxl')
            
            # Save to file using xlsxwriter engine
            combined_path = os.path.join(self.excel_output_dir, f"story_branches_{timestamp}.xlsx")
            with pd.ExcelWriter(combined_path, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Story Branches')
                
            logger.info(f"Combined Excel file saved to {combined_path}")
            return combined_path
            
        except Exception as e:
            logger.error(f"Error saving combined Excel file: {str(e)}")
            return "" 