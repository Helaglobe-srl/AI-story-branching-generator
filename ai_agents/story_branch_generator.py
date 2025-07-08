import os
import traceback
from typing import Tuple, Optional
from agents import Agent, Runner, ModelSettings
from models.models import StoryBranch
from utils.utils import save_text_to_file
from utils.logger import get_logger

logger = get_logger("story_branch_generator")

class StoryBranchGenerator:
    """Class for generating story branches using AI agents"""
    
    def __init__(self, model: str, summary_dir: str):
        """Initialize the story branch generator
        
        Args:
            model (str): The OpenAI model to use
            summary_dir (str): Directory to save summaries
        """
        self.model = model
        self.summary_dir = summary_dir
        os.makedirs(self.summary_dir, exist_ok=True)
        logger.info(f"StoryBranchGenerator initialized with model: {model}")
        logger.info(f"Summary directory: {summary_dir}")
    
    async def create_story_branch_from_text(self, text: str, filename: str, disease: str, language: str = "Italian", how_many_nodes: int = 10) -> Tuple[Optional[StoryBranch], Optional[str]]:
        """Process a single text document through the agent pipeline
        
        Args:
            text (str): The text to process
            filename (str): The name of the file to process
            disease (str): The disease the character is suffering from
            language (str): The language to generate the story branch in

        Returns:
            Tuple[Optional[StoryBranch], Optional[str]]: A tuple containing the story branch and the filename
        """
        try:
            # remove .pdf extension from filename
            base_filename = filename.replace('.pdf', '')
            logger.info(f"Processing text for {base_filename} about {disease} in {language}")
            logger.info(f"Generating story branch with {how_many_nodes} nodes")
            
            # processing with text_cleaner agent
            logger.info("Creating text formatter agent")
            text_cleaner = Agent(
                name="text formatter",
                instructions=f"""
                Sei un esperto nell'editing e nella formattazione di testi informativi.
                Prenditi cura di ripulire e riformattare il testo fornito riguardo a {disease}, scritto in **{language}**, senza modificarne il contenuto sostanziale.

                Il tuo compito è:
                - mantenere intatto tutto il significato originale
                - migliorare la leggibilità, correggendo errori grammaticali o sintattici
                - rendere il testo più chiaro e scorrevole, preferendo un linguaggio diretto e accessibile
                - suddividere logicamente il testo in paragrafi, se necessario
                - mantenere eventuali informazioni pratiche (gestione, sintomi, trattamenti, stile di vita, supporto) così come sono, ma rendendole più facilmente comprensibili
                """,
                model=self.model
            )

            logger.info("Running text formatter agent")
            summary_result = await Runner.run(text_cleaner, text)
            logger.info("Text formatter agent completed")
            
            # save summary
            summary_path = os.path.join(self.summary_dir, f"{base_filename}_summary.txt")
            save_text_to_file(summary_result.final_output, summary_path)
            logger.info(f"Saved formatted text to {summary_path}")
            
            # story branch generation
            logger.info("Creating story branch generator agent")
            story_generator = Agent(
                name="story branch generator",
                instructions = f"""
                Sei un esperto nella creazione di esperienze narrative interattive per persone con condizioni di salute.
                Crea una *story branch* composta da {how_many_nodes} nodi decisionali, basata sul testo fornito riguardo a {disease}.

                Per ogni nodo:
                1. Descrivi una situazione realistica che potrebbe verificarsi durante una giornata tipica di una persona con {disease}, in cui sia necessario compiere una scelta.
                2. Fornisci una spiegazione del perché di questa situazione, in base alle informazioni disponibili.
                3. Fornisci ESATTAMENTE 2 opzioni di scelta plausibili, entrambe con vantaggi e compromessi, evitando che una risulti chiaramente 'giusta'.
                4. Per ciascuna opzione, descrivi:
                - l'effetto immediato della scelta
                - l'impatto a breve o medio termine sulla condizione di salute e sul benessere generale della persona
                - un punteggio: +1 per la scelta più corretta dal punto di vista medico, -1 per la scelta meno corretta

                Assicurati che le situazioni riguardino momenti diversi della giornata, come:
                - routine del mattino
                - attività lavorative o quotidiane
                - relazioni sociali
                - pasti
                - attività fisica
                - routine serale
                - eventi imprevisti

                Rendi le scelte non ovvie:
                - Inserisci compromessi in entrambe le opzioni, affinché nessuna sia chiaramente migliore
                - Usa un linguaggio sfumato, evitando termini assoluti o moralistici come "ignora", "salta", "non prendere", "non fare"
                - Considera le motivazioni personali e soggettive (es. dovere vs piacere, efficienza vs benessere)
                - Ritarda o attenua gli effetti delle scelte per rendere più difficile intuire quale sia la più utile
                
                Esempio 1 di nodo:
                Al mattino, Mario si sveglia e deve prendere i farmaci. Deve decidere se fare una colazione o no.
                Opzione A
                Mario decide di prepararsi un caffè veloce con un biscotto avanzato dalla sera prima. Non è una colazione vera e propria, ma gli consente di prendere comunque i farmaci. Si prende qualche minuto in più del previsto, ma spera che questa pausa lo aiuti a sentirsi più lucido nel corso della mattinata.
                Score: +1
                Opzione B
                Mario opta per saltare la colazione e rimandare l'assunzione dei farmaci a quando troverà un momento tranquillo. Preferisce approfittare dell'energia mentale iniziale per sbrigare le prime attività mentre la casa è ancora silenziosa. Pensa che potrà recuperare più tardi, magari durante la pausa pranzo.
                Score: -1

                Esempio 2 di nodo:
                All'ora della pausa, i colleghi invitano Matteo a prendere un espresso al bar e a mangiare una brioche.
                Opzione A
                Va al bar con gli altri e prende un caffè, senza mangiare la brioche, per non rinunciare alla compagnia e limitare gli extra.
                Score: -1
                Opzione B
                Declina l'invito e resta alla scrivania con la propria bottiglietta d'acqua, sfruttando la pausa per rilassarsi.
                Score: +1
                
                Tutto il testo deve essere scritto in **{language}**.
                """,
                output_type=StoryBranch,
                model="gpt-4.1",
                model_settings=ModelSettings(temperature=0.3)
            )
            
            # prompt for the story generator
            logger.info("Preparing prompt for story generator")
            prompt = f"""
            **Patologia: {disease}**

            **Riassunto delle informazioni su {disease}:**  
            {summary_result.final_output}

            Crea una *story branch* con nodi decisionali per una persona che convive con {disease}.
            """
            
            logger.info("Running story branch generator agent")
            story_result = await Runner.run(story_generator, prompt)
            logger.info("Story branch generator agent completed")
            
            # disease field in the result
            if story_result.final_output_as(StoryBranch):
                story_result.final_output_as(StoryBranch).disease = disease
                logger.info(f"Successfully generated story branch with {len(story_result.final_output_as(StoryBranch).nodes)} nodes")
            else:
                logger.warning("Failed to generate story branch")
            
            return story_result.final_output_as(StoryBranch), base_filename  
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
            logger.error(traceback.format_exc())
            print(f"Error processing {filename}: {str(e)}")
            print(traceback.format_exc())
            return None, None 