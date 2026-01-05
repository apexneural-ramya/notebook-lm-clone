"""Podcast script generation using LLM"""
import json
import logging
from typing import List, Dict
from dataclasses import dataclass

from crewai import LLM

logger = logging.getLogger(__name__)


@dataclass
class PodcastScript:
    """Represents a generated podcast script"""
    script: List[Dict[str, str]]
    source_document: str
    total_lines: int
    estimated_duration: str
    
    def to_json(self) -> str:
        return json.dumps({
            "script": self.script,
            "metadata": {
                "source_document": self.source_document,
                "total_lines": self.total_lines,
                "estimated_duration": self.estimated_duration
            }
        }, indent=2)


class PodcastScriptGenerator:
    def __init__(self, openrouter_api_key: str, model_name: str = "openai/gpt-4o-mini"):
        self.llm = LLM(
            model=f"openrouter/{model_name}",
            temperature=0.7,
            max_tokens=4000,
            api_key=openrouter_api_key
        )
        logger.info(f"Podcast script generator initialized with {model_name}")
    
    def generate_script_from_text(
        self,
        text_content: str,
        source_name: str,
        podcast_style: str = "Conversational",
        target_duration: str = "10 minutes"
    ) -> PodcastScript:
        """Generate a podcast script from text content"""
        logger.info("Generating podcast script from text input")
        
        if len(text_content) > 8000:
            text_content = text_content[:8000] + "..."
        
        prompt = f"""You are a professional podcast script writer. Create a {podcast_style.lower()} podcast script based on the following content.

Source: {source_name}
Style: {podcast_style}
Target Duration: {target_duration}

Content:
{text_content}

Create a dialogue between two speakers (Speaker 1 and Speaker 2) discussing the key points from the content. Make it engaging, informative, and natural.

Requirements:
- Use exactly two speakers: "Speaker 1" and "Speaker 2"
- Alternate between speakers
- Each dialogue should be a complete thought or sentence
- Keep responses concise but informative
- Aim for approximately {target_duration} of content
- Make it sound like a natural conversation

Respond with a valid JSON object containing a 'script' array. Each array element should be an object with either 'Speaker 1' or 'Speaker 2' as the key and their dialogue as the value.

Example format:
{{
  "script": [
    {{"Speaker 1": "Welcome to today's podcast. Let's discuss the key points from our source."}},
    {{"Speaker 2": "Absolutely! I found the content very interesting, especially..."}},
    {{"Speaker 1": "That's a great point. What do you think about..."}}
  ]
}}"""

        try:
            response = self.llm.call(prompt)
            
            script_data = json.loads(response)
            
            if 'script' not in script_data or not isinstance(script_data['script'], list):
                raise ValueError("Invalid script format returned by LLM")
            
            validated_script = self._validate_and_clean_script(script_data['script'])
            
            estimated_minutes = max(1, len(validated_script) // 30)
            estimated_duration = f"{estimated_minutes} minutes"
            
            logger.info(f"Generated script with {len(validated_script)} lines")
            
            return PodcastScript(
                script=validated_script,
                source_document=source_name,
                total_lines=len(validated_script),
                estimated_duration=estimated_duration
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw LLM response: {response[:500]}...")
            response_clean = response.strip()
            
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
                if response_clean.endswith('```'):
                    response_clean = response_clean[:-3]
            elif response_clean.startswith('```'):
                response_clean = response_clean[3:]
                if response_clean.endswith('```'):
                    response_clean = response_clean[:-3]
            
            response_clean = response_clean.strip()
            
            try:
                script_data = json.loads(response_clean)
                if 'script' not in script_data:
                    raise ValueError("JSON response missing 'script' key")
                validated_script = self._validate_and_clean_script(script_data['script'])
                logger.info("Successfully parsed JSON after cleaning")
                
                estimated_minutes = max(1, len(validated_script) // 30)
                estimated_duration = f"{estimated_minutes} minutes"
                
                return PodcastScript(
                    script=validated_script,
                    source_document=source_name,
                    total_lines=len(validated_script),
                    estimated_duration=estimated_duration
                )
            except json.JSONDecodeError as e2:
                logger.error(f"Still failed to parse after cleaning: {e2}")
                logger.error(f"Cleaned response: {response_clean[:500]}...")
                raise ValueError(f"Could not parse LLM response as valid JSON. The AI may have returned invalid format. Please try again.")
            except Exception as e2:
                logger.error(f"Error processing cleaned JSON: {e2}")
                raise ValueError(f"Could not process LLM response: {str(e2)}")
        
        except Exception as e:
            logger.error(f"Error generating script: {str(e)}")
            raise
    
    def _validate_and_clean_script(self, script: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Validate and clean the script format"""
        cleaned_script = []
        expected_speaker = "Speaker 1"
        for item in script:
            if not isinstance(item, dict) or len(item) != 1:
                continue
            
            speaker, dialogue = next(iter(item.items()))
            speaker = speaker.strip()

            if speaker not in ["Speaker 1", "Speaker 2"]:
                if "1" in speaker or "one" in speaker.lower():
                    speaker = "Speaker 1"
                elif "2" in speaker or "two" in speaker.lower():
                    speaker = "Speaker 2"
                else:
                    speaker = expected_speaker
            
            dialogue = dialogue.strip()
            if not dialogue:
                continue
            if not dialogue.endswith(('.', '!', '?')):
                dialogue += '.'
            
            cleaned_script.append({speaker: dialogue})

            expected_speaker = "Speaker 2" if expected_speaker == "Speaker 1" else "Speaker 1"
        
        if len(cleaned_script) < 2:
            raise ValueError("Generated script is too short or invalid")
        
        return cleaned_script

