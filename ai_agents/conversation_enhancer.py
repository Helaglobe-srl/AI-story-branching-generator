import os
import json
from typing import Dict, List, Optional, Tuple, get_args
from agents import Agent, Runner, ModelSettings
from models.models import StoryBranch, BackgroundType, CharacterType
from utils.logger import get_logger

logger = get_logger("conversation_enhancer")

class ConversationEnhancer:
    """Class for enhancing story branches with more detailed conversations"""
    
    def __init__(self, model: str):
        """Initialize the conversation enhancer
        
        Args:
            model (str): The OpenAI model to use
        """
        self.model = model
        logger.info(f"ConversationEnhancer initialized with model: {model}")
        
        # valid options from the model definitions
        self.valid_backgrounds = get_args(BackgroundType)
        self.valid_character2_types = get_args(CharacterType)
        logger.debug(f"Valid backgrounds: {self.valid_backgrounds}")
        logger.debug(f"Valid character types: {self.valid_character2_types}")
    
    async def enhance_conversations(self, story_branch: StoryBranch, output_path: str) -> StoryBranch:
        """Enhance the conversations in a story branch
        
        Args:
            story_branch (StoryBranch): The story branch to enhance
            output_path (str): Path to save the enhanced story branch
            
        Returns:
            StoryBranch: The enhanced story branch
        """
        logger.info(f"Starting conversation enhancement for disease: {story_branch.disease}")
        logger.info(f"Output will be saved to: {output_path}")
        
        # select up to 3 nodes that have character2 (for dialogue)
        dialogue_nodes = [node for node in story_branch.nodes if node.character2 is not None]
        logger.info(f"Found {len(dialogue_nodes)} nodes with character2 for dialogue enhancement")
        
        # if we have more than 3 dialogue nodes, select 3 of them
        if len(dialogue_nodes) > 3:
            logger.info(f"Limiting to 3 nodes for enhancement (from {len(dialogue_nodes)} available)")
            dialogue_nodes = dialogue_nodes[:3]
        
        # enhance each selected node
        for i, node in enumerate(dialogue_nodes):
            # get the node index in the original story branch
            node_index = story_branch.nodes.index(node)
            logger.info(f"Enhancing node {node_index+1}/{len(story_branch.nodes)} (dialogue node {i+1}/{len(dialogue_nodes)})")
            
            # background
            if not node.background or node.background not in self.valid_backgrounds:
                logger.warning(f"Invalid background '{node.background}' detected, setting to default 'sala'")
                node.background = "sala"  # Default if missing or invalid
            else:
                logger.debug(f"Node background: {node.background}")
            
            # character2 type
            if node.character2 and hasattr(node.character2, 'type'):
                if node.character2.type not in self.valid_character2_types:
                    logger.warning(f"Invalid character2 type '{node.character2.type}' detected, setting to default 'familiare'")
                    node.character2.type = "familiare"  # default if invalid
                else:
                    logger.debug(f"Character2 type: {node.character2.type}")
            
            logger.info(f"Creating conversation enhancer agent for node {node_index+1}")
            # conversation enhancer agent
            enhancer = Agent(
                name="conversation enhancer",
                instructions=f"""
                crea dialoghi realistici per storie interattive sulla patologia: {story_branch.disease}.
                
                linee guida:
                - mantieni coerenza con la situazione, il ragionamento e le scelte disponibili
                - rimani neutrale: non suggerire quale scelta sia migliore
                - presenta il dilemma senza risolverlo
                - inizia in modo naturale e logico
                - alterna i messaggi tra paziente (who: 1) e altro personaggio (who: 2)
                - rifletti le preoccupazioni di una persona con {story_branch.disease}
                - esplora il dilemma emotivo senza anticipare decisioni
                
                formato output: lista di 4 messaggi json con campi "who" e "text"
                
                esempio 1 (invito a pranzo):
                [
                  {{"who": 2, "text": "Ehi, stiamo andando tutti a pranzo al nuovo ristorante. Ti unisci a noi?"}},
                  {{"who": 1, "text": "Mi piacerebbe, ma devo fare attenzione a cosa mangio per la mia condizione..."}},
                  {{"who": 2, "text": "Capisco, hanno anche opzioni salutari nel menu se preferisci."}},
                  {{"who": 1, "text": "Ok, grazie. Valuto un attimo..."}}
                ]
                
                esempio 2 (attività fisica):
                [
                  {{"who": 1, "text": "Oggi mi sento un po' stanco, non so se fare la mia solita camminata."}},
                  {{"who": 2, "text": "Capisco, è importante ascoltare il proprio corpo. Come ti senti rispetto ai valori?"}},
                  {{"who": 1, "text": "Sono stabili, ma ho avuto una giornata impegnativa e sono preoccupato di affaticarmi troppo."}},
                  {{"who": 2, "text": "Capisco... cosa pensi sia meglio?"}}
                ]
                """,
                model=self.model,
                model_settings=ModelSettings(temperature=0.7)
            )
            
            # Convert chat messages to dictionaries for serialization
            chat_dicts = []
            if node.chat:
                logger.debug(f"Node has {len(node.chat)} existing chat messages")
                for chat_msg in node.chat:
                    chat_dicts.append({
                        "who": chat_msg.who,
                        "text": chat_msg.text
                    })
            else:
                logger.debug("Node has no existing chat messages")
            
            # here we determine who should start the conversation based on the situation
            character2_type = node.character2.type if node.character2 and hasattr(node.character2, 'type') else 'familiare'
            logger.debug(f"Character2 type for conversation: {character2_type}")
            
            # prompt for the enhancer
            logger.info("Preparing prompt for conversation enhancement")
            prompt = f"""
            **Situazione:** {node.situation}
            
            **Ragionamento:** {node.reasoning}
            
            **Background:** {node.background}
            
            **Personaggio 1:** Paziente con {story_branch.disease}
            
            **Personaggio 2:** {character2_type}
            
            **Scelta 1:** {node.choices[0].text if node.choices and len(node.choices) > 0 else ""}
            
            **Scelta 2:** {node.choices[1].text if node.choices and len(node.choices) > 1 else ""}
            
            Crea una conversazione di 4 messaggi che:
            1. Inizi in modo naturale e appropriato al contesto
            2. Presenti il dilemma in modo equilibrato
            3. Rimanga neutrale rispetto alle scelte
            4. Non anticipi la decisione finale
            """
            
            # run the enhancer agent
            logger.info(f"Running conversation enhancer agent for node {node_index+1}")
            result = await Runner.run(enhancer, prompt)
            logger.info(f"Conversation enhancer agent completed for node {node_index+1}")
            
            try:
                # parse the enhanced conversation
                logger.debug(f"Raw agent output: {result.final_output}")
                enhanced_chat = json.loads(result.final_output)
                logger.info(f"Successfully parsed enhanced conversation with {len(enhanced_chat)} messages")
                
                # update the node's chat
                story_branch.nodes[node_index].chat = enhanced_chat
                logger.info(f"Updated chat for node {node_index+1}")
            except Exception as e:
                logger.error(f"Error parsing enhanced conversation: {str(e)}")
                logger.error(f"Raw output: {result.final_output}")
                print(f"Error parsing enhanced conversation: {str(e)}")
                print(f"Raw output: {result.final_output}")
        
        # save the enhanced story branch
        logger.info(f"Saving enhanced story branch to {output_path}")
        with open(output_path, "w") as f:
            json.dump(story_branch.model_dump(), f, indent=2, ensure_ascii=False)
        logger.info("Enhancement complete")
        
        return story_branch 