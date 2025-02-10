# storyjupyter/services/markdown.py
from typing import Sequence
from ..core.protocols import TimelineManager
from pathlib import Path
from typing import Optional
class MarkdownGenerator:
    """Generates markdown output from timeline events"""
    
    def __init__(self, timeline_manager: TimelineManager) -> None:
        self.timeline = timeline_manager
    
    def generate_chapter(self, chapter: int) -> str:
        """Generate markdown for a specific chapter"""
        events = self.timeline.get_events(chapter=chapter)
        
        # Group events by location for scene breaks
        scenes = []
        current_scene = []
        current_location = None
        
        for event in events:
            if event.location != current_location:
                if current_scene:
                    scenes.append((current_location, current_scene))
                current_scene = []
                current_location = event.location
            current_scene.append(event.content)
        
        if current_scene:
            scenes.append((current_location, current_scene))
        
        # Generate markdown
        output = [f"# Chapter {chapter}\n"]
        
        for location, content in scenes:
            output.append(f"\n## {location}\n")
            output.append("".join(content))
            output.append("\n")
        
        return "\n".join(output)
    
    def generate_manuscript(self, chapters: Sequence[int]) -> str:
        """Generate complete manuscript"""
        chapter_content = []
        
        for chapter in sorted(chapters):
            chapter_content.append(self.generate_chapter(chapter))
        
        return "\n\n".join(chapter_content)