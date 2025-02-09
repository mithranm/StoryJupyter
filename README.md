# StoryJupyter Framework

## Motivation

To assist writers in creating coherent stories, I propose a framework using Jupyter notebook and other libraries that will manage many of the difficult tasks writers face.

A writer's computer can struggle with large amounts of narrative text. I propose writers start every chapter in a new notebook, breaking their chapters down into multiple markdown/latex cells. This will also help with organization.

Writing a timeline that is consistent is challenging, especially when multiple perspectives are involved. To assist writers in creating timelines, StoryJupyter should represent the timeline in the narrative as a data structure and validate it. This can be done through author written python code utilizing certain libraries.

Writing compelling characters on the first attempt is difficult. To assist writers in this endeavor, I propose characters optionally be represented through placeholders, with their attributes such as name and ethnicity easily interchangeable through python code.

## Example Workflow

```python
# start_time is defined in the story_jupyter package
from story_jupyter import set_time, inc_time, get_time, character, pronoun
set_time("2024-01-01_13-12-34")
```

```markdown
It was a beautiful afteroon. My watch displayed 1:12, I was three minutes early. There were six students already in the classroom.
```

```python
inc_time("5 minutes")
```

```markdown
The time right now in ISO Format would be {{get_time("ISO")}}.
```

```python
main_character = character.create(first="Jessie", prounoun=pronoun.male())

students_alpha = character.creates(num=5)
students_alpha[0] = character.create(full="Alice Override") # Can create a new character and assign it to list
students_alpha[0].set(last="Allwein") # Overrides initial name setting
students_alpha[1].set(full="Bob Buchanan Builder") # Set can be called because character.creates() initializes list with empty character object.
students_alpha[2] = character.create(prompt="A female student of asian descent whose name starts with a C", fill=["first", "last", "middle"]) # Utilizes any openai compatible endpoint to generate values
character[3] = character.create(first="Devin", middle="Darnell", last="Daredevil", age="18", love_interest="Alice", custom_field="test") # Schema should be flexible and unique to every character. Not even first name is guaranteed.

teacher_alpha = character.create(last="Watson", title="Ms.")

# Character fills the last and middle names with random names of a first name only character if they ever accessed. Are not LLM generated and are unique as well as consistent through every execution of the notebook. Implementation likely requires maintaining a database of unique names that don't collide in first middle and last.
print(main_character.get("last"))
# Jackson
print(main_character.get("full"))
# Jessie Jojo Jackson
print(main_character.get("love_interest"))
# INFO: LLM Generating key 'love_interest' for Jessie Jojo Jackson
# Alice Ahjee Allwein
asian_girl = students_alpha[2]
print(asian_girl)
# Carly Catherine Chen
```

```markdown
{{main_character.get("first")}} walks to {{main_character.pronoun("possessive")}} desk and sits down. He sits next to {{students_alpha[3].get("first")}} who is currently staring at {{asian_girl}}.
```

## Example output

```markdown
It was a beautiful afteroon. My watch displayed 1:12, I was three minutes early. There were six students already in the classroom.

The time right now in ISO Format would be 2024-01-01T13:17:34.

Jessie walks to his desk and sits down. He sits next to Devin who is currently staring at Carly Catherine Chen. 
```

## Limitations

Middle names are requried, multiple middle names are unsupported, hyphenations are unsupported.

Authors should have more granular control over how keys behave, for example, in the case of "love_interest", the author could specify that StoryJupyter should choose from all the characters that have been introduced so far under the age of 20. We could offer a SQL-like query language for finding appropriate matches. Perhaps maintaining an SQLite database for each notebook is the answer.

Another limitation is cross-chapter maintenance. How can authors link their notebooks together and make sure all the information is up to date and relevant?

There is also a formatting limitation. An author may want to create changes to the state of the story mid paragraph. There needs to be a method to do this.

## DeepSeek Addressing Limitations

**1. Schema Rigidity in Character Attributes**

**Problem**: The framework enforces mandatory middle names and lacks support for hyphenations or multiple middle names, limiting flexibility.**Solution**:

- **Flexible Schema Design**: Use a schema-less data structure like Python dictionaries or Pydantic models to allow dynamic attribute assignment. For example:
  ```python
  class Character(BaseModel):
      attributes: dict = Field(default_factory=dict)
      def set(self, **kwargs): self.attributes.update(kwargs)
  ```

  This enables authors to define custom fields (e.g., `hyphenated_names`, `aliases`) without constraints .
- **Name Generation Libraries**: Integrate libraries like `Faker` for locale-specific name generation, supporting hyphenations, multiple middle names, and cultural variations.

---

#### **2. Granular Control Over Character Relationships**

**Problem**: Attributes like `love_interest` lack context-aware selection (e.g., filtering characters by age).**Solution**:

- **SQLite Integration**: Embed an SQLite database per notebook to store character metadata. Use SQLAlchemy ORM for querying:
  ```python
  session.query(Character).filter(Character.age < 20).all()
  ```

  This allows authors to run complex queries (e.g., "select characters introduced in Chapter 3") .
- **Rule-Based Matching**: Implement a DSL (Domain-Specific Language) for defining relationship rules, such as:
  ```python
  love_interest_rules = {"age": "<20", "chapter_introduced": "<=current"}
  ```

---

#### **3. Cross-Chapter Consistency**

**Problem**: Notebooks are isolated, making global state management (e.g., timeline, character changes) difficult.**Solution**:

- **Centralized Metadata Storage**: Use a lightweight database (e.g., DuckDB) or YAML/JSON files to track characters, timelines, and plot points across notebooks.
- **Dependency Management**: Adopt `Ploomber` to create pipelines that link notebooks into a cohesive workflow, ensuring data synchronization .
- **Version Control**: Pair notebooks with plain-text scripts via `Jupytext` to simplify Git-based tracking of character arcs and timelines .

---

#### **4. Mid-Paragraph State Updates**

**Problem**: Authors cannot modify story state mid-paragraph without disrupting narrative flow.**Solution**:

- **Reactive Programming**: Integrate `ipywidgets` or `Observable`’s reactive runtime to dynamically update variables when dependencies change. For example:
  ```python
  from ipywidgets import interact
  @interact(time=inc_time("5 minutes"))
  def update_scene(time):
      display(Markdown(f"The time is now {time}"))
  ```
- **Preprocessor Directives**: Add custom Markdown tags (e.g., `{{% inc_time("5 minutes") %}}`) parsed by a Jupyter extension to execute code inline .

---

#### **5. Performance and Scalability**

**Problem**: Large narratives may strain Jupyter’s memory or execution speed.**Solution**:

- **Modular Codebases**: Transition core logic (e.g., timeline validation) to standalone Python modules, reducing notebook bloat .
- **Caching**: Use `joblib` or `diskcache` to cache LLM-generated content (e.g., auto-filled character names) .
- **Cloud Integration**: Offload heavy computations (e.g., LLM inference) to serverless functions via `AWS Lambda` or `Modal`.

---

### Proposed Technology Stack

| Component                        | Tool/Library                    | Use Case                                |
| -------------------------------- | ------------------------------- | --------------------------------------- |
| **Data Storage**           | SQLite, DuckDB                  | Track characters and timelines globally |
| **Query Language**         | SQLAlchemy                      | Filter characters with complex logic    |
| **Reactive UI**            | ipywidgets, Voilà              | Dynamic state updates and dashboards    |
| **Workflow Orchestration** | Ploomber, DVC                   | Link notebooks and version data         |
| **Name Generation**        | Faker, OpenAI Compatible Ollama | Culturally diverse character attributes |

---

### Final Recommendations

- **Adopt JupyterLab**: Replace classic Jupyter with JupyterLab for better tab management, file navigation, and extensions .
- **Automate Testing**: Use `nbval` to validate notebook outputs during CI/CD pipelines, ensuring timeline and character consistency .
- **Hybrid Workflow**: Separate exploratory writing (notebooks) from production-ready code (modules) to balance interactivity and scalability .

By addressing these limitations, StoryJupyter can evolve into a robust platform for both creative writing and technical rigor.
