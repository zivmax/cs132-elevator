## Requirements Document Style Guide

### Document Structure & Organization

**Main Section Hierarchy:**
1. **System Overview** - High-level system description and key components
2. **Use Case Diagram** - Visual representation with detailed descriptions
3. **Class Diagram** - System architecture with relationship mappings
4. **Activity Diagrams** - Process workflows with decision points
5. **Sequence Diagrams** - Interaction flows between components
6. **Functional Requirements** - Structured requirement specifications

**Section Formatting Rules:**
- Use clear, numbered table of contents with anchor links
- Separate major sections with triple dashes (`---`)
- Include descriptive subsection headers for complex diagrams
- End with italicized summary statement

### Content Organization Patterns

**System Overview Structure:**
- Lead with concise system purpose statement
- Include bulleted list of "Key System Components" with bold labels and descriptions
- Focus on high-level architecture and primary capabilities

**Diagram Integration:**
- Each diagram type gets its own major section
- Include both visual diagrams (Mermaid) and explanatory text
- Provide "Description" subsections that categorize and explain diagram elements
- Use consistent naming conventions across all diagrams

**Use Case Documentation:**
- Organize use cases into logical categories (Primary, System Operations, etc.)
- Use format: "**UC# - Title**: Description"
- Include actor relationships and system interactions

### Visual Diagram Standards

**Mermaid Diagram Conventions:**
- Use descriptive node labels, not just abbreviations
- Apply consistent color/styling through subgraphs
- Include relationship annotations (e.g., "contains 2", "uses")
- Use semantic node shapes (rectangles for processes, diamonds for decisions)

**Class Diagram Specifics:**
- Show visibility modifiers (`+` public, `-` private)
- Include method signatures with return types
- Group related classes in logical sections
- Add interface stereotypes where applicable
- Document relationships with cardinality and descriptions

**Activity/Sequence Diagrams:**
- Use decision diamonds for branching logic
- Include loop constructs for repetitive processes
- Show parallel processing where applicable
- Use descriptive participant names in sequence diagrams

### Functional Requirements Format

**Hierarchical Numbering:**
- Major categories: FR1, FR2, FR3...
- Sub-requirements: FR1.1, FR1.2, FR1.3...

**Requirement Statement Structure:**
- **Bold category titles** with descriptive names
- Each requirement starts with "System shall..." or "Users shall be able to..."
- Include specific measurable criteria (times, quantities, behaviors)
- Group related requirements under logical categories

### Writing Style Guidelines

**Tone and Voice:**
- Use technical, precise language
- Maintain consistency in terminology throughout
- Write in third person, active voice
- Use "shall" for mandatory requirements

**Formatting Conventions:**
- Bold key terms, component names, and requirement categories
- Use backticks for code elements, file names, or technical identifiers
- Apply consistent capitalization for system components
- Use bullet points for lists, numbered lists for sequential processes

**Documentation Standards:**
- Include file path comments at document start
- Provide clear section anchors for navigation
- Use descriptive alt-text concepts for diagrams
- Maintain consistent indentation and spacing

### Content Depth Guidelines

**Comprehensive Coverage:**
- Include both user-facing and system-internal requirements
- Document error conditions and edge cases
- Specify performance requirements with measurable criteria
- Cover all major system interfaces and integration points

**Balanced Detail Level:**
- Provide enough detail for implementation guidance
- Avoid over-specification that constrains design flexibility
- Include rationale for complex requirements
- Reference external standards or protocols when applicable

This style guide captures the professional, comprehensive approach of your elevator system requirements document, emphasizing clear structure, visual integration, and precise technical communication.