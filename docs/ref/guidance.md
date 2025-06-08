# Documentation
*   `requirement.md`:
    *   **Should contain descriptions and diagrams**:
        *   System-wide **use case diagram**.
        *   **Class diagram** (include users and system components).
        *   Expanded workflows for user-system interactions using **activity diagrams** or **sequence diagrams** (chosen based on workflow complexity).
    *   **Rule**: Diagrams and descriptions must complement each other. Add a diagram whenever textual explanations are insufficient to avoid ambiguity.
*   `user_manual.md`:
    *   **Detailed instructions**:
        *   Environment setup (e.g., Python version, required libraries).
        *   UI introduction (e.g., screenshots with labeled components).
        *   Step-by-step workflows for basic operations and cautions for potential error.
*   `specification.md`:
    *   **Class diagram** (focus on system components only; exclude users).
    *   **Method descriptions**: For every method in each class, provide:
        *   A functional description.
        *   Supporting UML diagrams (e.g., sequence diagrams for complex logic).
*   `validation.md`:
    *   **Testing**:
        *   **Unit tests**:
            *   Paste code snippets of **all functions with at least one branching logic**.
            *   **Mark each branch with a unique ID** (e.g., TC1, TC2).
            *   Design test cases to cover all marked branches.
            *   Calculate and report **branch coverage results** (e.g., "12/15 branches covered").
            *   Ensure **consistency** between test cases and the unit test code.
        *   **Integration tests**:
            *   Identify **types of component interactions** (e.g., data validation between modules).
            *   Define test coverage items using **equivalent partitioning** (e.g., valid/invalid inputs).
            *   Design test cases to cover these items.
        *   **System tests**:
            *   Describe **common workflows** (e.g., standard user operations).
            *   Describe **rare workflows** (linked to risk management) and design corresponding test cases.
    *   **Model Checking (include diagrams and explanations)**:
        *   **System model**: Must align with the actual system’s behavior. Justify any abstraction or approximations (e.g., simplified elevator location state space).
        *   **Environment model**: potential user operations should be covered as much as possible.
        *   **Verification queries**: Explain the purpose of each query and interpret the results.
    *   **Risk Management**:
        *   **Risk analysis:** First identify potential risks as complete as possible and describe when it can happen. Specify the frequency and severity of each risk.
        *   **Risk mitigation:** For each risk, describe how you mitigated it in your system, and justify with results from specification/model checking/testing.
*   `traceability.md`:
    *   **Traceability table**:
        *   Assign **unique IDs** to all requirements, specifications, code, test coverage items, and test cases.
        *   Map relationships in a large table (e.g., REQ1 → SPEC2.1 → Code3 → TEST-UNIT-3 in the same row of the table).
    *   **Rule**: Ensure every requirement is implemented and tested.
