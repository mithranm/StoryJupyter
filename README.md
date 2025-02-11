# StoryJupyter Framework

## Motivation

Complex narratives have many dynamic elements. Characters, Events, Timelines, Syuzhet, Fabula—each presents a unique challenge that threatens to derail the storytelling process. Maintaining consistency across multiple character arcs becomes a nightmare of interconnected motivations and potential plot holes. Timeline coherence demands obsessive attention, with each narrative thread risking contradiction or confusion.

## Solution

StoryJupyter leverages the interactive nature of Jupyter Notebooks to provide a structured environment for managing complex narratives. The framework offers tools for character generation, timeline management, and narrative consistency checking, all within the familiar notebook interface.

## Features

### Core Story Management
- **StoryManager**: Central interface for managing all story elements
- **Chapter-based Organization**: Stories are organized into chapters with proper state management
- **Persistence**: Automatic saving of story elements using MongoDB
- **Timeline Validation**: Built-in checks for timeline consistency within chapters

### Character Management
- **Flexible Character Generation**:
  - Faker-based character generation for quick prototyping
  - LLM-based character generation for more detailed, context-aware characters
  - Support for custom character attributes and relationships
- **Name Components**: Structured handling of character names including first, middle, last names, prefixes, and suffixes
- **Pronouns System**: Comprehensive pronoun management (he/she/they) with proper grammatical forms
- **Character Persistence**: Database storage and retrieval of character information
- **Chapter Tracking**: Automatic tracking of when characters are introduced in the story

### Timeline Management
- **Chronological Events**: Precise timestamp-based event tracking
- **Location Tracking**: Scene and location management
- **Duration Parsing**: Natural language parsing for time durations (e.g., "15 minutes", "2 hours")
- **Time Navigation**: Methods for setting and advancing story time
- **Event Metadata**: Support for additional event data including tags and importance levels

### Content Generation
- **Markdown Export**: Generation of properly formatted manuscript chapters
- **Scene Organization**: Automatic scene breaks based on location changes
- **Brand Management**: Deterministic generation of consistent brand names

### Interactive Tools
- **Jupyter Widgets**: Interactive controls for character generation parameters
- **Real-time Preview**: Immediate feedback for generated content
- **Timeline Visualization**: Chapter-based timeline views

## Getting Started

### Installation

```bash
git clone https://github.com/mithranm/StoryJupyter.git
cd StoryJupyter
pip install -e .
```

### Basic Usage

```python
from storyjupyter import StoryManager
from datetime import datetime

# Initialize story
story = StoryManager(db_name="my_story", chapter=1)

# Set initial time and location
story.set_time(datetime(2025, 1, 1, 12, 0, 0))
story.set_location("Town Square")

# Create a character
protagonist = story.create_character(character_id="protagonist")

# Add story events
story.print("The clock tower strikes noon.")
story.advance_time("15 minutes")
story.print(f"A figure emerges from the crowd. {protagonist.name.first} looks around nervously.")

# Generate manuscript
manuscript = story.generate_manuscript()
```

## Examples

The package includes several example notebooks demonstrating key features:
- `example.ipynb`: Basic story creation and management
- `character_tuning.ipynb`: Character generation with different parameters
- `persistence_example.ipynb`: Working with saved story elements

## Requirements
- Python 3.12 or higher
- MongoDB instance for persistence
